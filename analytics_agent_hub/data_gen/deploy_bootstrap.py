"""Generate FULL synthetic warehouse data for deployment.

Creates realistic FitFlow Studios data across all marts/tables so the
deployed app has rich dashboards, funnels, anomalies, and AI-analyst answers.
Run once at container startup when no warehouse exists yet.
"""
from __future__ import annotations

import random
import uuid
from datetime import date, timedelta
from pathlib import Path

import duckdb


STUDIOS = [
    ("S01", "Menteng",     "Jakarta",   "Premium"),
    ("S02", "Sudirman",    "Jakarta",   "Premium"),
    ("S03", "Dago",        "Bandung",   "Standard"),
    ("S04", "Setiabudi",   "Bandung",   "Standard"),
    ("S05", "Tunjungan",   "Surabaya",  "Premium"),
    ("S06", "Gubeng",      "Surabaya",  "Standard"),
    ("S07", "Malioboro",   "Yogyakarta","Standard"),
    ("S08", "Gejayan",     "Yogyakarta","Standard"),
    ("S09", "Sudirman",    "Medan",     "Premium"),
    ("S10", "GatotSubroto","Medan",     "Standard"),
    ("S11", "PantaiIndah", "Makassar",  "Standard"),
    ("S12", "SombaOpu",    "Makassar",  "Standard"),
]

CHANNELS = [
    ("ch_ig",      "Instagram",   "Social"),
    ("ch_fb",      "Facebook",    "Social"),
    ("ch_ga",      "Google Ads",  "Paid Search"),
    ("ch_tiktok",  "TikTok",      "Social"),
    ("ch_email",   "Email",       "Organic"),
    ("ch_organic", "Organic",     "Organic"),
]

PLANS = [
    ("PL_BASIC",   "Basic Monthly",    250000),
    ("PL_STD",     "Standard Monthly",  450000),
    ("SL_PREMIUM", "Premium Monthly",   750000),
    ("PL_ANNUAL",  "Annual Pro",      5000000),
]

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]
START = date(2025, 1, 1)
END = date(2025, 12, 31)
DAYS = (END - START).days + 1


