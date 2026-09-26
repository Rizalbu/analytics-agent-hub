"""Read-only DuckDB access with a tiny thread-safe connection cache.

Every query goes through `rows()` / `row()` which return plain dicts so the
API layer never touches the cursor. The connection is opened read_only to
guarantee the hub can never mutate the warehouse.
"""
from __future__ import annotations

import threading
from typing import Any

import duckdb

from .config import settings

_local = threading.local()


def _conn() -> duckdb.DuckDBPyConnection:
    c = getattr(_local, "conn", None)
    if c is None:
        c = duckdb.connect(settings.db_path, read_only=True)
        _local.conn = c
    return c


def rows(sql: str, params: list[Any] | None = None) -> list[dict]:
    cur = _conn().execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def row(sql: str, params: list[Any] | None = None) -> dict | None:
    out = rows(sql, params)
    return out[0] if out else None


def scalar(sql: str, params: list[Any] | None = None) -> Any:
    r = _conn().execute(sql, params or []).fetchone()
    return r[0] if r else None
