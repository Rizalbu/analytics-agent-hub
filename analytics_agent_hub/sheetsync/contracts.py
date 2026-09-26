"""Per-sheet data contracts. In a real deployment these would be YAML files
under contracts/; kept inline here so the demo is single-source and runnable.

A contract declares: canonical columns, accepted header aliases (drift
tolerance), types, required flags, and the natural key for idempotent MERGE.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Column:
    name: str
    type: str = "str"            # str | int | float | date | bool
    required: bool = False
    aliases: list[str] = field(default_factory=list)


@dataclass
class Contract:
    sheet: str
    key: list[str]
    columns: list[Column]
    owner: str = "ops@fitflow.demo"

    def alias_map(self) -> dict[str, str]:
        m = {}
        for c in self.columns:
            m[c.name.lower()] = c.name
            for a in c.aliases:
                m[a.lower()] = c.name
        return m


# Daily front-desk log every studio keeps in a sheet.
DAILY_LOG = Contract(
    sheet="studio_daily_log",
    key=["log_date", "studio_code"],
    columns=[
        Column("log_date", "date", True, ["date", "tanggal", "tgl"]),
        Column("studio_code", "str", True, ["studio", "kode_studio", "cabang"]),
        Column("walk_ins", "int", False, ["walkin", "walk in", "tamu"]),
        Column("trials_run", "int", False, ["trials", "trial", "trial_count"]),
        Column("cash_collected", "float", False, ["cash", "kas", "cash_in"]),
        Column("staff_on_duty", "int", False, ["staff", "petugas"]),
    ],
)

CONTRACTS = {c.sheet: c for c in [DAILY_LOG]}