def _ym(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def _lead_id() -> str:
    return f"L{uuid.uuid4().hex[:10].upper()}"


def generate(db_path: str, seed: int = 42) -> None:
    p = Path(db_path)
    if p.exists():
        print(f"Warehouse exists at {db_path}, skipping bootstrap.")
        return

    print(f"Generating full synthetic warehouse → {db_path} (seed={seed}) ...")
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        _generate_inner(p, seed)
    except BaseException:
        import traceback
        traceback.print_exc()
        p.unlink(missing_ok=True)
        raise


def _generate_inner(p: Path, seed: int = 42) -> None:
    con = duckdb.connect(str(p))
    try:
        con.execute("BEGIN TRANSACTION")

        schemas = ["main_marts", "main_intermediate", "main_seeds", "snapshots"]
        for s in schemas:
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")

        # ── create tables ───────────────────────────────────────────
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.dim_studio (studio_key VARCHAR, studio_code VARCHAR, studio_name VARCHAR, city VARCHAR, capacity_tier VARCHAR)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.dim_channel (channel_key VARCHAR, channel_name VARCHAR, channel_group VARCHAR)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.dim_date (date_day DATE, year_month VARCHAR)")
        con.execute("CREATE TABLE IF NOT EXISTS main_seeds.price_book (plan_code VARCHAR, plan_name VARCHAR, monthly_price INTEGER, valid_from DATE, valid_to DATE)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.fct_targets (studio_key VARCHAR, target_revenue INTEGER)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.fct_funnel_daily (date_day DATE, studio_key VARCHAR, channel_key VARCHAR, leads INTEGER, qualified INTEGER, booked INTEGER, visited INTEGER, purchased INTEGER)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.fct_revenue (sold_date DATE, studio_key VARCHAR, channel_key VARCHAR, amount INTEGER, lead_id VARCHAR, plan_name VARCHAR)")
        con.execute("CREATE TABLE IF NOT EXISTS main_intermediate.int_funnel_atomic (lead_id VARCHAR, created_date DATE, studio_code VARCHAR, channel_key VARCHAR)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.fct_ad_spend (date_day DATE, channel_key VARCHAR, spend INTEGER)")
        con.execute("CREATE TABLE IF NOT EXISTS main_marts.mart_executive_scorecard (year_month VARCHAR, city VARCHAR, revenue INTEGER, target_revenue INTEGER, cr_lead_qualified_pct FLOAT)")
        con.execute("CREATE TABLE IF NOT EXISTS snapshots.snap_channel_mapping (channel_raw VARCHAR, channel_name VARCHAR, channel_group VARCHAR, dbt_valid_from TIMESTAMP, dbt_valid_to TIMESTAMP)")

        # ── dim tables ──────────────────────────────────────────────
        for sc, name, city, tier in STUDIOS:
            con.execute(
                "INSERT INTO main_marts.dim_studio VALUES (?,?,?,?,?)",
                [sc, sc, name, city, tier],
            )

        for ck, cn, cg in CHANNELS:
            con.execute(
                "INSERT INTO main_marts.dim_channel VALUES (?,?,?)",
                [ck, cn, cg],
            )

        for d in range(DAYS):
            dt = START + timedelta(days=d)
            con.execute(
                "INSERT INTO main_marts.dim_date VALUES (?,?)",
                [dt, _ym(dt)],
            )

        # ── price_book ──────────────────────────────────────────────
        for pc, pn, pp in PLANS:
            con.execute(
                "INSERT INTO main_seeds.price_book VALUES (?,?,?,?,?)",
                [pc, pn, pp, "2025-01-01", "2025-12-31"],
            )

        # ── target revenue per studio per month ─────────────────────
        rng = random.Random(seed)
        monthly_target: dict[str, int] = {}
        for sc, _, city, tier in STUDIOS:
            base = 200_000_000 if tier == "Premium" else 100_000_000
            for m in MONTHS:
                tgt = round(rng.uniform(0.80, 1.20) * base)
                monthly_target[f"{sc}|{m}"] = tgt
                if m == "2025-01":
                    con.execute(
                        "INSERT INTO main_marts.fct_targets VALUES (?,?)",
                        [sc, tgt],
                    )

        # ── daily funnel + revenue + spend ──────────────────────────
        m_revenue: dict[str, float] = {}
        m_target: dict[str, float] = {}
        m_cr: dict[str, float] = {}

        daily_leads: list[dict] = []
        daily_qualified: list[dict] = []
        all_leads: list[tuple[str, date, str, str]] = []

        for d in range(DAYS):
            dt = START + timedelta(days=d)
            ym = _ym(dt)
            for sc, sname, city, tier in STUDIOS:
                base_leads = rng.randint(15, 40) if tier == "Premium" else rng.randint(8, 22)
                for ck, cn, cg in CHANNELS:
                    ch_mult = {"Instagram": 0.30, "Facebook": 0.18, "Google Ads": 0.25,
                               "TikTok": 0.12, "Email": 0.08, "Organic": 0.07}[cn]
                    leads = max(1, round(base_leads * ch_mult * rng.uniform(0.7, 1.3)))
                    qual = max(0, round(leads * rng.uniform(0.35, 0.65)))
                    booked = max(0, round(qual * rng.uniform(0.50, 0.80)))
                    visited = max(0, round(booked * rng.uniform(0.70, 0.95)))
                    purchased = max(0, round(visited * rng.uniform(0.40, 0.70)))

                    con.execute(
                        "INSERT INTO main_marts.fct_funnel_daily VALUES (?,?,?,?,?,?,?,?)",
                        [dt, sc, ck, leads, qual, booked, visited, purchased],
                    )

                    for _ in range(min(leads, 3)):
                        lid = _lead_id()
                        all_leads.append((lid, dt, sc, ck))

                    daily_leads.append({"day": dt, "val": leads, "city": city, "sc": sc})
                    daily_qualified.append({"day": dt, "val": qual, "city": city, "sc": sc})

                    for _ in range(purchased):
                        plan = rng.choice(PLANS)
                        lid = _lead_id()
                        amount = round(plan[2] * rng.uniform(0.9, 1.1))
                        con.execute(
                            "INSERT INTO main_marts.fct_revenue VALUES (?,?,?,?,?,?)",
                            [dt, sc, ck, amount, lid, plan[1]],
                        )
                        key = f"{city}|{ym}"
                        m_revenue.setdefault(key, 0)
                        m_revenue[key] += amount

        # ── int_funnel_atomic ───────────────────────────────────────
        for lid, dt, sc, ck in all_leads:
            con.execute(
                "INSERT INTO main_intermediate.int_funnel_atomic VALUES (?,?,?,?)",
                [lid, dt, sc, ck],
            )

        # ── ad_spend ────────────────────────────────────────────────
        for d in range(DAYS):
            dt = START + timedelta(days=d)
            for ck, cn, cg in CHANNELS:
                if cn == "Organic":
                    continue
                daily_budget = {"Instagram": 500_000, "Facebook": 350_000,
                                "Google Ads": 800_000, "TikTok": 300_000,
                                "Email": 100_000}[cn]
                spend = round(daily_budget * rng.uniform(0.7, 1.3))
                con.execute(
                    "INSERT INTO main_marts.fct_ad_spend VALUES (?,?,?)",
                    [dt, ck, spend],
                )

        # ── mart_executive_scorecard ────────────────────────────────
        cities = list({c for _, _, c, _ in STUDIOS})
        for city in cities:
            city_studios = [sc for sc, _, c, _ in STUDIOS if c == city]
            for ym in MONTHS:
                rev = m_revenue.get(f"{city}|{ym}", 0)
                tgt = sum(monthly_target.get(f"{sc}|{ym}", 0) for sc in city_studios)
                cr = round(rng.uniform(18.0, 42.0), 1)
                if city == "Jakarta" and ym == "2025-09":
                    cr = round(cr * 0.65, 1)
                con.execute(
                    "INSERT INTO main_marts.mart_executive_scorecard VALUES (?,?,?,?,?)",
                    [ym, city, round(rev), round(tgt), cr],
                )

        # ── snapshots (SCD2) ────────────────────────────────────────
        for ck, cn, cg in CHANNELS:
            con.execute(
                "INSERT INTO snapshots.snap_channel_mapping VALUES (?,?,?,?,?)",
                [cn.lower(), cn, cg, "2025-01-01 00:00:00", None],
            )

        con.execute("COMMIT")
    finally:
        con.close()
    _count_rows(p)


def _count_rows(p: Path) -> None:
    con2 = duckdb.connect(str(p))
    for tbl in [
        "main_marts.dim_studio", "main_marts.dim_channel",
        "main_marts.dim_date", "main_marts.fct_funnel_daily",
        "main_marts.fct_revenue", "main_marts.fct_ad_spend",
        "main_marts.mart_executive_scorecard", "main_marts.fct_targets",
        "main_intermediate.int_funnel_atomic", "main_seeds.price_book",
        "snapshots.snap_channel_mapping",
    ]:
        cnt = con2.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl}: {cnt:>8} rows")
    con2.close()
    print("✅ Synthetic warehouse ready.")


if __name__ == "__main__":
    from app.config import settings
    generate(settings.db_path)
