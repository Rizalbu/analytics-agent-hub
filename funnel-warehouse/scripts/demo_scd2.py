"""SCD2 demo: remap a channel, re-snapshot, show history.

Simulates the real-world event 'marketing reclassifies TikTok Ads from
paid_social to paid_video'. Run AFTER an initial `dbt build`:

    python scripts/demo_scd2.py        # mutates mapping + reruns snapshot
    python scripts/demo_scd2.py --show # just print snapshot history
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "funnel.duckdb"


def show_history() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""
        select channel_raw, channel_name, channel_group,
               dbt_valid_from::date as valid_from,
               coalesce(dbt_valid_to::date::varchar, 'current') as valid_to
        from snapshots.snap_channel_mapping
        where channel_raw in ('tiktok ads', 'TikTok')
        order by channel_raw, dbt_valid_from
    """).fetchall()
    print(f"{'raw':<12} {'name':<12} {'group':<14} {'from':<12} to")
    for r in rows:
        print(f"{r[0]:<12} {r[1]:<12} {r[2]:<14} {str(r[3]):<12} {r[4]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if not args.show:
        con = duckdb.connect(str(DB))
        con.execute("""
            update raw.channel_mapping_current
            set channel_group = 'paid_video'
            where channel_name = 'TikTok Ads'
        """)
        con.close()
        print("mapping mutated: TikTok Ads -> paid_video; re-running snapshot…")
        r = subprocess.run(
            [sys.executable, "-m", "dbt.cli.main", "snapshot",
             "--profiles-dir", ".", "--project-dir", "."],
            cwd=ROOT / "dbt",
        )
        if r.returncode != 0:
            sys.exit(r.returncode)
        print("\nSCD2 history now shows both versions:\n")
    show_history()


if __name__ == "__main__":
    main()
