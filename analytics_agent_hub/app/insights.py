"""Data-science layer: anomaly detection, forecasting, and an auto-generated
insights feed. Pure Python + SQL aggregates · no heavyweight ML deps, so the
logic is transparent and every number is reproducible.
"""
from __future__ import annotations

import statistics
from datetime import date, timedelta

from . import db, queries


# ---- anomaly detection ---------------------------------------------------

def _rolling_z(series: list[tuple[str, float]], window: int = 28,
               min_history: int = 14, z: float = 3.0) -> list[dict]:
    """Flag points whose value deviates > z rolling stdevs from the trailing
    mean. Guards against tiny histories (min_history) and zero variance."""
    out = []
    for i, (label, val) in enumerate(series):
        hist = [v for _, v in series[max(0, i - window):i]]
        if len(hist) < min_history:
            continue
        mu = statistics.mean(hist)
        sd = statistics.pstdev(hist)
        if sd == 0:
            continue
        score = (val - mu) / sd
        if abs(score) >= z:
            out.append({
                "label": label, "value": round(val, 2), "expected": round(mu, 2),
                "z": round(score, 2),
                "direction": "spike" if score > 0 else "drop",
                "deviation_pct": round((val - mu) / mu * 100, 1) if mu else None,
            })
    return out


def scan_anomalies() -> list[dict]:
    """Scan key daily metrics per city for anomalies. Returns ranked findings,
    each with a deep-link filter the UI can apply."""
    findings = []
    cities = queries.dimensions()["cities"]

    # daily lead->qualified CR per city (the Crestline story lives here)
    for city in cities:
        daily = db.rows("""
            select d.date_day::varchar as lbl,
                   sum(f.qualified)*100.0/nullif(sum(f.leads),0) cr
            from main_marts.fct_funnel_daily f
            join main_marts.dim_studio s on f.studio_key = s.studio_key
            join main_marts.dim_date d on f.date_day = d.date_day
            where s.city = ?
            group by 1 order by 1""", [city])
        series = [(r["lbl"], r["cr"]) for r in daily if r["cr"] is not None]
        # aggregate to weekly to reduce daily noise
        weekly = _to_weekly(series)
        for a in _rolling_z(weekly, window=8, min_history=5, z=2.2):
            findings.append({
                "metric": "Lead→Qualified CR", "dimension": f"City: {city}",
                "filter": {"city": city}, "unit": "%", **a,
            })

    # daily revenue per city
    for city in cities:
        daily = db.rows("""
            select d.date_day::varchar as lbl, sum(r.amount) rev
            from main_marts.fct_revenue r
            join main_marts.dim_studio s on r.studio_key = s.studio_key
            join main_marts.dim_date d on r.sold_date = d.date_day
            where s.city = ? group by 1 order by 1""", [city])
        weekly = _to_weekly([(r["lbl"], r["rev"] or 0) for r in daily])
        for a in _rolling_z(weekly, window=8, min_history=5, z=2.5):
            findings.append({
                "metric": "Revenue", "dimension": f"City: {city}",
                "filter": {"city": city}, "unit": "Rp", **a,
            })

    findings.sort(key=lambda x: abs(x["z"]), reverse=True)
    return findings


def _to_weekly(series: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Collapse a daily (label=ISO date) series into ISO-week means."""
    buckets: dict[str, list[float]] = {}
    for label, val in series:
        d = date.fromisoformat(label)
        wk = (d - timedelta(days=d.weekday())).isoformat()
        buckets.setdefault(wk, []).append(val)
    return [(wk, statistics.mean(vs)) for wk, vs in sorted(buckets.items())]


# ---- forecasting ---------------------------------------------------------

def _seasonal_naive(values: list[float], horizon: int, period: int = 1) -> list[float]:
    return [values[-period] for _ in range(horizon)]


def _trend(values: list[float], horizon: int) -> list[float]:
    """Linear least-squares trend extrapolation."""
    n = len(values)
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(values) / n
    denom = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, values)) / denom
    intercept = my - slope * mx
    return [intercept + slope * (n + h) for h in range(horizon)]


def _damped_trend(values: list[float], horizon: int, phi: float = 0.85) -> list[float]:
    """Trend with a damping factor so projections don't run away."""
    base = values[-1]
    n = len(values)
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(values) / n
    denom = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, values)) / denom
    out, damp = [], 0.0
    for h in range(1, horizon + 1):
        damp += phi ** h
        out.append(base + slope * damp)
    return out


