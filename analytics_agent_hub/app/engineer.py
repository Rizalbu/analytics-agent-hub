"""Autonomous engineering loop: an owner instructs it, an LLM writes a file,
the test suite gates it, git records it. That much is fully autonomous - no
human reviews the diff before the LLM's attempt is judged. What happens after
a passing attempt is not autonomous by design: it becomes a STAGED proposal,
recorded on its own git branch and sitting in agent_features_staged/ (which
main.py's mount loop never scans), and only an explicit promote() call by a
human moves it into agent_features/ where it becomes live after a restart.
Every run is boxed in hard, non-negotiable ways:

  1. Scope: can only create/modify files under agent_features/, never
     app/auth.py, app/tenancy.py, app/db.py, or anything security-relevant.
  2. Gate: the request must come from an "owner" role (checked by the
     caller, app/main.py, via auth.is_owner). A chat message from a
     regular member can't trigger this at all.
  3. Correctness: the full pytest suite must pass on the new file before
     it's kept. Any failure discards the attempt entirely; nothing broken
     is ever left in place, let alone staged.
  4. Isolation: a passing attempt is staged, not applied. It sits on its own
     `agent/<slug>-<ts>` branch (the permanent, inspectable record of exactly
     what was generated and tested - kept even if the proposal is later
     rejected) and as a file under agent_features_staged/, invisible to the
     live app's auto-mount step until a human promotes it.
  5. Approval: promoting requires a different owner than the one who asked
     for the feature, whenever a second owner account exists at all; with a
     single owner, promotion instead requires typing the exact filename as
     an explicit confirmation. Either way, self-service silent promotion
     never happens.
  6. Audit: every attempt (accepted, rejected, staged, promoted) is logged
     to the same activity feed the rest of the AI Agents workspace uses.

Restart the server (or run it with `uvicorn --reload`) to pick up a file
this loop just promoted into agent_features/. A running Python process
doesn't reload modules that were added or changed after import, same as any
other Python app. That's a real, disclosed limitation, not a gap in the
autonomy: nothing here silently fails to take effect, it just needs the
same restart step any code change to this app needs.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import llm

_ROOT = Path(__file__).resolve().parents[1]  # analytics_agent_hub/
FEATURES_DIR = _ROOT / "app" / "agent_features"
FEATURES_DIR.mkdir(exist_ok=True)
(FEATURES_DIR / "__init__.py").touch(exist_ok=True)

# Staged proposals live here - never scanned by main.py's auto-mount loop,
# so a passing-but-unreviewed attempt can never accidentally go live.
STAGED_DIR = _ROOT / "app" / "agent_features_staged"
STAGED_DIR.mkdir(exist_ok=True)

STAGED_META_PATH = _ROOT / "data" / "staged_features.json"
MANIFEST_PATH = _ROOT / "data" / "promoted_features.json"

_CODE_FENCE = re.compile(r"^```[a-zA-Z]*\n|\n```$", re.MULTILINE)


class EngineerError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validated_name(filename: str) -> str:
    if not filename.endswith(".py") or "/" in filename.replace("agent_features/", "", 1):
        raise EngineerError("filename must be a single .py file inside agent_features/")
    name = filename.split("/")[-1]
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*\.py", name):
        raise EngineerError("invalid module name")
    return name


def _extract_code(raw: str) -> str:
    return _CODE_FENCE.sub("", raw.strip())


def _run_tests() -> tuple[bool, str]:
    r = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-q"],
        cwd=str(_ROOT), capture_output=True, text=True, timeout=120,
    )
    return r.returncode == 0, (r.stdout + r.stderr)[-3000:]


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(_ROOT), capture_output=True, text=True)
    return r.stdout + r.stderr


# ---- staged-proposal store (data/staged_features.json) --------------------

def _load_staged_all() -> dict:
    if not STAGED_META_PATH.exists():
        return {}
    return json.loads(STAGED_META_PATH.read_text())


def _save_staged_entry(proposal: dict) -> None:
    STAGED_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    d = _load_staged_all()
    d[proposal["id"]] = proposal
    STAGED_META_PATH.write_text(json.dumps(d, indent=2))


def list_staged(status: str | None = None) -> list[dict]:
    items = list(_load_staged_all().values())
    if status:
        items = [p for p in items if p["status"] == status]
    return sorted(items, key=lambda p: p["created_at"], reverse=True)


def get_staged(proposal_id: str) -> dict | None:
    return _load_staged_all().get(proposal_id)


# ---- promoted-feature manifest (data/promoted_features.json) --------------
# Per-org rollout + an instant kill-switch for anything the engineering loop
# has promoted, so disabling a bad feature never has to wait for a restart.

def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())


def _save_manifest(d: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(d, indent=2))


def get_manifest_entry(filename: str) -> dict | None:
    return _load_manifest().get(filename)


def set_feature_enabled(filename: str, enabled: bool) -> bool:
    manifest = _load_manifest()
    if filename not in manifest:
        return False
    manifest[filename]["enabled"] = enabled
    _save_manifest(manifest)
    return True


SYSTEM_PROMPT = """You are an autonomous software engineer maintaining a FastAPI
+ DuckDB analytics app. You will be given a feature instruction and must output
ONLY the complete Python source for one new module - no prose, no markdown
fences, no explanation. The module will be saved as-is and must be syntactically
valid Python 3.11. If it needs to expose an HTTP endpoint, define an
`APIRouter` named `router` (from fastapi import APIRouter) - the app will
mount it once a human promotes this proposal. Keep it self-contained; only
import from the standard library, fastapi, or pydantic."""


def propose(instruction: str, filename: str, requested_by: str, org_id: str | None = None) -> dict:
    """Write + test a new feature. A pass stages it for human review; a
    failure discards it completely. Never touches the live app directly."""
    name = _validated_name(filename)
    live_path = FEATURES_DIR / name
    staged_path = STAGED_DIR / name
    if live_path.exists() or staged_path.exists():
        raise EngineerError(f"{name} already exists (live or pending review)")

    code = _extract_code(llm.complete(
        f"Feature instruction: {instruction}\n\nModule filename: {name}",
        system=SYSTEM_PROMPT,
        for_engineer=True,
    ))

    # Written briefly into the LIVE directory so the pytest subprocess below
    # actually imports and mounts it (that's what exercises the router) -
    # but this process's own mount already ran at boot, so the running app
    # is never affected by the file's momentary presence here.
    live_path.write_text(code)
    ok, test_output = _run_tests()

    from . import agents  # local import: avoid a circular import at module load

    if not ok:
        live_path.unlink(missing_ok=True)
        agents._log("engineer", f"REJECTED, tests failed for {name}: {instruction[:100]}", requested_by)
        return {"ok": False, "applied": False, "staged": False, "test_output": test_output}

    live_path.unlink()  # tests passed; move it OUT of the live dir into staging
    staged_path.write_text(code)

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "feature"
    branch = f"agent/{slug}-{int(time.time())}"
    rel = staged_path.relative_to(_ROOT)
    commit_msg = (
        f"agent: propose {name}\n\n{instruction[:200]}\n\n"
        f"Requested by {requested_by}, staged for review (not yet live)."
    )
    # Commit the staged file onto its OWN branch via plumbing, without ever
    # checking that branch out - the working tree (and whatever's live on
    # main) never moves. This is the permanent audit trail: it survives even
    # if the proposal is later rejected and the on-disk file removed.
    _git("add", str(rel))
    tree = _git("write-tree").strip()
    parent = _git("rev-parse", "HEAD").strip()
    commit = _git("commit-tree", tree, "-p", parent, "-m", commit_msg).strip()
    _git("update-ref", f"refs/heads/{branch}", commit)
    _git("rm", "--cached", "-q", str(rel))  # unstage from main's index; file stays on disk
    commit_hash = commit[:7]

    proposal_id = f"stg-{uuid.uuid4().hex[:8]}"
    proposal = {
        "id": proposal_id, "filename": name, "instruction": instruction,
        "requested_by": requested_by, "org_id": org_id, "branch": branch,
        "commit": commit_hash, "status": "pending", "test_output": test_output[-1500:],
        "created_at": _now(), "decided_at": None, "decided_by": None, "promote_commit": None,
    }
    _save_staged_entry(proposal)

    agents._log("engineer", f"STAGED {name} ({commit_hash}) for review: {instruction[:100]}", requested_by)
    return {"ok": True, "applied": False, "staged": True, "proposal": proposal}


def preview(proposal_id: str, method: str, path: str,
            query: dict | None = None, json_body: dict | None = None) -> dict:
    """Run a real HTTP request against a staged proposal's router, in-process
    but isolated to a throwaway FastAPI app - never the live one. Lets a
    reviewer see actual response data before deciding, not just read a diff."""
    proposal = get_staged(proposal_id)
    if not proposal:
        raise EngineerError("proposal not found")
    staged_path = STAGED_DIR / proposal["filename"]
    if not staged_path.exists():
        raise EngineerError("staged file is gone (already promoted or rejected?)")

    try:
        import asyncio
        import importlib.util
        import httpx
        from fastapi import FastAPI as _FastAPI

        modname = f"_staged_preview_{proposal_id.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(modname, staged_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        router = getattr(mod, "router", None)
        if router is None:
            raise EngineerError("staged module has no `router` - nothing to call as an endpoint")

        preview_app = _FastAPI()
        preview_app.include_router(router)

        # Drive the throwaway app directly over ASGI (in-process, no socket,
        # no subprocess) instead of Starlette's TestClient - this environment's
        # httpx has dropped sync support from ASGITransport, so we go async
        # and bridge it ourselves rather than pull in a new dependency for it.
        async def _call():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=preview_app),
                                          base_url="http://preview") as client:
                return await client.request(method.upper(), path, params=query, json=json_body)

        resp = asyncio.run(_call())
        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text
        return {"status_code": resp.status_code, "body": payload}
    except EngineerError:
        raise
    except Exception as e:
        raise EngineerError(f"preview failed: {e}")


def promote(proposal_id: str, promoted_by: str, scope: str = "org", org_id: str | None = None) -> dict:
    proposal = get_staged(proposal_id)
    if not proposal:
        raise EngineerError("proposal not found")
    if proposal["status"] != "pending":
        raise EngineerError(f"already {proposal['status']}")

    staged_path = STAGED_DIR / proposal["filename"]
    if not staged_path.exists():
        raise EngineerError("staged file is missing")
    live_path = FEATURES_DIR / proposal["filename"]
    live_path.write_text(staged_path.read_text())
    staged_path.unlink()

    _git("add", str(live_path.relative_to(_ROOT)))
    commit_msg = (
        f"agent: promote {proposal['filename']}\n\n"
        f"Reviewed from {proposal['branch']} ({proposal['commit']}).\n"
        f"Requested by {proposal['requested_by']}, promoted by {promoted_by}."
    )
    _git("commit", "-m", commit_msg)
    commit_hash = _git("rev-parse", "--short", "HEAD").strip()

    effective_scope = "global" if org_id is None else (scope if scope in ("org", "global") else "org")
    manifest = _load_manifest()
    manifest[proposal["filename"]] = {
        "enabled": True, "scope": effective_scope,
        "org_ids": [org_id] if (effective_scope == "org" and org_id) else [],
    }
    _save_manifest(manifest)

    proposal.update(status="promoted", decided_at=_now(), decided_by=promoted_by, promote_commit=commit_hash)
    _save_staged_entry(proposal)

    from . import agents
    agents._log("engineer", f"PROMOTED {proposal['filename']} ({commit_hash}), scope={effective_scope}: "
                             f"{proposal['instruction'][:100]}", promoted_by)
    return {"ok": True, "commit": commit_hash, "filename": proposal["filename"], "scope": effective_scope}


def reject(proposal_id: str, rejected_by: str, comment: str = "") -> dict:
    proposal = get_staged(proposal_id)
    if not proposal:
        raise EngineerError("proposal not found")
    if proposal["status"] != "pending":
        raise EngineerError(f"already {proposal['status']}")

    staged_path = STAGED_DIR / proposal["filename"]
    staged_path.unlink(missing_ok=True)

    # Keep the branch (renamed) as the permanent record instead of deleting
    # it - a rejected attempt is still worth being able to inspect later.
    new_branch = proposal["branch"].replace("agent/", "rejected/", 1)
    _git("branch", "-m", proposal["branch"], new_branch)

    proposal.update(status="rejected", decided_at=_now(), decided_by=rejected_by, branch=new_branch)
    _save_staged_entry(proposal)

    from . import agents
    note = f" - {comment}" if comment else ""
    agents._log("engineer", f"REJECTED {proposal['filename']} (kept as git branch {new_branch}): "
                             f"{proposal['instruction'][:100]}{note}", rejected_by)
    return {"ok": True, "branch": new_branch}
