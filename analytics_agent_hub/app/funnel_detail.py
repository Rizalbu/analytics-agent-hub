"""Synthetic expanded funnel with multi-source acquisition-flow complexity.

Extends the warehouse's 5-stage funnel (lead->qualified->booked->visited->purchased)
with realistic upstream (impression, click) and downstream (retained, churned)
stages plus nurture/evaluate mid-funnel, broken out by 11 acquisition sources across 6 channel groups.

All numbers are synthetic — generated from the warehouse aggregate as a seed value
and then distributed across sources using realistic conversion-curve parameters.
"""
from __future__ import annotations

import random
from typing import Any

from . import queries
from .config import settings

# ---- Funnel architecture -------------------------------------------------

STAGES = [
    "impression", "click", "lead", "nurtured", "evaluated",
    "qualified", "booked", "visited", "purchased", "retained",
]

STAGE_LABELS = {
    "impression": "Impression", "click": "Click", "lead": "Lead",
    "nurtured": "Nurtured", "evaluated": "Evaluated",
    "qualified": "Qualified", "booked": "Booked", "visited": "Visited",
    "purchased": "Purchased", "retained": "Retained (90d)",
}

STAGE_DESC = {
    "impression": "Ad/content served or viewed",
    "click": "Clicked through to landing page",
    "lead": "Submitted a form / sign-up",
    "nurtured": "Engaged via email, SMS, or retargeting",
    "evaluated": "Compared pricing, attended info session",
    "qualified": "Met fitness-assessment criteria",
    "booked": "Booked a trial session",
    "visited": "Attended trial session",
    "purchased": "Signed a membership",
    "retained": "Still active after 90 days",
}

# ---- 11 acquisition sources with realistic parameters --------------------
# Each source: base_share (lead share), and conversion-curve multipliers
# per stage. Higher = better survival to that stage.

