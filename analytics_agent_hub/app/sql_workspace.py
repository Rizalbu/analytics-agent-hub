"""Read-only SQL workspace: validate -> guard -> execute on the warehouse.

Defense in depth: the DuckDB connection is already read_only, AND we (1) parse
with sqlglot and require a single SELECT/WITH, (2) block file-reading functions
and ATTACH/COPY/INSTALL/etc., (3) cap rows and add a statement timeout.
"""
from __future__ import annotations

import re
import threading
import time

import sqlglot
from sqlglot import exp

from . import db

ALLOWED_SCHEMAS = {
    "main_marts", "main_staging", "main_intermediate", "main_seeds",
    "raw", "snapshots", "information_schema", "main",
}
# functions that can read local files (read_only does NOT block these)
_FORBIDDEN_FUNC = re.compile(
    r"\b(read_csv|read_parquet|read_json|read_text|read_blob|glob|"
    r"parquet_scan|csv_scan)\s*\(", re.I)
# statements/clauses that must never appear
_FORBIDDEN_KW = re.compile(
    r"\b(attach|detach|copy|install|load|pragma|export|import)\b", re.I)

ROW_CAP = 1000
TIMEOUT_S = 5.0

class SqlError(Exception):
    pass

def validate(query: str) -> str:
    q = (query or "").strip().rstrip(";").strip()
    if not q:
        raise SqlError("Query is empty.")
    if ";" in q:
        raise SqlError("Only a single statement is allowed.")
    if _FORBIDDEN_FUNC.search(q) or _FORBIDDEN_KW.search(q):
        raise SqlError("Query uses a disallowed function or keyword.")
    try:
        expr = sqlglot.parse_one(q, read="duckdb")
    except Exception as e:
        raise SqlError(f"Parse error: {str(e)[:200]}")
    if not isinstance(expr, exp.Select):
        raise SqlError("Only SELECT / WITH ... SELECT queries are allowed.")
    for t in expr.find_all(exp.Table):
        schema = (t.db or "").lower()
        if schema and schema not in ALLOWED_SCHEMAS:
            raise SqlError(f"Schema not allowed: {schema}")
    return q

def _cell(v):
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)

def run(query: str) -> dict:
    q = validate(query)
    wrapped = f"SELECT * FROM ({q}) AS _sub LIMIT {ROW_CAP}"
    con = db._conn()
    timer = threading.Timer(TIMEOUT_S, con.interrupt)
    t0 = time.perf_counter()
    timer.start()
    try:
        cur = con.execute(wrapped)
        cols = [d[0] for d in cur.description]
        data = cur.fetchall()
    except Exception as e:
        raise SqlError(f"Execution error: {str(e)[:300]}")
    finally:
        timer.cancel()
    rows = [[_cell(v) for v in r] for r in data]
    return {"columns": cols, "rows": rows, "rowcount": len(rows),
            "ms": round((time.perf_counter() - t0) * 1000, 1),
            "capped": len(rows) >= ROW_CAP}

def schema() -> list[dict]:
    rows = db.rows("""
        select table_schema, table_name, column_name, data_type
        from information_schema.columns
        where table_schema in
          ('main_marts','main_staging','main_intermediate','main_seeds','raw')
        order by table_schema, table_name, ordinal_position""")
    out: dict = {}
    for r in rows:
        out.setdefault((r["table_schema"], r["table_name"]), []).append(
            {"name": r["column_name"], "type": r["data_type"]})
    return [{"schema": k[0], "table": k[1], "columns": v} for k, v in out.items()]


def preview(schema_name: str, table: str, limit: int = 50) -> dict:
    """Quick SELECT * preview of a table (skips schema validation for safety)."""
    q = f'SELECT * FROM "{schema_name}"."{table}" LIMIT {limit}'
    return run(q)


def stats() -> dict:
    """Warehouse-level statistics."""
    con = db._conn()
    table_counts = con.execute("""
        select table_schema, table_name,
               (select count(*) from information_schema.columns
                where table_schema = t.table_schema and table_name = t.table_name
               ) as col_count
        from (select distinct table_schema, table_name
              from information_schema.tables
              where table_schema in
                ('main_marts','main_staging','main_intermediate','main_seeds','raw')
             ) t
        order by table_schema, table_name
    """).fetchall()
    schemas = {}
    total_cols = 0
    for r in table_counts:
        s = r[0]; schemas.setdefault(s, {"tables": 0, "cols": 0})
        schemas[s]["tables"] += 1
        schemas[s]["cols"] += r[2]
        total_cols += r[2]
    return {
        "total_tables": len(table_counts),
        "total_schemas": len(schemas),
        "total_columns": total_cols,
        "schemas": [{"name": k, **v} for k, v in schemas.items()],
    }


def format_sql(query: str) -> str:
    """Pretty-print a SQL query via sqlglot."""
    q = (query or "").strip()
    if not q:
        return ""
    try:
        result = sqlglot.transpile(q, read="duckdb", pretty=True)
        return (result or [q])[0]
    except Exception:
        return q
