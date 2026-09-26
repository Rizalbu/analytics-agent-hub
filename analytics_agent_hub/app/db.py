"""Read-only DuckDB access with a tiny thread-safe connection cache.

Every query goes through `rows()` / `row()` which return plain dicts so the
API layer never touches the cursor. The connection is opened read_only to
guarantee the hub can never mutate the warehouse.

Multi-tenant isolation hooks in here: `set_db_path()` (called from request
middleware, based on the caller's org) points the *next* query at a
different warehouse file. It's a contextvar, not a global, so it's safe
across concurrent requests, and it defaults to the single shared warehouse
when no org is in play — every other module (queries.py, analyst.py, ...)
is unchanged, they just call rows()/row()/scalar() same as before.
"""
from __future__ import annotations

import contextvars
import threading
from typing import Any

import duckdb

from .config import settings

_local = threading.local()
_current_db_path: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_db_path", default=None
)


def set_db_path(path: str | None) -> None:
    _current_db_path.set(path)


def _conn() -> duckdb.DuckDBPyConnection:
    path = _current_db_path.get() or settings.db_path
    conns: dict[str, duckdb.DuckDBPyConnection] = getattr(_local, "conns", None)
    if conns is None:
        conns = {}
        _local.conns = conns
    c = conns.get(path)
    if c is None:
        c = duckdb.connect(path, read_only=True)
        conns[path] = c
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
