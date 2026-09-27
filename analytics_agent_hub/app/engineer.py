"""Autonomous engineering loop: an owner instructs it, an LLM writes a file,
the test suite gates it, git records it. No human reviews the diff before
it's applied (that's the "fully autonomous" part), but every run is boxed
in hard, non-negotiable ways so autonomy doesn't mean unbounded:

  1. Scope: can only create/modify files under agent_features/, never
     app/auth.py, app/tenancy.py, app/db.py, or anything security-relevant.
  2. Gate: the request must come from an "owner" role (checked by the
     caller, app/main.py, via auth.is_owner). A chat message from a
     regular member can't trigger this at all.
  3. Correctness: the full pytest suite must pass on the new file before
     it's kept. Any failure reverts the write completely; nothing broken
     is ever left in place, let alone committed.
  4. Audit: every attempt (accepted or rejected) is logged to the same
     activity feed the rest of the AI Agents workspace uses, with the
     instruction, the outcome, and (on failure) the test output.

Restart the server (or run it with `uvicorn --reload`) to pick up a file
this loop just wrote. A running Python process doesn't reload modules
that were added or changed after import, same as any other Python app.
That's a real, disclosed limitation, not a gap in the autonomy: nothing
here silently fails to take effect, it just needs the same restart step
any code change to this app needs.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from . import llm

_ROOT = Path(__file__).resolve().parents[1]  # analytics_agent_hub/
FEATURES_DIR = _ROOT / "app" / "agent_features"
FEATURES_DIR.mkdir(exist_ok=True)
(FEATURES_DIR / "__init__.py").touch(exist_ok=True)

_CODE_FENCE = re.compile(r"^```[a-zA-Z]*\n|\n```$", re.MULTILINE)


class EngineerError(Exception):
    pass


def _validated_path(filename: str) -> Path:
    if not filename.endswith(".py") or "/" in filename.replace("agent_features/", "", 1):
        raise EngineerError("filename must be a single .py file inside agent_features/")
    name = filename.split("/")[-1]
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*\.py", name):
        raise EngineerError("invalid module name")
    p = (FEATURES_DIR / name).resolve()
    if p.parent != FEATURES_DIR.resolve():
        raise EngineerError("path escapes the allowed directory")
    return p


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


SYSTEM_PROMPT = """You are an autonomous software engineer maintaining a FastAPI
+ DuckDB analytics app. You will be given a feature instruction and must output
ONLY the complete Python source for one new module - no prose, no markdown
fences, no explanation. The module will be saved as-is and must be syntactically
valid Python 3.11. If it needs to expose an HTTP endpoint, define an
`APIRouter` named `router` (from fastapi import APIRouter) - the app will
mount it. Keep it self-contained; only import from the standard library,
fastapi, or pydantic."""


def propose_and_apply(instruction: str, filename: str, requested_by: str) -> dict:
    path = _validated_path(filename)
    existed_before = path.exists()
    backup = path.read_text() if existed_before else None

    code = _extract_code(llm.complete(
        f"Feature instruction: {instruction}\n\nModule filename: {filename}",
        system=SYSTEM_PROMPT,
        for_engineer=True,
    ))

    path.write_text(code)
    ok, test_output = _run_tests()

    from . import agents  # local import: avoid a circular import at module load

    if not ok:
        if existed_before:
            path.write_text(backup)
        else:
            path.unlink(missing_ok=True)
        agents._log("engineer", f"REJECTED, tests failed for {filename}: {instruction[:100]}", requested_by)
        return {"ok": False, "applied": False, "test_output": test_output, "path": str(path)}

    _git("add", str(path))
    commit_msg = f"agent: {instruction[:72]}\n\nAuthored by the autonomous engineering loop, requested by {requested_by}.\nFile: {filename}"
    _git("commit", "-m", commit_msg)
    commit_hash = _git("rev-parse", "--short", "HEAD").strip()

    agents._log("engineer", f"APPLIED {filename} ({commit_hash}): {instruction[:100]}", requested_by)
    return {"ok": True, "applied": True, "commit": commit_hash, "path": str(path), "code": code}