SOURCES = [
    # Social platforms
    {"id": "ig",   "name": "Instagram",     "group": "Social",     "group_id": "social",
     "base_share": 0.22, "impression_rate": 1.0, "click_rate": 0.19, "lead_rate": 0.11,
     "nurtured_rate": 0.55, "evaluated_rate": 0.40, "qualified_rate": 0.72,
     "booked_rate": 0.60, "visited_rate": 0.78, "purchased_rate": 0.65, "retained_rate": 0.72,
     "color": "#e1306c", "icon": "ig", "desc": "Visual campaigns, stories & reels"},

    {"id": "fb",   "name": "Facebook",      "group": "Social",     "group_id": "social",
     "base_share": 0.15, "impression_rate": 1.0, "click_rate": 0.14, "lead_rate": 0.09,
     "nurtured_rate": 0.50, "evaluated_rate": 0.38, "qualified_rate": 0.68,
     "booked_rate": 0.55, "visited_rate": 0.72, "purchased_rate": 0.58, "retained_rate": 0.68,
     "color": "#1877f2", "icon": "fb", "desc": "Paid social, retargeting & lookalikes"},

    {"id": "tt",   "name": "TikTok",        "group": "Social",     "group_id": "social",
     "base_share": 0.08, "impression_rate": 1.0, "click_rate": 0.22, "lead_rate": 0.07,
     "nurtured_rate": 0.38, "evaluated_rate": 0.30, "qualified_rate": 0.55,
     "booked_rate": 0.45, "visited_rate": 0.60, "purchased_rate": 0.48, "retained_rate": 0.58,
     "color": "#ff0050", "icon": "tt", "desc": "Viral challenges & influencer UGC"},

    # Search
    {"id": "ga",   "name": "Google Ads",    "group": "Search",     "group_id": "search",
     "base_share": 0.14, "impression_rate": 1.0, "click_rate": 0.32, "lead_rate": 0.18,
     "nurtured_rate": 0.60, "evaluated_rate": 0.50, "qualified_rate": 0.78,
     "booked_rate": 0.68, "visited_rate": 0.82, "purchased_rate": 0.72, "retained_rate": 0.78,
     "color": "#4285f4", "icon": "ga", "desc": "Brand + non-brand SEM, DSA & PMax"},

    {"id": "ba",   "name": "Bing Ads",      "group": "Search",     "group_id": "search",
     "base_share": 0.03, "impression_rate": 1.0, "click_rate": 0.28, "lead_rate": 0.15,
     "nurtured_rate": 0.55, "evaluated_rate": 0.45, "qualified_rate": 0.74,
     "booked_rate": 0.62, "visited_rate": 0.78, "purchased_rate": 0.66, "retained_rate": 0.74,
     "color": "#008373", "icon": "ba", "desc": "Bing audience network"},

    # Referral
    {"id": "mr",   "name": "Member Referral","group": "Referral",  "group_id": "referral",
     "base_share": 0.06, "impression_rate": 1.0, "click_rate": 0.45, "lead_rate": 0.35,
     "nurtured_rate": 0.78, "evaluated_rate": 0.70, "qualified_rate": 0.92,
     "booked_rate": 0.88, "visited_rate": 0.94, "purchased_rate": 0.88, "retained_rate": 0.92,
     "color": "#4ec9b0", "icon": "mr", "desc": "Member-get-member & referral rewards"},

    {"id": "pr",   "name": "Partner Referral","group": "Referral", "group_id": "referral",
     "base_share": 0.03, "impression_rate": 1.0, "click_rate": 0.38, "lead_rate": 0.28,
     "nurtured_rate": 0.72, "evaluated_rate": 0.65, "qualified_rate": 0.88,
     "booked_rate": 0.82, "visited_rate": 0.90, "purchased_rate": 0.82, "retained_rate": 0.88,
     "color": "#c586c0", "icon": "pr", "desc": "Corporate wellness & hotel partnerships"},

    # Email
    {"id": "nl",   "name": "Newsletter",    "group": "Email",      "group_id": "email",
     "base_share": 0.04, "impression_rate": 1.0, "click_rate": 0.24, "lead_rate": 0.12,
     "nurtured_rate": 0.82, "evaluated_rate": 0.55, "qualified_rate": 0.70,
     "booked_rate": 0.58, "visited_rate": 0.74, "purchased_rate": 0.62, "retained_rate": 0.72,
     "color": "#dcdcaa", "icon": "nl", "desc": "Weekly newsletter & nurture sequences"},

    {"id": "dc",   "name": "Drip Campaign", "group": "Email",      "group_id": "email",
     "base_share": 0.03, "impression_rate": 1.0, "click_rate": 0.20, "lead_rate": 0.14,
     "nurtured_rate": 0.85, "evaluated_rate": 0.62, "qualified_rate": 0.76,
     "booked_rate": 0.65, "visited_rate": 0.80, "purchased_rate": 0.70, "retained_rate": 0.78,
     "color": "#4ec9b0", "icon": "dc", "desc": "Automated email sequences based on behaviour"},

    # Events & Direct
    {"id": "ev",   "name": "Events",        "group": "Events",     "group_id": "events",
     "base_share": 0.05, "impression_rate": 1.0, "click_rate": 0.35, "lead_rate": 0.30,
     "nurtured_rate": 0.70, "evaluated_rate": 0.72, "qualified_rate": 0.88,
     "booked_rate": 0.82, "visited_rate": 0.92, "purchased_rate": 0.85, "retained_rate": 0.90,
     "color": "#ce9178", "icon": "ev", "desc": "Pop-up trials, expo booths & webinars"},

    {"id": "di",   "name": "Direct",        "group": "Direct",     "group_id": "direct",
     "base_share": 0.17, "impression_rate": 1.0, "click_rate": 0.55, "lead_rate": 0.40,
     "nurtured_rate": 0.85, "evaluated_rate": 0.78, "qualified_rate": 0.95,
     "booked_rate": 0.92, "visited_rate": 0.96, "purchased_rate": 0.92, "retained_rate": 0.94,
     "color": "#4da6ff", "icon": "di", "desc": "Walk-in, website direct & organic search"},
]

SOURCE_BY_ID = {s["id"]: s for s in SOURCES}


# ---- Generators ----------------------------------------------------------

