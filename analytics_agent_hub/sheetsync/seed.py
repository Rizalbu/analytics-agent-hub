"""Generate emulated 'studio sheets' as messy CSVs, the zero-setup source.

Deliberately injects the real-world problems Sheet Sync exists to catch:
  - per-studio header drift (3 variants incl. Indonesian)
  - mixed date formats and "Rp 1.250.000" money text
  - a few duplicate rows
  - ONE scripted breaking drift: studio S07 renames cash_collected -> 'omzet'
    (an alias we do NOT know) so the drift→quarantine→suggestion flow demos
  - a deletion between snapshots (handled by run.py --simulate-delete)

Run:  python -m sheetsync.seed
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from app.config import settings

STUDIOS = ["S01", "S03", "S05", "S07", "S09", "S11"]  # subset that uses sheets
HEADERS = {
    "A": ["log_date", "studio_code", "walk_ins", "trials_run", "cash_collected", "staff_on_duty"],
    "B": ["Tanggal", "Studio", "Walk In", "Trials", "Cash", "Staff"],
    "C": ["tgl", "kode_studio", "tamu", "trial_count", "kas", "petugas"],
}
VARIANT = {"S01": "A", "S03": "B", "S05": "A", "S07": "A", "S09": "C", "S11": "B"}
DATEFMT = {"A": "%Y-%m-%d", "B": "%d/%m/%Y", "C": "%d-%b-%Y"}


def gen(days: int = 45, seed: int = 7, inject_drift: bool = True) -> None:
    rng = random.Random(seed)
    out_dir = Path(settings.sheets_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = date(2025, 11, 1)
    for sc in STUDIOS:
        var = VARIANT[sc]
        header = HEADERS[var][:]
        # scripted breaking drift: S07 renamed cash column to an unknown alias
        if inject_drift and sc == "S07":
            header[4] = "omzet"
        rows = []
        for i in range(days):
            d = start + timedelta(days=i)
            walk = max(0, round(rng.gauss(14, 5)))
            trials = max(0, round(walk * rng.uniform(0.4, 0.7)))
            cash = trials * rng.randint(150_000, 400_000)
            cash_s = (f"Rp {cash:,}".replace(",", ".") if rng.random() < 0.2 else str(cash))
            staff = rng.randint(2, 5)
            rows.append([d.strftime(DATEFMT[var]), sc, walk, trials, cash_s, staff])
        # inject a couple duplicate rows
        for _ in range(2):
            rows.append(rng.choice(rows)[:])
        with open(out_dir / f"{sc}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    print(f"seeded {len(STUDIOS)} studio sheets in {out_dir} "
          f"({'with' if inject_drift else 'no'} scripted drift on S07)")


if __name__ == "__main__":
    gen()
