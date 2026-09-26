"""Load messy studio CSVs into the DuckDB `raw` schema.

Boundary contract (see docs/adr/001): the loader does STRUCTURAL
normalization only: header aliases and lineage columns. All semantic
cleaning (types, dedupe, date parsing, money parsing) happens in dbt staging,
where it is versioned and tested.

Header drift is resolved per-file: the header row is read in Python and
mapped through HEADER_ALIASES, then the body is bulk-loaded natively by
DuckDB (read_csv with explicit names), fast and type-agnostic (all VARCHAR).

Run: python pipeline/load_raw.py [--db warehouse/funnel.duckdb]
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

# lowercase/stripped header -> canonical column
HEADER_ALIASES = {
    # leads variants A/B/C
    "lead_id": "lead_id", "leadid": "lead_id", "id_lead": "lead_id",
    "studio_code": "studio_code", "studio": "studio_code", "kode_studio": "studio_code",
    "channel": "channel_raw", "channel name": "channel_raw", "kanal": "channel_raw",
    "created_at": "created_at_raw", "created date": "created_at_raw",
    "tanggal_dibuat": "created_at_raw",
    "full_name": "full_name", "name": "full_name", "nama": "full_name",
    "phone": "phone", "phone number": "phone", "telepon": "phone",
    "status": "status",
    # bookings / visits / sales / spend (already canonical, kept for safety)
    "booking_id": "booking_id", "booked_at": "booked_at", "trial_date": "trial_date",
    "booking_status": "booking_status", "visit_id": "visit_id",
    "visit_date": "visit_date", "attended": "attended_raw",
    "sale_id": "sale_id", "plan_code": "plan_code", "sold_at": "sold_at",
    "amount": "amount", "payment_status": "payment_status",
    "spend_date": "spend_date", "spend": "spend_raw",
    "impressions": "impressions", "clicks": "clicks",
}

SOURCES = ["leads", "bookings", "visits", "sales", "ad_spend"]


def normalized_header(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        raw_header = next(csv.reader(f))
    cols = []
    for h in raw_header:
        key = h.strip().lower()
        if key not in HEADER_ALIASES:
            raise ValueError(f"{path.name}: unmapped header {h!r}, "
                             f"add it to HEADER_ALIASES or fix the source")
        cols.append(HEADER_ALIASES[key])
    return cols


def load_source(con: duckdb.DuckDBPyConnection, source: str, loaded_at: str) -> int:
    files = sorted((ROOT / "data" / "drops" / source).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no CSVs for {source}, run the generator first")

    table = f"raw.{source}"
    con.execute(f"DROP TABLE IF EXISTS {table}")
    created = False
    total = 0
    for fp in files:
        cols = normalized_header(fp)
        names_sql = "[" + ", ".join(f"'{c}'" for c in cols) + "]"
        rel = (f"read_csv('{fp.as_posix()}', header=false, skip=1, "
               f"names={names_sql}, all_varchar=true)")
        select = (f"SELECT *, '{fp.name}' AS _source_file, "
                  f"TIMESTAMP '{loaded_at}' AS _loaded_at FROM {rel}")
        if not created:
            con.execute(f"CREATE TABLE {table} AS {select}")
            created = True
        else:
            con.execute(f"INSERT INTO {table} BY NAME {select}")
        total += con.execute(
            f"SELECT count(*) FROM {rel}").fetchone()[0]
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "warehouse" / "funnel.duckdb"))
    args = ap.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for source in SOURCES:
        n = load_source(con, source, loaded_at)
        print(f"raw.{source}: {n:,} rows")

    # current-state channel mapping (snapshotted by dbt for SCD2 history)
    con.execute("DROP TABLE IF EXISTS raw.channel_mapping_current")
    con.execute(f"""
        CREATE TABLE raw.channel_mapping_current AS
        SELECT *, TIMESTAMP '{loaded_at}' AS _loaded_at
        FROM read_csv_auto('{(ROOT / "reference" / "channel_map.csv").as_posix()}', header=true)
    """)
    print("raw.channel_mapping_current: refreshed")
    con.close()


if __name__ == "__main__":
    main()
