"""The AI Analyst · a two-tier engine.

Tier 1 (always on, no API key): a deterministic natural-language-to-insight
engine. It parses an intent (metric x dimension x period x comparison) from
bilingual (Indonesian + English) text, runs *safe, parameterized* queries via
queries.py, and returns a structured answer: prose with real numbers, an
ECharts spec, an optional table, and the provenance (which query produced it).

Tier 2 (optional): if an OpenAI-compatible LLM is configured, it rewrites the
tier-1 facts into fluent narrative and handles fuzzier multi-part questions,
but every number still originates from a tier-1 tool call ("no naked numbers").

Design goal: the chat feels intelligent and trustworthy even with zero cloud
dependencies, and a recruiter can read exactly how it works.
"""
from __future__ import annotations

import re

from . import insights, queries

# ---- vocabulary (bilingual) ---------------------------------------------

METRICS = {
    "revenue": ["revenue", "pendapatan", "omzet", "sales value", "penjualan"],
    "members": ["member", "members", "purchase", "pembelian", "konversi beli",
                "new member", "join"],
    "leads": ["lead", "leads", "prospek", "calon"],
    "cac": ["cac", "cost per acquisition", "biaya akuisisi", "cost acquisition"],
    "roas": ["roas", "return on ad spend", "return ad"],
    "cr": ["cr", "conversion rate", "konversi", "conversion", "tingkat konversi"],
    "spend": ["spend", "budget", "biaya iklan", "ad spend", "belanja iklan"],
    "cpl": ["cpl", "cost per lead", "biaya per lead"],
}

PERIOD_MONTHS = {
    "q1": ("01", "03"), "q2": ("04", "06"), "q3": ("07", "09"), "q4": ("10", "12"),
    "kuartal 1": ("01", "03"), "kuartal 2": ("04", "06"),
    "kuartal 3": ("07", "09"), "kuartal 4": ("10", "12"),
}
MONTH_WORDS = {
    "january": "01", "januari": "01", "february": "02", "februari": "02",
    "march": "03", "maret": "03", "april": "04", "may": "05", "mei": "05",
    "june": "06", "juni": "06", "july": "07", "juli": "07", "august": "08",
    "agustus": "08", "september": "09", "october": "10", "oktober": "10",
    "november": "11", "december": "12", "desember": "12",
}


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower().strip())


def parse_intent(text: str) -> dict:
    t = _norm(text)
    dims = queries.dimensions()
    intent: dict = {"raw": text, "filters": {}, "metric": None,
                    "comparison": None, "breakdown": None, "why": False}

    # metric
    for metric, kws in METRICS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in kws):
            intent["metric"] = metric
            break

    # filters: city / channel / studio
    for city in dims["cities"]:
        if city.lower() in t:
            intent["filters"]["city"] = city
    for ch in dims["channels"]:
        if ch.lower() in t:
            intent["filters"]["channel"] = ch
    for s in dims["studios"]:
        if s["studio_code"].lower() in t or s["studio_name"].lower() in t:
            intent["filters"]["studio"] = s["studio_code"]

    # period: quarter words / month words / explicit YYYY-MM
    year = (dims["month_max"] or "2025-12")[:4]
    for kw, (a, b) in PERIOD_MONTHS.items():
        if kw in t:
            intent["filters"]["month_from"] = f"{year}-{a}"
            intent["filters"]["month_to"] = f"{year}-{b}"
    for word, mm in MONTH_WORDS.items():
        if re.search(rf"\b{word}\b", t):
            intent["filters"]["month_from"] = f"{year}-{mm}"
            intent["filters"]["month_to"] = f"{year}-{mm}"
    m = re.search(r"(20\d{2})-(0[1-9]|1[0-2])", t)
    if m:
        intent["filters"]["month_from"] = intent["filters"]["month_to"] = m.group(0)

    # "last month" / "bulan lalu"
    if "last month" in t or "bulan lalu" in t or "bulan kemarin" in t:
        months = dims["months"]
        if len(months) >= 1:
            intent["filters"]["month_from"] = intent["filters"]["month_to"] = months[-1]

    # comparison
    if any(w in t for w in ["mom", "month over month", "bulan ke bulan",
                            "dibanding bulan", "vs last month"]):
        intent["comparison"] = "mom"
    if any(w in t for w in ["per channel", "by channel", "tiap channel",
                            "masing-masing channel", "per kanal"]):
        intent["breakdown"] = "channel"
    if any(w in t for w in ["per studio", "by studio", "tiap studio",
                            "per cabang", "masing-masing studio"]):
        intent["breakdown"] = "studio"
    if any(w in t for w in ["per city", "by city", "tiap kota", "per kota"]):
        intent["breakdown"] = "city"

    # intent type: why / miss-target / top
    if any(w in t for w in ["why", "kenapa", "mengapa", "penyebab", "turun",
                            "drop", "naik", "anjlok"]):
        intent["why"] = True
    if any(w in t for w in ["miss target", "below target", "miss", "gagal target",
                            "di bawah target", "tidak capai", "ga capai"]):
        intent["intent_type"] = "miss_target"
    if any(w in t for w in ["top", "terbaik", "tertinggi", "best", "paling tinggi"]):
        intent["intent_type"] = intent.get("intent_type") or "top"
    if any(w in t for w in ["forecast", "prediksi", "proyeksi", "ramalan",
                            "bulan depan", "next month"]):
        intent["intent_type"] = "forecast"
    if any(w in t for w in ["anomali", "anomaly", "aneh", "unusual", "outlier"]):
        intent["intent_type"] = "anomaly"
    return intent


