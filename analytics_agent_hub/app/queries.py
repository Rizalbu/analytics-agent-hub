"""All warehouse reads live here. SQL only touches mart/dim tables · there is
no string interpolation of user input; every filter is a bound parameter and
every dimension value is validated against a known allow-list (`dimensions()`).

This module is the single source of truth for numbers shown in the UI AND for
the AI analyst's tool calls, so a figure in the chat always matches a chart.
"""
from __future__ import annotations

from typing import Any

from . import db

# ---- joined base CTEs (reused everywhere) -------------------------------

_FUNNEL_BASE = """
with f as (
    select
        d.date_day, d.year_month, s.studio_code, s.studio_name, s.city,
        s.capacity_tier, c.channel_name, c.channel_group,
        f.leads, f.qualified, f.booked, f.visited, f.purchased
    from main_marts.fct_funnel_daily f
    join main_marts.dim_studio  s on f.studio_key  = s.studio_key
    join main_marts.dim_channel c on f.channel_key = c.channel_key
    join main_marts.dim_date    d on f.date_day    = d.date_day
)
"""


def _where(filters: dict | None) -> tuple[str, list[Any]]:
    """Build a parameterized WHERE from validated filters.

    A studio is more specific than a city, so when both are set the studio
    wins (prevents the 'Arden + a Crestline studio = 0 rows' dead end)."""
    filters = filters or {}
    clauses, params = [], []
    dims = dimensions()
    studio_set = filters.get("studio") in dims["studio_codes"]
    if filters.get("city") and filters["city"] in dims["cities"] and not studio_set:
        clauses.append("city = ?")
        params.append(filters["city"])
    if filters.get("channel") and filters["channel"] in dims["channels"]:
        clauses.append("channel_name = ?")
        params.append(filters["channel"])
    if filters.get("studio") and filters["studio"] in dims["studio_codes"]:
        clauses.append("studio_code = ?")
        params.append(filters["studio"])
    if filters.get("month_from"):
        clauses.append("year_month >= ?")
        params.append(filters["month_from"])
    if filters.get("month_to"):
        clauses.append("year_month <= ?")
        params.append(filters["month_to"])
    sql = (" where " + " and ".join(clauses)) if clauses else ""
    return sql, params


# ---- dimensions / metadata ----------------------------------------------

import time

_dim_cache = None
_dim_cache_time = 0

def dimensions() -> dict:
    global _dim_cache, _dim_cache_time
    now = time.time()
    if _dim_cache is not None and now - _dim_cache_time < 300:
        return _dim_cache

    cities = [r["city"] for r in db.rows(
        "select distinct city from main_marts.dim_studio order by 1")]
    channels = [r["channel_name"] for r in db.rows(
        "select distinct channel_name from main_marts.dim_channel order by 1")]
    studios = db.rows(
        "select studio_code, studio_name, city, capacity_tier "
        "from main_marts.dim_studio order by studio_code")
    months = [r["year_month"] for r in db.rows(
        "select distinct year_month from main_marts.mart_executive_scorecard "
        "order by 1")]
    
    _dim_cache = {
        "cities": cities,
        "channels": channels,
        "studios": studios,
        "studio_codes": [s["studio_code"] for s in studios],
        "months": months,
        "month_min": months[0] if months else None,
        "month_max": months[-1] if months else None,
    }
    _dim_cache_time = now
    return _dim_cache


# ---- Overview ------------------------------------------------------------

def kpis(filters: dict | None = None) -> dict:
    w, p = _where(filters)
    cur = db.row(f"""{_FUNNEL_BASE}
        select sum(leads) leads, sum(qualified) qualified, sum(booked) booked,
               sum(visited) visited, sum(purchased) purchased
        from f {w}""", p) or {}
    rev = db.row(f"""
        select sum(amount) revenue, count(*) sales,
               avg(amount) aov
        from main_marts.fct_revenue r
        join main_marts.dim_studio s on r.studio_key = s.studio_key
        join main_marts.dim_channel c on r.channel_key = c.channel_key
        {_rev_where(filters)[0]}""", _rev_where(filters)[1]) or {}
    spend = _scope_spend(filters)
    purchased = cur.get("purchased") or 0
    revenue = rev.get("revenue") or 0
    return {
        "leads": cur.get("leads") or 0,
        "qualified": cur.get("qualified") or 0,
        "visited": cur.get("visited") or 0,
        "members": purchased,
        "revenue": revenue,
        "aov": round(rev.get("aov") or 0),
        "spend": round(spend),
        "cac": round(spend / purchased) if purchased else None,
        "roas": round(revenue / spend, 2) if spend else None,
        "cr_overall": round(purchased / cur["leads"] * 100, 2)
        if cur.get("leads") else None,
    }


