# ADR-006: SQL Workspace guardrails

**Status:** accepted

## Context

Users want to run their own SQL against the warehouse, not just the pre-built
pages. Exposing an arbitrary query endpoint is risky: even a read-only DuckDB
connection can read local files (`read_csv('/etc/...')`), `ATTACH` other
databases, `INSTALL`/`LOAD` extensions, or run expensive scans.

## Decision

`app/sql_workspace.py` executes user SQL through layered guardrails; the DB
connection is already `read_only=True` (defense in depth), and on top of that:

1. **SELECT-only.** Parse with `sqlglot` (`parse_one`, dialect `duckdb`);
   reject anything that isn't a single `SELECT`/`WITH ... SELECT`. Multiple
   statements (`;`) rejected.
2. **Function/keyword blocklist.** Regex blocks file readers (`read_csv`,
   `read_parquet`, `glob`, …) and `ATTACH`/`COPY`/`INSTALL`/`LOAD`/`PRAGMA`.
3. **Schema allow-list.** Table references outside the known warehouse schemas
   are rejected.
4. **Row cap + timeout.** Query is wrapped with an outer `LIMIT` (1000) and a
   `threading.Timer` calls `con.interrupt()` after 5s.

Endpoints: `POST /api/sql` (run), `GET /api/sql/schema` (browser),
`/api/sql/preview`, `/api/sql/stats`, `/api/sql/format`. Frontend: editor +
schema sidebar + results grid + CSV export, integrated with the AI Analyst
(open its provenance SQL in the workspace).

## Consequences

- Safe read-only exploration without a separate BI tool.
- `sqlglot` added as a dependency (lightweight, parse-only).
- Guardrails are validated by a self-check; the read-only connection is the
  final backstop if a validator gap is ever found.
- Limitation: no query history/saved queries yet; add a small table if users
  ask.
