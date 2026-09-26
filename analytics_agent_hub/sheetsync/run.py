"""Sheet Sync CLI.

  python -m sheetsync.seed                 # create emulated messy sheets
  python -m sheetsync.run                  # sync all sheets once
  python -m sheetsync.run --fix-drift      # re-seed S07 WITHOUT the drift, resync
  python -m sheetsync.run --simulate-delete  # drop last row of S01, resync (shows deletion detection)
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from app.config import settings
from . import engine, seed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix-drift", action="store_true")
    ap.add_argument("--simulate-delete", action="store_true")
    args = ap.parse_args()

    sheets = Path(settings.sheets_dir)
    if not any(sheets.glob("*.csv")):
        seed.gen()

    if args.fix_drift:
        seed.gen(inject_drift=False)
        print("re-seeded without S07 drift")
    if args.simulate_delete:
        # drop the 2nd data row (a unique day) so a logical record truly
        # disappears — the engine should flag it as a deletion
        f = sheets / "S01.csv"
        rows = list(csv.reader(open(f, encoding="utf-8")))
        if len(rows) > 3:
            kept = [rows[0]] + rows[2:]  # header + skip first data row
            with open(f, "w", newline="", encoding="utf-8") as out:
                csv.writer(out).writerows(kept)
            print(f"removed a unique row from S01.csv (was {rows[1]})")

    results = engine.sync_all()
    for r in results:
        line = (f"{r['sheet_file']:<10} {r['status']:<16} "
                f"in={r['rows_in']:>4} valid={r['rows_valid']:>4} "
                f"err={r['rows_error']:>3} merged={r['rows_merged']:>4} "
                f"del={r['deletes']:>2}")
        print(line)
        for e in r["errors"][:3]:
            print(f"    ! {e}")


if __name__ == "__main__":
    main()
