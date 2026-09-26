"""The deterministic NLQ engine is the centerpiece — these lock its behavior
on the canonical questions (bilingual) so a refactor can't silently break it.
"""
from app import analyst


def test_intent_metric_and_filters():
    it = analyst.parse_intent("revenue Brightwater Q3")
    assert it["metric"] == "revenue"
    assert it["filters"]["city"] == "Brightwater"
    assert it["filters"]["month_from"] == "2025-07"
    assert it["filters"]["month_to"] == "2025-09"


def test_intent_indonesian_why():
    it = analyst.parse_intent("kenapa CR Crestline turun september?")
    assert it["filters"]["city"] == "Crestline"
    assert it["why"] is True
    assert it["filters"]["month_from"] == "2025-09"


def test_answer_revenue_has_numbers_and_chart():
    a = analyst.answer("revenue Brightwater Q3")
    assert "Rp" in a["text"]
    assert a["chart"] is not None
    assert a["tier"] == 1


def test_answer_why_explains_crestline():
    a = analyst.answer("kenapa CR Crestline turun september?")
    assert "Crestline" in a["text"]
    assert a["chart"] is not None  # city CR chart attached


def test_answer_miss_target_lists_studios():
    a = analyst.answer("which studios miss target?")
    assert "target" in a["text"].lower()
    assert a["table"] is not None


def test_answer_forecast_reports_method():
    a = analyst.answer("forecast next month revenue")
    assert "forecast" in a["text"].lower()
    assert "MAPE" in a["text"] or "method" in a["text"].lower()


def test_breakdown_excludes_organic_for_cac():
    a = analyst.answer("CAC per channel")
    # organic channels have no spend → must not appear in a CAC ranking
    rows = (a.get("table") or {}).get("rows", [])
    chans = [r.get("channel") for r in rows]
    assert "Referral" not in chans and "Walk-in" not in chans


def test_unknown_question_offers_suggestions():
    a = analyst.answer("hello there")
    assert a["followups"]