# ---- formatting ----------------------------------------------------------

def _rp(n) -> str:
    if n is None:
        return "–"
    n = float(n)
    if abs(n) >= 1e9:
        return f"Rp {n/1e9:.2f} M"
    if abs(n) >= 1e6:
        return f"Rp {n/1e6:.1f} jt"
    return f"Rp {n:,.0f}".replace(",", ".")


def _num(n) -> str:
    return "–" if n is None else f"{n:,}".replace(",", ".")


def _period_label(f: dict) -> str:
    if f.get("month_from") and f.get("month_to"):
        return (f["month_from"] if f["month_from"] == f["month_to"]
                else f"{f['month_from']}…{f['month_to']}")
    return "full year"


# ---- handlers (each returns an answer dict) -----------------------------

def _answer(text, chart=None, table=None, sql="queries.py mart aggregate",
            followups=None):
    return {"text": text, "chart": chart, "table": table,
            "provenance": sql, "followups": followups or [], "tier": 1}


def h_forecast(intent):
    fc = insights.forecast_revenue()
    nxt = fc["forecast"][0]
    bt = fc["backtest_mape"]
    txt = (f"**Revenue forecast** (method: *{fc['best_method'].replace('_',' ')}*, "
           f"chosen by lowest backtest MAPE):\n\n"
           f"- Next month: **{_rp(nxt['forecast'])}** "
           f"(range {_rp(nxt['lower'])}–{_rp(nxt['upper'])})\n"
           f"- Backtest MAPE · seasonal-naive {bt['seasonal_naive']}%, "
           f"linear {bt['linear_trend']}%, damped {bt['damped_trend']}%.")
    chart = {
        "title": {"text": "Revenue forecast", "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category",
                  "data": [h["year_month"] for h in fc["history"]] +
                          [f["year_month"] for f in fc["forecast"]]},
        "yAxis": {"type": "value"},
        "series": [
            {"name": "Actual", "type": "line",
             "data": [h["revenue"] for h in fc["history"]] +
                     [None] * len(fc["forecast"])},
            {"name": "Forecast", "type": "line", "lineStyle": {"type": "dashed"},
             "data": [None] * (len(fc["history"]) - 1) +
                     [fc["history"][-1]["revenue"]] +
                     [f["forecast"] for f in fc["forecast"]]},
        ],
    }
    return _answer(txt, chart=chart, sql="insights.forecast_revenue()",
                   followups=["Which channel drives next month's revenue?",
                              "Show revenue attainment by city"])


def h_anomaly(intent):
    found = insights.scan_anomalies()
    f = intent.get("filters", {})
    if f.get("city"):
        found = [a for a in found if a["filter"].get("city") == f["city"]]
    if not found:
        return _answer("No statistically significant anomalies (>2σ) in the "
                       "scanned daily metrics for that scope.")
    top = found[0]
    rows = [{"metric": a["metric"], "where": a["dimension"],
             "when": a["label"], "change": f"{a['deviation_pct']}%",
             "z": a["z"]} for a in found[:8]]
    txt = (f"Found **{len(found)} anomalies**. Most significant: "
           f"**{top['metric']} {top['direction']}** in {top['dimension']} "
           f"around {top['label']} · {top['value']} vs expected ~{top['expected']} "
           f"({top['deviation_pct']}%, z={top['z']}).")
    return _answer(txt, table={"columns": list(rows[0].keys()), "rows": rows},
                   sql="insights.scan_anomalies()",
                   followups=[f"Why did CR drop in {top['dimension'].split(': ')[-1]}?"])


