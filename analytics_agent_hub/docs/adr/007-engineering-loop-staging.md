# ADR-007: Engineering Loop staging pipeline

**Status:** accepted

## Context

The autonomous engineering loop (`app/engineer.py`) lets an owner describe a
feature in plain language; an LLM writes a module, the full test suite gates
it, and a pass used to be committed straight into the app's own git history
and mounted alongside every built-in route on the next restart. The only
check between "the LLM wrote this" and "this is part of the real app" was
the automated test run - no diff review, no way to see what an endpoint
actually returns before it's live, and no way to scope a new feature to the
org that asked for it.

## Decision

A passing attempt is now **staged**, not applied:

1. **Isolation.** The file is written to `app/agent_features_staged/`, a
   directory `main.py`'s auto-mount loop never scans, and recorded on its
   own `agent/<slug>-<ts>` git branch via plumbing commands (`write-tree` /
   `commit-tree` / `update-ref`) - the working tree never checks that branch
   out, so nothing about the live app changes while a proposal is pending.
2. **Live preview.** `engineer.preview()` drives the staged router directly
   over ASGI (`httpx.AsyncClient` + `ASGITransport`, wrapped in `asyncio.run`)
   against a throwaway `FastAPI()` instance - a reviewer sends a real request
   and reads the real response before deciding, not just a diff. (Starlette's
   `TestClient` was tried first; this environment's `httpx` has dropped sync
   support from `ASGITransport`, so the async bridge avoids adding a new
   dependency just for preview.)
3. **Promotion.** `engineer.promote()` copies the staged file into
   `app/agent_features/` and commits it on `main` directly (not a git merge -
   the staged file's path differs, so the commit message links back to the
   reviewed branch/commit instead). Requires typing the exact filename as
   confirmation, and requires a *different* owner than the one who requested
   it whenever a second owner account exists (`auth.owner_usernames()`).
4. **Per-org scope + kill switch.** Promotion writes an entry to
   `data/promoted_features.json` (`enabled`, `scope: org|global`, `org_ids`).
   Every mounted agent-feature router gets a `Depends(_feature_gate(...))`
   dependency (`app/main.py`) that checks this manifest per request - a
   feature can be limited to the org that asked for it, rolled out globally,
   or disabled instantly, with no restart needed for the disable path.
5. **Rejection keeps the trail.** `engineer.reject()` deletes the staged
   file but renames the branch to `rejected/<slug>` instead of deleting it -
   a rejected attempt stays inspectable via git even though it's gone from
   disk.

Endpoints: `POST /api/agents/engineer` (propose), `GET .../staged` (list,
optional `?status=`), `GET .../staged/{id}` (detail + code), `POST
.../staged/{id}/preview`, `.../promote`, `.../reject`, `POST
.../promoted/{filename}/toggle` (kill switch). Frontend: a "Pending review"
list on the AI Agents page per proposal - test output, a live "Try it"
request form, and a promote flow that requires typing the filename.

## Consequences

- A broken or unwanted LLM attempt never reaches the live app or another
  org's users, and disabling a bad promoted feature doesn't need a restart.
- Promotion is a second, explicit human action, separate from the LLM's own
  test-gated write - autonomy stays in the write+test step, not in what
  goes live.
- Not a literal `git merge`: the staged branch is an audit trail, not the
  source of the promotion commit's diff. Simpler than reconciling the
  staged path (`agent_features_staged/`) against the live one
  (`agent_features/`) through a real merge, at the cost of the promotion
  commit not being a merge commit.
- Fixed in the same pass: `app/agents.py`'s `_seed()` re-acquired
  `_agent_lock` (a non-reentrant `threading.Lock`) from inside `_log()`,
  which already held it - dormant only because the seed data had already
  been written once; a truly empty `agent.duckdb` deadlocked the first
  write. `_seed()` no longer takes the lock itself, and no longer calls the
  lock-taking `create_task()` for its own seed rows.
- Limitation: still single-process, in-app execution once promoted (same
  trust boundary as before this ADR) - preview and staging isolate *review*,
  not a hostile LLM output at promotion time.
