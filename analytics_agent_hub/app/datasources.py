"""Real user-registered data sources (replaces the fictional connector
catalog that used to live in app.js / funnel_detail.py — those showed fake
stats for Postgres/BigQuery/Snowflake/etc. with zero actual connections).

A source today = a local CSV file, loaded into its own writable DuckDB
(sources.duckdb), attached into every query connection as schema `custom`
(see db.py). SQL Workspace can query `custom.<table>` directly, and the
Data/Analytics Engineer agents mention registered sources in their real
context (see agents.py agent_tool_context). Not attempted here: the NLQ
"AI Analyst" is deterministic and schema-specific to the FitFlow marts, so
it doesn't dynamically understand an arbitrary uploaded table's columns —
that would need a schema-aware LLM-grounded rewrite, a bigger job than this.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path

import duckdb

_ROOT = Path(__file__).resolve().parents[1]
SOURCES_DB_PATH = _ROOT / "data" / "sources.duckdb"
REGISTRY_PATH = _ROOT / "data" / "datasources.json"

_SAFE = re.compile(r"[^a-z0-9_]+")


def _table_name(name: str, source_id: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_") or "source"
    return f"{slug}_{source_id}"


def _load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    return json.loads(REGISTRY_PATH.read_text())


def _save_registry(reg: dict[str, dict]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg))


def list_sources() -> list[dict]:
    return list(_load_registry().values())


def get_source(source_id: str) -> dict | None:
    return _load_registry().get(source_id)


def add_source(name: str, csv_path: str, added_by: str) -> dict:
    p = Path(csv_path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"No such file: {csv_path}")
    if p.suffix.lower() != ".csv":
        raise ValueError("Only .csv files are supported right now.")

    source_id = uuid.uuid4().hex[:10]
    table = _table_name(name, source_id)

    SOURCES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(SOURCES_DB_PATH))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS custom")
        con.execute(
            f'CREATE TABLE custom."{table}" AS SELECT * FROM read_csv_auto(?, header=true)',
            [str(p)],
        )
        cols = con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'custom' AND table_name = ?", [table],
        ).fetchall()
        row_count = con.execute(f'SELECT count(*) FROM custom."{table}"').fetchone()[0]
    finally:
        con.close()

    record = {
        "id": source_id,
        "name": name,
        "table": table,
        "path": str(p),
        "columns": [{"name": c, "type": t} for c, t in cols],
        "row_count": row_count,
        "added_by": added_by,
        "added_at": time.time(),
    }
    reg = _load_registry()
    reg[source_id] = record
    _save_registry(reg)
    return record


def remove_source(source_id: str) -> bool:
    reg = _load_registry()
    rec = reg.pop(source_id, None)
    if not rec:
        return False
    con = duckdb.connect(str(SOURCES_DB_PATH))
    try:
        con.execute(f'DROP TABLE IF EXISTS custom."{rec["table"]}"')
    finally:
        con.close()
    _save_registry(reg)
    return True