def h_why(intent):
    """Explain a movement by decomposing into the anomaly + contributing cut."""
    f = intent.get("filters", {})
    city = f.get("city")
    anomalies = insights.scan_anomalies()
    if city:
        anomalies = [a for a in anomalies if a["filter"].get("city") == city]
    if not anomalies:
        # fall back to MoM on the metric
        return h_metric({**intent, "comparison": "mom"})
    a = anomalies[0]
    # contributing breakdown: channel CR within that city
    cut = queries.channel_league({"city": city} if city else {})
    cut_sorted = sorted([c for c in cut if c["cvr"] is not None],
                        key=lambda x: x["cvr"])
    worst = cut_sorted[0] if cut_sorted else None
    txt = (f"**{a['metric']} {a['direction']}** in {a['dimension']} around "
           f"{a['label']}: {a['value']} vs an expected ~{a['expected']} "
           f"(**{a['deviation_pct']}%**, z={a['z']}).")
    if worst:
        txt += (f"\n\nLargest drag: **{worst['channel']}** "
                f"(lead→member {worst['cvr']}%, {worst['members']} members on "
                f"{worst['leads']} leads). The blended company average hides "
                f"this because other cities held steady.")
    chart = _city_cr_chart(city)
    return _answer(txt, chart=chart, sql="insights.scan_anomalies() + channel_league()",
                   followups=["Show this in the Funnel Explorer",
                              "CAC per channel for this city"])


def _city_cr_chart(highlight=None):
    matrix = queries.city_cr_matrix()
    cities = sorted({r["city"] for r in matrix})
    months = sorted({r["year_month"] for r in matrix})
    series = []
    for c in cities:
        data = []
        for m in months:
            rec = next((r for r in matrix if r["city"] == c and r["year_month"] == m), None)
            data.append(rec["cr_lead_qualified_pct"] if rec else None)
        series.append({"name": c, "type": "line", "data": data,
                       "lineStyle": {"width": 3 if c == highlight else 1.5}})
    return {"title": {"text": "Lead→Qualified CR by city", "left": "center"},
            "tooltip": {"trigger": "axis"}, "legend": {"top": 24},
            "xAxis": {"type": "category", "data": months},
            "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
            "series": series}


def h_miss_target(intent):
    studios = queries.studio_league(intent.get("filters"))
    missed = sorted([s for s in studios if s["attainment"] is not None
                     and s["attainment"] < 100], key=lambda x: x["attainment"])
    if not missed:
        return _answer("Every studio in scope hit ≥100% of its revenue target. 🎯")
    rows = [{"studio": s["studio_name"], "city": s["city"],
             "revenue": _rp(s["revenue"]), "target": _rp(s["target_revenue"]),
             "attainment": f"{s['attainment']}%"} for s in missed]
    txt = (f"**{len(missed)} studios** are below their revenue target. "
           f"Worst: **{missed[0]['studio_name']}** ({missed[0]['city']}) at "
           f"**{missed[0]['attainment']}%**.")
    chart = {"title": {"text": "Revenue attainment (<100%)", "left": "center"},
             "tooltip": {"trigger": "axis"},
             "xAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
             "yAxis": {"type": "category",
                       "data": [s["studio_name"] for s in missed[::-1]]},
             "series": [{"type": "bar",
                         "data": [s["attainment"] for s in missed[::-1]]}]}
    return _answer(txt, chart=chart, table={"columns": list(rows[0].keys()), "rows": rows},
                   sql="queries.studio_league()",
                   followups=["Forecast next month revenue",
                              "Which channel has the worst CAC?"])


def h_breakdown(intent):
    """metric broken down by channel/studio/city as a sorted table + bar."""
    metric = intent.get("metric") or "revenue"
    bd = intent["breakdown"]
    f = intent.get("filters", {})
    if bd == "channel":
        data = queries.channel_league(f)
        key = {"revenue": "revenue", "cac": "cac", "roas": "roas",
               "members": "members", "leads": "leads", "spend": "spend",
               "cpl": "cpl", "cr": "cvr"}.get(metric, "revenue")
        # paid-only metrics are meaningless for organic channels (no spend)
        if metric in ("cac", "cpl", "roas", "spend"):
            data = [d for d in data if (d.get("spend") or 0) > 0]
        data = [d for d in data if d.get(key) is not None]
        data.sort(key=lambda x: x[key], reverse=(metric not in ("cac", "cpl")))
        label = "channel"
    elif bd == "studio":
        data = queries.studio_league(f)
        key = {"revenue": "revenue", "members": "members", "leads": "leads"}.get(metric, "revenue")
        data.sort(key=lambda x: x.get(key) or 0, reverse=True)
        label = "studio_name"
    else:
        sc = [r for r in queries.city_cr_matrix()]
        agg: dict = {}
        for r in sc:
            agg.setdefault(r["city"], 0)
        data = [{"city": c} for c in agg]
        label = "city"
        return h_metric(intent)  # city breakdown handled via scorecard

    fmt = (_rp if metric in ("revenue", "spend", "cac", "cpl") else
           (lambda v: f"{v}×" if metric == "roas" else
            (lambda v: f"{v}%") if metric == "cr" else _num))
    rows = [{label: d.get(label) or d.get("channel"),
             metric: fmt(d.get(key))} for d in data[:12]]
    period = _period_label(f)
    txt = (f"**{metric.upper()} by {bd}** ({period}). "
           f"Top: **{rows[0][label]}** at {rows[0][metric]}.")
    chart = {"title": {"text": f"{metric} by {bd}", "left": "center"},
             "tooltip": {"trigger": "axis"},
             "xAxis": {"type": "category",
                       "data": [r[label] for r in rows], "axisLabel": {"rotate": 30}},
             "yAxis": {"type": "value"},
             "series": [{"type": "bar", "data": [d.get(key) for d in data[:12]]}]}
    return _answer(txt, chart=chart, table={"columns": list(rows[0].keys()), "rows": rows},
                   sql=f"queries.{bd}_league()",
                   followups=[f"Why is {rows[-1][label]} lowest?",
                              "Forecast next month revenue"])


