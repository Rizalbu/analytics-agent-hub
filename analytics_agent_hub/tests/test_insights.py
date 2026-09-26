"""Anomaly + forecast invariants."""
from app import insights


def test_scan_finds_crestline_drop():
    found = insights.scan_anomalies()
    crest = [a for a in found if a["filter"].get("city") == "Crestline"
             and "CR" in a["metric"] and a["direction"] == "drop"]
    assert crest, "scripted Crestline CR collapse must be detected"
    assert crest[0]["z"] <= -2


def test_forecast_picks_best_by_mape():
    fc = insights.forecast_revenue()
    assert fc["best_method"] in fc["backtest_mape"]
    best = fc["backtest_mape"][fc["best_method"]]
    assert all(best <= v for v in fc["backtest_mape"].values())
    assert len(fc["forecast"]) == 3
    assert fc["forecast"][0]["lower"] <= fc["forecast"][0]["forecast"] <= fc["forecast"][0]["upper"]


def test_insights_feed_nonempty():
    feed = insights.insights_feed()
    assert feed and all("title" in f and "severity" in f for f in feed)