def _mape(actual: list[float], pred: list[float]) -> float:
    pairs = [(a, p) for a, p in zip(actual, pred) if a]
    if not pairs:
        return float("nan")
    return round(sum(abs(a - p) / a for a, p in pairs) / len(pairs) * 100, 1)


def forecast_revenue(horizon: int = 3, method_param: str | None = None) -> dict:
    """Forecast monthly revenue with 3 methods + a rolling backtest that picks
    the winner by MAPE. Honest model comparison is the point (DS signal)."""
    rows = db.rows("""
        select d.year_month ym, sum(r.amount) rev
        from main_marts.fct_revenue r
        join main_marts.dim_date d on r.sold_date = d.date_day
        group by 1 order by 1""")
    months = [r["ym"] for r in rows]
    vals = [float(r["rev"] or 0) for r in rows]
    methods = {
        "seasonal_naive": _seasonal_naive,
        "linear_trend": _trend,
        "damped_trend": _damped_trend,
    }

    # rolling-origin backtest on the last 4 points (1-step ahead)
    backtest = {}
    for name, fn in methods.items():
        errs_actual, errs_pred = [], []
        for cut in range(max(4, len(vals) - 4), len(vals)):
            train = vals[:cut]
            if len(train) < 3:
                continue
            pred = fn(train, 1)[0]
            errs_actual.append(vals[cut])
            errs_pred.append(pred)
        backtest[name] = _mape(errs_actual, errs_pred)

    best = min(backtest, key=lambda k: backtest[k])
    # allow user override
    if method_param and method_param in methods:
        best = method_param
    fc_vals = methods[best](vals, horizon)
    # crude CI band from backtest error
    err = (backtest[best] or 10) / 100
    fc = []
    last = date.fromisoformat(months[-1] + "-01")
    for h, v in enumerate(fc_vals, 1):
        m = (last.replace(day=1) + timedelta(days=32 * h)).strftime("%Y-%m")
        fc.append({
            "year_month": m, "forecast": round(v),
            "lower": round(v * (1 - err)), "upper": round(v * (1 + err)),
        })
    return {
        "history": [{"year_month": m, "revenue": round(v)}
                    for m, v in zip(months, vals)],
        "forecast": fc, "best_method": best, "backtest_mape": backtest,
    }


# ---- auto insights feed --------------------------------------------------

def insights_feed(limit: int = 6) -> list[dict]:
    """Plain-language bullets for the Overview. Generated from anomalies +
    league extremes + target pace · each carries a severity and a deep link."""
    feed: list[dict] = []

    for a in scan_anomalies()[:3]:
        arrow = "▼" if a["direction"] == "drop" else "▲"
        feed.append({
            "severity": "alert" if a["direction"] == "drop" else "info",
            "title": f"{a['metric']} {a['direction']} · {a['dimension']}",
            "detail": (f"{arrow} {abs(a['deviation_pct'])}% vs expected "
                       f"({a['value']} vs ~{a['expected']}{a['unit'] if a['unit']=='%' else ''}) "
                       f"around {a['label']}"),
            "filter": a["filter"],
        })

    league = queries.channel_league()
    if league:
        best = max((c for c in league if c["roas"]), key=lambda x: x["roas"], default=None)
        worst = min((c for c in league if c["cac"]), key=lambda x: -(x["cac"] or 0), default=None)
        if best:
            feed.append({
                "severity": "good",
                "title": f"Best ROAS channel · {best['channel']}",
                "detail": f"ROAS {best['roas']}× on {best['members']} members "
                          f"({best['group']}).",
                "filter": {"channel": best["channel"]},
            })

    studios = queries.studio_league()
    missed = [s for s in studios if s["attainment"] and s["attainment"] < 90]
    if missed:
        worst = min(missed, key=lambda x: x["attainment"])
        feed.append({
            "severity": "alert",
            "title": f"{len(missed)} studios below 90% revenue target",
            "detail": f"Lowest: {worst['studio_name']} at {worst['attainment']}% "
                      f"of target.",
            "filter": {"studio": worst["studio_code"]},
        })

    fc = forecast_revenue()
    if fc["forecast"]:
        nxt = fc["forecast"][0]
        feed.append({
            "severity": "info",
            "title": f"Next-month revenue forecast: Rp {nxt['forecast']/1e6:.0f} jt",
            "detail": f"Method: {fc['best_method'].replace('_',' ')} "
                      f"(backtest MAPE {fc['backtest_mape'][fc['best_method']]}%).",
            "filter": {},
        })
    return feed[:limit]