def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate_funnel(filters: dict | None = None) -> dict:
    """Generate a detailed multi-source funnel based on warehouse aggregates.

    Uses the real `leads` count from the warehouse as the anchor, then
    distributes upstream (impressions/clicks) and downstream stages using
    the per-source conversion-curve parameters.
    """
    rng = _rng(42)
    base = queries.kpis(filters)
    total_leads = base.get("leads") or 15000

    # Distribute leads across sources
    for s in SOURCES:
        s["leads"] = max(1, int(total_leads * s["base_share"] * rng.uniform(0.85, 1.15)))

    # Normalize to match total_leads exactly
    lead_sum = sum(s["leads"] for s in SOURCES)
    for s in SOURCES:
        s["leads"] = max(1, int(s["leads"] * total_leads / lead_sum))

    # Re-normalize
    lead_sum = sum(s["leads"] for s in SOURCES)
    diff = total_leads - lead_sum
    if diff:
        SOURCES[0]["leads"] = max(1, SOURCES[0]["leads"] + diff)

    # Build stage data per source
    source_data = []
    total_by_stage = {s: 0 for s in STAGES}

    for s in SOURCES:
        leads = s["leads"]
        row = {"source_id": s["id"], "source_name": s["name"], "group": s["group"],
               "group_id": s["group_id"], "color": s["color"], "leads": leads}

        # Upstream: impressions -> clicks
        impressions = int(leads / (s["lead_rate"] * s["click_rate"]))
        clicks = int(impressions * s["click_rate"] * rng.uniform(0.92, 1.08))
        row["impressions"] = max(impressions, clicks + 100)
        row["clicks"] = max(clicks, leads + 10)

        # Downstream: cascade through stages
        cascade = {"lead": leads}
        stage_keys = ["nurtured", "evaluated", "qualified", "booked", "visited", "purchased", "retained"]
        for sk in stage_keys:
            rate_key = f"{sk}_rate"
            prev_key = "lead" if sk == "nurtured" else stage_keys[stage_keys.index(sk) - 1]
            prev_val = cascade[prev_key]
            val = int(prev_val * s[rate_key] * rng.uniform(0.94, 1.06))
            cascade[sk] = max(0, val)
        row.update(cascade)
        row["churned"] = cascade["purchased"] - cascade["retained"]

        # Spend: synthetic but realistic
        spend_per_lead = {"social": 18000, "search": 25000, "referral": 3000,
                          "email": 5000, "events": 45000, "direct": 2000}
        row["spend"] = int(leads * spend_per_lead.get(s["group_id"], 15000) * rng.uniform(0.85, 1.15))
        row["revenue"] = int(cascade["purchased"] * 320000 * rng.uniform(0.92, 1.08))

        source_data.append(row)

        # Accumulate totals
        for stage in STAGES:
            if stage == "click":
                total_by_stage["click"] += row["clicks"]
            elif stage == "impression":
                total_by_stage["impression"] += row["impressions"]
            else:
                if stage in row:
                    total_by_stage[stage] += row[stage]

    # Stage-to-stage conversion rates
    steps = []
    stage_keys = [s for s in STAGES if s != "retained"]  # all except retained
    for i in range(1, len(stage_keys)):
        frm, to = stage_keys[i - 1], stage_keys[i]
        frm_key = "clicks" if frm == "click" else frm
        to_key = "clicks" if to == "click" else to
        pv, cv = total_by_stage.get(frm_key, 0), total_by_stage.get(to_key, 0)
        steps.append({
            "from": STAGE_LABELS.get(frm, frm),
            "to": STAGE_LABELS.get(to, to),
            "from_key": frm, "to_key": to,
            "rate": round(cv / pv * 100, 2) if pv else 0,
            "volume_in": int(pv), "volume_out": int(cv),
            "drop": int(max(0, pv - cv)),
        })

    # Retention step
    purchased = total_by_stage.get("purchased", 0)
    retained = total_by_stage.get("retained", 0)
    steps.append({
        "from": STAGE_LABELS["purchased"], "to": STAGE_LABELS["retained"],
        "from_key": "purchased", "to_key": "retained",
        "rate": round(retained / purchased * 100, 2) if purchased else 0,
        "volume_in": int(purchased), "volume_out": int(retained),
        "drop": int(max(0, purchased - retained)),
    })

    # Cost metrics per source
    for s in source_data:
        s["cpl"] = round(s["spend"] / s["leads"]) if s["leads"] else 0
        s["cac"] = round(s["spend"] / s["purchased"]) if s["purchased"] else 0
        s["roas"] = round(s["revenue"] / s["spend"], 2) if s["spend"] else 0
        s["cvr"] = round(s["purchased"] / s["leads"] * 100, 2) if s["leads"] else 0

    return {
        "stages": STAGES,
        "stage_labels": STAGE_LABELS,
        "stage_desc": STAGE_DESC,
        "totals": {k: int(v) for k, v in total_by_stage.items()},
        "steps": steps,
        "sources": source_data,
        "groups": list(dict.fromkeys(s["group"] for s in SOURCES)),
        "summary": {
            "total_impressions": int(total_by_stage.get("impression", 0)),
            "total_clicks": int(total_by_stage.get("click", 0)),
            "total_leads": int(total_by_stage.get("lead", 0)),
            "total_purchased": int(total_by_stage.get("purchased", 0)),
            "total_retained": int(total_by_stage.get("retained", 0)),
            "total_spend": int(sum(s["spend"] for s in source_data)),
            "total_revenue": int(sum(s["revenue"] for s in source_data)),
            "blended_cac": round(sum(s["spend"] for s in source_data) / max(1, total_by_stage.get("purchased", 0))),
            "blended_roas": round(sum(s["revenue"] for s in source_data) / max(1, sum(s["spend"] for s in source_data)), 2),
        },
    }