def h_metric(intent):
    """Single metric for a scope, optionally with MoM comparison."""
    metric = intent.get("metric") or "revenue"
    f = intent.get("filters", {})
    period = _period_label(f)
    scope = []
    if f.get("city"):
        scope.append(f["city"])
    if f.get("channel"):
        scope.append(f["channel"])
    if f.get("studio"):
        scope.append(f["studio"])
    scope_txt = (" · ".join(scope)) if scope else "all studios"

    if intent.get("comparison") == "mom":
        mw = queries.kpis_with_mom(f)
        cur, delta = mw["current"], mw["delta"]
        val = cur.get(_metric_key(metric))
        d = delta.get(_metric_key(metric))
        arrow = "" if d is None else (" ▲" if d > 0 else " ▼")
        txt = (f"**{metric.upper()}** for {scope_txt} ({period}): "
               f"**{_fmt_metric(metric, val)}**"
               + (f", {abs(d)}%{arrow} vs previous month." if d is not None else "."))
        return _answer(txt, chart=_trend_chart(f, metric),
                       followups=[f"{metric} by channel", "Any anomalies?"])

    k = queries.kpis(f)
    val = k.get(_metric_key(metric))
    txt = f"**{metric.upper()}** for {scope_txt} ({period}): **{_fmt_metric(metric, val)}**."
    # add supporting context
    if metric == "revenue":
        txt += f" From {_num(k['members'])} new members (AOV {_rp(k['aov'])})."
    elif metric in ("cac", "roas"):
        txt += f" On {_rp(k['spend'])} spend, {_num(k['members'])} members."
    return _answer(txt, chart=_trend_chart(f, metric),
                   followups=[f"{metric} by channel", f"{metric} month over month",
                              "Forecast next month revenue"])


def _metric_key(metric):
    return {"cr": "cr_overall"}.get(metric, metric)


def _fmt_metric(metric, val):
    if val is None:
        return "no data"
    if metric in ("revenue", "spend", "cac", "cpl", "aov"):
        return _rp(val)
    if metric == "roas":
        return f"{val}×"
    if metric == "cr":
        return f"{val}%"
    return _num(val)


def _trend_chart(f, metric):
    data = queries.trend_monthly(f)
    key = {"revenue": "revenue", "members": "members", "leads": "leads",
           "spend": "spend"}.get(metric, "revenue")
    return {"title": {"text": f"{metric} trend", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [r["year_month"] for r in data]},
            "yAxis": {"type": "value"},
            "series": [{"type": "line", "smooth": True, "areaStyle": {},
                        "data": [r.get(key) for r in data]}]}


# ---- router --------------------------------------------------------------

def answer(text: str) -> dict:
    intent = parse_intent(text)
    it = intent.get("intent_type")
    try:
        if it == "forecast":
            return h_forecast(intent)
        if it == "anomaly":
            return h_anomaly(intent)
        if it == "miss_target":
            return h_miss_target(intent)
        if intent.get("why"):
            return h_why(intent)
        if intent.get("breakdown"):
            return h_breakdown(intent)
        if intent.get("metric"):
            return h_metric(intent)
    except Exception as e:  # never 500 the chat
        return _answer(f"I hit an error answering that ({type(e).__name__}). "
                       f"Try rephrasing, e.g. 'revenue Brightwater Q3'.")
    # no intent matched → guided suggestions
    return _answer(
        "I can answer questions about revenue, members, leads, CAC, ROAS, "
        "conversion, and forecasts · filtered by city, channel, studio, or "
        "period. Try one of these:",
        followups=["Revenue by channel for Q3",
                   "Why did CR drop in Crestline?",
                   "Which studios miss target?",
                   "Forecast next month revenue",
                   "CAC per channel last month"])