def kpis_with_mom(filters: dict | None = None) -> dict:
    """Current KPI set plus month-over-month deltas on the last full month."""
    months = dimensions()["months"]
    cur = kpis(filters)
    if len(months) < 2:
        return {"current": cur, "delta": {}}
    last, prev = months[-1], months[-2]
    f_last = {**(filters or {}), "month_from": last, "month_to": last}
    f_prev = {**(filters or {}), "month_from": prev, "month_to": prev}
    a, b = kpis(f_last), kpis(f_prev)
    delta = {}
    for k in ("leads", "members", "revenue", "cac", "roas", "cr_overall"):
        av, bv = a.get(k), b.get(k)
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)) and bv:
            delta[k] = round((av - bv) / bv * 100, 1)
    return {"current": cur, "delta": delta, "last_month": last}


def trend_monthly(filters: dict | None = None) -> list[dict]:
    w, p = _where(filters)
    funnel = db.rows(f"""{_FUNNEL_BASE}
        select year_month, sum(leads) leads, sum(purchased) members
        from f {w} group by 1 order by 1""", p)
    rw, rp = _rev_where(filters)
    rev = {r["year_month"]: r for r in db.rows(f"""
        select d.year_month, sum(r.amount) revenue
        from main_marts.fct_revenue r
        join main_marts.dim_studio s on r.studio_key = s.studio_key
        join main_marts.dim_channel c on r.channel_key = c.channel_key
        join main_marts.dim_date d on r.sold_date = d.date_day
        {rw} group by 1""", rp)}
    # spend per month, allocated to the scope by that month's lead share
    chan = {k: v for k, v in (filters or {}).items() if k == "channel"}
    sw, sp = _spend_where(chan)
    spend_tot = {r["year_month"]: r["spend"] for r in db.rows(f"""
        select d.year_month, sum(a.spend) spend
        from main_marts.fct_ad_spend a
        join main_marts.dim_channel c on a.channel_key = c.channel_key
        join main_marts.dim_date d on a.date_day = d.date_day
        {sw} group by 1""", sp)}
    gw, gp = _where(chan)
    glob = {r["year_month"]: r["leads"] for r in db.rows(f"""{_FUNNEL_BASE}
        select year_month, sum(leads) leads from f {gw} group by 1""", gp)}
    for r in funnel:
        ym = r["year_month"]
        r["revenue"] = (rev.get(ym) or {}).get("revenue") or 0
        share = (r["leads"] / glob[ym]) if glob.get(ym) else 0
        r["spend"] = round((spend_tot.get(ym) or 0) * share)
    return funnel


def city_cr_matrix() -> list[dict]:
    """Lead->qualified CR per city per month · surfaces the Crestline story."""
    return db.rows("""
        select year_month, city, cr_lead_qualified_pct
        from main_marts.mart_executive_scorecard order by city, year_month""")


# ---- Funnel Explorer -----------------------------------------------------

def funnel(filters: dict | None = None) -> dict:
    w, p = _where(filters)
    r = db.row(f"""{_FUNNEL_BASE}
        select sum(leads) leads, sum(qualified) qualified, sum(booked) booked,
               sum(visited) visited, sum(purchased) purchased
        from f {w}""", p) or {}
    stages = ["leads", "qualified", "booked", "visited", "purchased"]
    vals = [r.get(s) or 0 for s in stages]
    steps = []
    for i in range(1, len(stages)):
        prev, cur = vals[i - 1], vals[i]
        steps.append({
            "from": stages[i - 1], "to": stages[i],
            "rate": round(cur / prev * 100, 1) if prev else None,
            "drop": prev - cur,
        })
    return {"stages": stages, "values": vals, "steps": steps}


