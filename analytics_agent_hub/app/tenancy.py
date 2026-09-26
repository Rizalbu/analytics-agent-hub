"""Multi-tenant org registry.

Isolation boundary = a separate DuckDB warehouse file per org, not a shared
table with an org_id column. That's a deliberate simplification for this
codebase: queries.py / coordinator.py / analyst.py / insights.py / etc. never
change — they just get pointed at a different file for the duration of a
request (see db.set_db_path()), the same way the nakama pattern makes org
the isolation boundary but via a header + middleware instead of a schema
migration across 26 tables.

Creating an org runs the full synthetic-warehouse generator, so it takes
~1-2 minutes — same cost as the app's own first-boot bootstrap.
"""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]  # analytics_agent_hub/, independent
                                              # of where the warehouse resolves
                                              # to (own repo vs. sibling vendor)
ORGS_PATH = _ROOT / "data" / "orgs.json"
ORGS_DATA_DIR = _ROOT / "data" / "orgs"


def _load() -> dict[str, dict]:
    if not ORGS_PATH.exists():
        return {}
    return json.loads(ORGS_PATH.read_text())


def _save(orgs: dict[str, dict]) -> None:
    ORGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ORGS_PATH.write_text(json.dumps(orgs))


def create_org(name: str, owner_username: str) -> dict:
    orgs = _load()
    org_id = secrets.token_hex(6)
    db_path = ORGS_DATA_DIR / org_id / "funnel.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    sys.path.append(str(_ROOT))
    from data_gen.deploy_bootstrap import generate

    # deploy_bootstrap defaults to a fixed seed (reproducible single-tenant
    # demo); each org needs its own so orgs don't all get identical numbers.
    seed = int(org_id, 16) % (2**31)
    generate(str(db_path), seed=seed)

    org = {"id": org_id, "name": name, "db_path": str(db_path), "members": [owner_username]}
    orgs[org_id] = org
    _save(orgs)
    return org


def get_org(org_id: str | None) -> dict | None:
    if not org_id:
        return None
    return _load().get(org_id)


def is_member(org_id: str, username: str | None) -> bool:
    org = get_org(org_id)
    return bool(org and username and username in org.get("members", []))


def add_member(org_id: str, username: str) -> bool:
    orgs = _load()
    org = orgs.get(org_id)
    if not org or username in org["members"]:
        return False
    org["members"].append(username)
    _save(orgs)
    return True


def list_orgs_for(username: str) -> list[dict]:
    return [
        {"id": o["id"], "name": o["name"]}
        for o in _load().values()
        if username in o.get("members", [])
    ]
