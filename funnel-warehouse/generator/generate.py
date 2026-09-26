"""FitFlow synthetic funnel data generator.

Produces messy-on-purpose operational CSVs (per studio) plus reference seeds:

  data/drops/leads/<studio>.csv      3 header variants, 3 date formats, dup rows
  data/drops/bookings/<studio>.csv
  data/drops/visits/<studio>.csv     attended as Y/N/yes/no/1/0/TRUE/FALSE
  data/drops/sales/<studio>.csv
  data/drops/ad_spend/spend.csv      15% of spend values as "Rp 1.250.000" text
  dbt/seeds/monthly_targets.csv      targets derived from actuals (±)

Deterministic for a given --seed. Run:  python generator/generate.py --days 365
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (  # noqa: E402
    ANOMALY, ATTEND_BY_LEADTIME, ATTENDED_TOKENS_FALSE, ATTENDED_TOKENS_TRUE,
    CAPACITY_LEAD_BASE, CHANNELS, CPL_RANGE, DATE_FMT, DISCOUNTS, DUP_RATE,
    GROUP_QUALITY, LEADS_HEADERS, P_BOOKED, P_CANCELLED, P_PURCHASE,
    P_QUALIFIED, PLAN_WEIGHTS, SPEND_AS_TEXT_RATE, START_DATE, STUDIOS,
)

ROOT = Path(__file__).resolve().parents[1]


def load_channel_map() -> dict[str, tuple[str, str]]:
    out = {}
    with open(ROOT / "reference" / "channel_map.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["channel_raw"]] = (row["channel_name"], row["channel_group"])
    return out


def load_price_book() -> list[dict]:
    with open(ROOT / "dbt" / "seeds" / "price_book.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["monthly_price"] = int(r["monthly_price"])
        r["valid_from"] = date.fromisoformat(r["valid_from"])
        r["valid_to"] = date.fromisoformat(r["valid_to"])
    return rows


def price_at(price_book: list[dict], plan: str, d: date) -> int:
    for r in price_book:
        if r["plan_code"] == plan and r["valid_from"] <= d <= r["valid_to"]:
            return r["monthly_price"]
    raise ValueError(f"no price for {plan} at {d}")


def attend_prob(lead_time_days: int) -> float:
    for max_days, p in ATTEND_BY_LEADTIME:
        if lead_time_days <= max_days:
            return p
    return ATTEND_BY_LEADTIME[-1][1]


def weekday_factor(d: date) -> float:
    return {0: 1.1, 1: 1.0, 2: 1.0, 3: 1.05, 4: 1.15, 5: 1.35, 6: 0.9}[d.weekday()]


def inject_dups(rows: list, rate: float, rng: random.Random) -> list:
    dups = [r for r in rows if rng.random() < rate]
    out = rows + dups
    rng.shuffle(out)
    return out


def generate(days: int, seed: int) -> dict:
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)
    channel_map = load_channel_map()
    price_book = load_price_book()

    leads_by_studio: dict[str, list] = {s: [] for s in STUDIOS}
    bookings_by_studio: dict[str, list] = {s: [] for s in STUDIOS}
    visits_by_studio: dict[str, list] = {s: [] for s in STUDIOS}
    sales_by_studio: dict[str, list] = {s: [] for s in STUDIOS}
    spend_rows: list = []
    monthly_actuals: dict[tuple, dict] = {}

    lead_n = booking_n = visit_n = sale_n = 0
    end = START_DATE + timedelta(days=days - 1)

    for day_i in range(days):
        d = START_DATE + timedelta(days=day_i)
        daily_leads_by_channel: dict[str, int] = {}

        for studio_code, (_name, city, tier, variant) in STUDIOS.items():
            base = CAPACITY_LEAD_BASE[tier] * weekday_factor(d)
            for ch_raw, (weight, _is_paid) in CHANNELS.items():
                ch_name, ch_group = channel_map[ch_raw]
                mean = base * weight
                n = max(0, round(rng.gauss(mean, mean * 0.45)))
                daily_leads_by_channel[ch_raw] = daily_leads_by_channel.get(ch_raw, 0) + n

                p_q = P_QUALIFIED * GROUP_QUALITY[ch_group]
                if (city == ANOMALY["city"] and ch_group == ANOMALY["channel_group"]
                        and d >= ANOMALY["from"]):
                    p_q *= ANOMALY["qualified_multiplier"]

                for _ in range(n):
                    lead_n += 1
                    lead_id = f"L{lead_n:07d}"
                    qualified = rng.random() < min(p_q, 0.95)
                    status = ("qualified" if qualified
                              else rng.choice(["new", "contacted", "contacted", "disqualified"]))
                    leads_by_studio[studio_code].append({
                        "lead_id": lead_id, "studio_code": studio_code,
                        "channel": ch_raw,
                        "created_at": d.strftime(DATE_FMT[variant]),
                        "full_name": fake.name(), "phone": fake.msisdn()[:11],
                        "status": status,
                    })

                    mk = (d.strftime("%Y-%m"), studio_code)
                    acc = monthly_actuals.setdefault(
                        mk, {"leads": 0, "visits": 0, "revenue": 0})
                    acc["leads"] += 1

                    if not (qualified and rng.random() < P_BOOKED):
                        continue
                    booking_n += 1
                    booking_id = f"B{booking_n:07d}"
                    booked_at = d + timedelta(days=rng.randint(0, 2))
                    trial_date = booked_at + timedelta(days=rng.randint(1, 7))
                    cancelled = rng.random() < P_CANCELLED
                    if trial_date > end:
                        continue  # trial falls outside the generated window
                    bookings_by_studio[studio_code].append({
                        "booking_id": booking_id, "lead_id": lead_id,
                        "booked_at": booked_at.isoformat(),
                        "trial_date": trial_date.isoformat(),
                        "booking_status": "cancelled" if cancelled else "scheduled",
                    })
                    if cancelled:
                        continue

                    visit_n += 1
                    lead_time = (trial_date - d).days
                    attended = rng.random() < attend_prob(lead_time)
                    token = rng.choice(ATTENDED_TOKENS_TRUE if attended
                                       else ATTENDED_TOKENS_FALSE)
                    visits_by_studio[studio_code].append({
                        "visit_id": f"V{visit_n:07d}", "booking_id": booking_id,
                        "visit_date": trial_date.isoformat(), "attended": token,
                    })
                    if attended:
                        acc2 = monthly_actuals.setdefault(
                            (trial_date.strftime("%Y-%m"), studio_code),
                            {"leads": 0, "visits": 0, "revenue": 0})
                        acc2["visits"] += 1

                    if not (attended and rng.random() < P_PURCHASE):
                        continue
                    sale_n += 1
                    sold_at = trial_date + timedelta(days=rng.randint(0, 2))
                    if sold_at > end:
                        sold_at = end
                    plan = rng.choices(list(PLAN_WEIGHTS), weights=list(PLAN_WEIGHTS.values()))[0]
                    list_price = price_at(price_book, plan, sold_at)
                    amount = round(list_price * (1 - rng.choice(DISCOUNTS)))
                    sales_by_studio[studio_code].append({
                        "sale_id": f"SA{sale_n:07d}", "lead_id": lead_id,
                        "plan_code": plan, "sold_at": sold_at.isoformat(),
                        "amount": amount,
                        "payment_status": rng.choice(["paid", "paid", "paid", "installment"]),
                    })
                    acc3 = monthly_actuals.setdefault(
                        (sold_at.strftime("%Y-%m"), studio_code),
                        {"leads": 0, "visits": 0, "revenue": 0})
                    acc3["revenue"] += amount

        # ad spend per raw paid channel, loosely tied to lead volume
        for ch_raw, (_w, is_paid) in CHANNELS.items():
            if not is_paid:
                continue
            n_leads = daily_leads_by_channel.get(ch_raw, 0)
            cpl = rng.randint(*CPL_RANGE)
            spend = n_leads * cpl
            if spend == 0:
                continue
            spend_val = (f"Rp {spend:,}".replace(",", ".")
                         if rng.random() < SPEND_AS_TEXT_RATE else str(spend))
            spend_rows.append({
                "spend_date": d.isoformat(), "channel": ch_raw, "spend": spend_val,
                "impressions": n_leads * rng.randint(180, 420),
                "clicks": n_leads * rng.randint(4, 12),
            })

    return {
        "leads": leads_by_studio, "bookings": bookings_by_studio,
        "visits": visits_by_studio, "sales": sales_by_studio,
        "spend": spend_rows, "monthly_actuals": monthly_actuals, "rng": rng,
        "counts": {"leads": lead_n, "bookings": booking_n,
                   "visits": visit_n, "sales": sale_n},
    }


def write_csv(path: Path, rows: list[dict], header: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header or keys)
        for r in rows:
            w.writerow([r[k] for k in keys])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    data = generate(args.days, args.seed)
    rng = data["rng"]
    drops = ROOT / "data" / "drops"

    for studio_code, (_n, _c, _t, variant) in STUDIOS.items():
        write_csv(drops / "leads" / f"{studio_code}.csv",
                  inject_dups(data["leads"][studio_code], DUP_RATE["leads"], rng),
                  header=LEADS_HEADERS[variant])
        write_csv(drops / "bookings" / f"{studio_code}.csv",
                  inject_dups(data["bookings"][studio_code], DUP_RATE["bookings"], rng))
        write_csv(drops / "visits" / f"{studio_code}.csv",
                  inject_dups(data["visits"][studio_code], DUP_RATE["visits"], rng))
        write_csv(drops / "sales" / f"{studio_code}.csv",
                  inject_dups(data["sales"][studio_code], DUP_RATE["sales"], rng))

    write_csv(drops / "ad_spend" / "spend.csv", data["spend"])

    targets = [
        {"month": m, "studio_code": s,
         "target_leads": max(1, round(v["leads"] * rng.uniform(0.92, 1.12))),
         "target_visits": max(1, round(v["visits"] * rng.uniform(0.92, 1.12))),
         "target_revenue": round(v["revenue"] * rng.uniform(0.92, 1.12))}
        for (m, s), v in sorted(data["monthly_actuals"].items())
    ]
    write_csv(ROOT / "dbt" / "seeds" / "monthly_targets.csv", targets)

    c = data["counts"]
    print(f"generated {args.days}d seed={args.seed}: "
          f"{c['leads']:,} leads, {c['bookings']:,} bookings, "
          f"{c['visits']:,} visits, {c['sales']:,} sales, "
          f"{len(data['spend']):,} spend rows")


if __name__ == "__main__":
    main()
