"""Generator invariants: if these fail, the warehouse tests upstream lose meaning."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator"))

from generate import generate, load_price_book, price_at  # noqa: E402


def small():
    return generate(days=30, seed=7)


def test_funnel_is_nested():
    data = small()
    c = data["counts"]
    assert c["leads"] >= c["bookings"] >= c["visits"] >= c["sales"] > 0


def test_ids_unique_before_dup_injection():
    data = small()
    ids = [r["lead_id"] for s in data["leads"].values() for r in s]
    assert len(ids) == len(set(ids))


def test_every_booking_references_a_lead():
    data = small()
    lead_ids = {r["lead_id"] for s in data["leads"].values() for r in s}
    for s in data["bookings"].values():
        for b in s:
            assert b["lead_id"] in lead_ids


def test_sale_amount_respects_effective_price():
    pb = load_price_book()
    data = small()
    for s in data["sales"].values():
        for sale in s:
            from datetime import date
            lp = price_at(pb, sale["plan_code"], date.fromisoformat(sale["sold_at"]))
            assert lp * 0.85 <= sale["amount"] <= lp


def test_deterministic_for_same_seed():
    a, b = generate(days=10, seed=99), generate(days=10, seed=99)
    assert a["counts"] == b["counts"]