def cohort_lag(filters: dict | None = None) -> list[dict]:
    """Distribution of lead->purchase lag in days (point-in-time correct).
    Filters apply to the `atom` CTE columns (alias a), so build the WHERE
    against `a.` rather than the dim aliases used elsewhere."""
    f = filters or {}
    clauses, rp = [], []
    dims = dimensions()
    studio_set = f.get("studio") in dims["studio_codes"]
    if f.get("city") in dims["cities"] and not studio_set:
        clauses.append("a.city = ?"); rp.append(f["city"])
    if f.get("channel") in dims["channels"]:
        clauses.append("a.channel_name = ?"); rp.append(f["channel"])
    if studio_set:
        clauses.append("a.studio_code = ?"); rp.append(f["studio"])
    if f.get("month_from"):
        clauses.append("strftime(r.sold_date,'%Y-%m') >= ?"); rp.append(f["month_from"])
    if f.get("month_to"):
        clauses.append("strftime(r.sold_date,'%Y-%m') <= ?"); rp.append(f["month_to"])
    rw = (" where " + " and ".join(clauses)) if clauses else ""
    return db.rows(f"""
        with atom as (
            select a.lead_id, a.created_date, s.city, s.studio_code, c.channel_name
            from main_intermediate.int_funnel_atomic a
            join main_marts.dim_studio s on a.studio_code = s.studio_code
            left join main_marts.dim_channel c on a.channel_key = c.channel_key
        )
        select
            case
                when datediff('day', created_date, sold_date) <= 7 then '0-7d'
                when datediff('day', created_date, sold_date) <= 14 then '8-14d'
                when datediff('day', created_date, sold_date) <= 30 then '15-30d'
                else '30d+'
            end as bucket,
            count(*) n
        from main_marts.fct_revenue r
        join atom a on r.lead_id = a.lead_id
        {rw}
        group by 1
        order by case bucket when '0-7d' then 1 when '8-14d' then 2
                             when '15-30d' then 3 else 4 end
    """, rp)


# ---- Channels & Spend ----------------------------------------------------

def channel_league(filters: dict | None = None) -> list[dict]:
    w, p = _where(filters)
    leads = {r["channel_name"]: r for r in db.rows(f"""{_FUNNEL_BASE}
        select channel_name, channel_group, sum(leads) leads,
               sum(purchased) members
        from f {w} group by 1,2""", p)}
    alloc = _alloc_spend_by_channel(filters)
    spend = {ch: {"spend": v} for ch, v in alloc.items()}
    rw, rp = _rev_where(filters)
    rev = {r["channel_name"]: r["revenue"] for r in db.rows(f"""
        select c.channel_name, sum(r.amount) revenue
        from main_marts.fct_revenue r
        join main_marts.dim_channel c on r.channel_key = c.channel_key
        join main_marts.dim_studio s on r.studio_key = s.studio_key
        join main_marts.dim_date d on r.sold_date = d.date_day
        {rw} group by 1""", rp)}
    out = []
    for ch, lr in leads.items():
        sp_v = (spend.get(ch) or {}).get("spend") or 0
        members = lr["members"] or 0
        rv = rev.get(ch) or 0
        clicks = (spend.get(ch) or {}).get("clicks") or 0
        out.append({
            "channel": ch, "group": lr["channel_group"],
            "leads": lr["leads"] or 0, "members": members,
            "spend": round(sp_v), "revenue": rv,
            "cpl": round(sp_v / lr["leads"]) if lr["leads"] else None,
            "cac": round(sp_v / members) if members else None,
            "roas": round(rv / sp_v, 2) if sp_v else None,
            "cvr": round(members / lr["leads"] * 100, 2) if lr["leads"] else None,
        })
    out.sort(key=lambda x: x["revenue"], reverse=True)
    return out


def channel_mix_monthly() -> list[dict]:
    return db.rows(f"""{_FUNNEL_BASE}
        select year_month, channel_group, sum(leads) leads
        from f group by 1,2 order by 1,2""")


def scd2_channel_history() -> list[dict]:
    """SCD2 snapshot history if present (DE flex). Empty if no snapshot run."""
    try:
        return db.rows("""
            select channel_raw, channel_name, channel_group,
                   dbt_valid_from::date valid_from,
                   coalesce(dbt_valid_to::date::varchar,'current') valid_to
            from snapshots.snap_channel_mapping
            order by channel_name, dbt_valid_from""")
    except Exception:
        return []


# ---- Studios -------------------------------------------------------------

def studio_league(filters: dict | None = None) -> list[dict]:
    w, p = _where(filters)
    base = db.rows(f"""{_FUNNEL_BASE}
        select studio_code, studio_name, city, capacity_tier,
               sum(leads) leads, sum(visited) visited, sum(purchased) members
        from f {w} group by 1,2,3,4""", p)
    rw, rp = _rev_where(filters)
    rev = {r["studio_code"]: r["revenue"] for r in db.rows(f"""
        select s.studio_code, sum(r.amount) revenue
        from main_marts.fct_revenue r
        join main_marts.dim_studio s on r.studio_key = s.studio_key
        join main_marts.dim_channel c on r.channel_key = c.channel_key
        join main_marts.dim_date d on r.sold_date = d.date_day
        {rw} group by 1""", rp)}
    tgt = {r["studio_code"]: r["t"] for r in db.rows("""
        select s.studio_code, sum(t.target_revenue) t
        from main_marts.fct_targets t
        join main_marts.dim_studio s on t.studio_key = s.studio_key
        group by 1""")}
    for r in base:
        r["revenue"] = rev.get(r["studio_code"]) or 0
        tv = tgt.get(r["studio_code"]) or 0
        r["target_revenue"] = tv
        r["attainment"] = round(r["revenue"] / tv * 100, 1) if tv else None
    base.sort(key=lambda x: x["revenue"], reverse=True)
    return base