def generate_data_sources() -> list[dict]:
    """Return a catalog of data sources that feed the funnel warehouse.

    Used by the lineage / Data Sources page.
    """
    return [
        {"name": "Google Ads API", "kind": "Paid Search", "table": "raw.adwords_performance",
         "stages": ["impression", "click", "lead"], "freshness": "hourly",
         "records": "12.4M impressions/mo", "status": "active"},
        {"name": "Meta (Facebook/IG) API", "kind": "Paid Social", "table": "raw.meta_insights",
         "stages": ["impression", "click", "lead"], "freshness": "hourly",
         "records": "8.7M impressions/mo", "status": "active"},
        {"name": "TikTok Ads API", "kind": "Paid Social", "table": "raw.tiktok_performance",
         "stages": ["impression", "click", "lead"], "freshness": "hourly",
         "records": "3.1M impressions/mo", "status": "active"},
        {"name": "Bing Ads API", "kind": "Paid Search", "table": "raw.bing_performance",
         "stages": ["impression", "click", "lead"], "freshness": "daily",
         "records": "1.2M impressions/mo", "status": "active"},
        {"name": "HubSpot CRM", "kind": "CRM", "table": "raw.hubspot_contacts",
         "stages": ["lead", "nurtured", "evaluated"], "freshness": "real-time",
         "records": "45K contacts", "status": "active"},
        {"name": "Salesforce CRM", "kind": "CRM", "table": "raw.sf_opportunities",
         "stages": ["sql", "qualified", "booked"], "freshness": "real-time",
         "records": "12K opportunities", "status": "active"},
        {"name": "Member Referral System", "kind": "Internal", "table": "raw.referral_tracking",
         "stages": ["lead", "mql", "purchased"], "freshness": "real-time",
         "records": "3.2K referrals/mo", "status": "active"},
        {"name": "Partner Network API", "kind": "Partnership", "table": "raw.partner_leads",
         "stages": ["lead", "qualified", "purchased"], "freshness": "daily",
         "records": "1.8K leads/mo", "status": "active"},
        {"name": "Email Platform (SendGrid)", "kind": "Email", "table": "raw.email_engagement",
         "stages": ["impression", "click", "lead"], "freshness": "real-time",
         "records": "2.1M sends/mo", "status": "active"},
        {"name": "Drip Automation (Customer.io)", "kind": "Email", "table": "raw.drip_events",
         "stages": ["click", "lead", "mql"], "freshness": "real-time",
         "records": "890K events/mo", "status": "active"},
        {"name": "Event Management (Eventbrite)", "kind": "Events", "table": "raw.event_registrations",
         "stages": ["impression", "lead", "booked"], "freshness": "daily",
         "records": "450 events/yr", "status": "active"},
        {"name": "Web Analytics (GA4)", "kind": "Analytics", "table": "raw.ga4_sessions",
         "stages": ["impression", "click"], "freshness": "hourly",
         "records": "18.5M sessions/mo", "status": "active"},
        {"name": "POS / Studio System", "kind": "Internal", "table": "raw.pos_transactions",
         "stages": ["visited", "purchased", "retained"], "freshness": "real-time",
         "records": "22K transactions/mo", "status": "active"},
        {"name": "Retention & Churn Tracker", "kind": "Internal", "table": "raw.member_retention",
         "stages": ["retained", "churned"], "freshness": "daily",
         "records": "15K active members", "status": "active"},
    ]