# ---- Revenue & Targets ---------------------------------------------------

def plan_mix_monthly() -> list[dict]:
    return db.rows("""
        select d.year_month, r.plan_name, sum(r.amount) revenue, count(*) n
        from main_marts.fct_revenue r
        join main_marts.dim_date d on r.sold_date = d.date_day
        group by 1,2 order by 1,2""")


def attainment_by_city() -> list[dict]:
    return db.rows("""
        select city,
               sum(revenue) revenue, sum(target_revenue) target_revenue,
               round(sum(revenue)*100.0/nullif(sum(target_revenue),0),1) attainment
        from main_marts.mart_executive_scorecard
        group by 1 order by 1""")


def price_changes() -> list[dict]:
    return db.rows("""
        select plan_name, monthly_price, valid_from, valid_to
        from main_seeds.price_book order by plan_code, valid_from""")


# ---- shared where helpers for revenue/spend (need date join) -------------

def _rev_where(filters: dict | None, alias_join: bool = False):
    filters = filters or {}
    clauses, params = [], []
    dims = dimensions()
    if filters.get("city") in dims["cities"]:
        clauses.append("s.city = ?"); params.append(filters["city"])
    if filters.get("channel") in dims["channels"]:
        clauses.append("c.channel_name = ?"); params.append(filters["channel"])
    if filters.get("studio") in dims["studio_codes"]:
        clauses.append("s.studio_code = ?"); params.append(filters["studio"])
    if filters.get("month_from"):
        clauses.append("strftime(r.sold_date,'%Y-%m') >= ?")
        params.append(filters["month_from"])
    if filters.get("month_to"):
        clauses.append("strftime(r.sold_date,'%Y-%m') <= ?")
        params.append(filters["month_to"])
    return ((" where " + " and ".join(clauses)) if clauses else ""), params


def _spend_where(filters: dict | None):
    filters = filters or {}
    clauses, params = [], []
    dims = dimensions()
    if filters.get("channel") in dims["channels"]:
        clauses.append("c.channel_name = ?"); params.append(filters["channel"])
    if filters.get("month_from"):
        clauses.append("strftime(a.date_day,'%Y-%m') >= ?")
        params.append(filters["month_from"])
    if filters.get("month_to"):
        clauses.append("strftime(a.date_day,'%Y-%m') <= ?")
        params.append(filters["month_to"])
    # city/studio not applicable to channel-level spend (allocated by lead share)
    return ((" where " + " and ".join(clauses)) if clauses else ""), params


def _alloc_spend_by_channel(filters: dict | None) -> dict[str, float]:
    """Ad platforms report spend per channel, not per studio/city. To make
    CAC/ROAS meaningful under a city/studio filter we allocate each channel's
    spend by that scope's share of the channel's leads (in the month window).
    Channel + month filters apply directly; city/studio drive the allocation.
    """
    f = filters or {}
    month = {k: v for k, v in f.items() if k in ("month_from", "month_to")}
    chan = {k: v for k, v in f.items() if k == "channel"}
    sw, sp = _spend_where({**month, **chan})
    spend = {r["channel_name"]: r["spend"] for r in db.rows(f"""
        select c.channel_name, sum(a.spend) spend
        from main_marts.fct_ad_spend a
        join main_marts.dim_channel c on a.channel_key = c.channel_key
        join main_marts.dim_date d on a.date_day = d.date_day
        {sw} group by 1""", sp)}
    w, p = _where(f)
    scope = {r["channel_name"]: r["leads"] for r in db.rows(f"""{_FUNNEL_BASE}
        select channel_name, sum(leads) leads from f {w} group by 1""", p)}
    gw, gp = _where({**month, **chan})
    glob = {r["channel_name"]: r["leads"] for r in db.rows(f"""{_FUNNEL_BASE}
        select channel_name, sum(leads) leads from f {gw} group by 1""", gp)}
    out = {}
    for ch, sp_v in spend.items():
        g, s = glob.get(ch, 0), scope.get(ch, 0)
        out[ch] = round(sp_v * (s / g)) if g else 0
    return out


def _scope_spend(filters: dict | None) -> float:
    return float(sum(_alloc_spend_by_channel(filters).values()))
