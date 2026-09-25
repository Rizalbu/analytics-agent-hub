"""Analytics Agent Hub — single-file FastAPI app.

Combines two architectural ideas (original implementation, no code copied):
  1. Deterministic-first multi-agent coordinator: a question is scored against
     a small agent roster by keyword match; the winning agent for data
     questions answers from real DuckDB numbers first, optional LLM only
     polishes the wording ("no naked numbers").
  2. Multi-tenant + channel adapters: each org has its own API key and data
     slice; a generic webhook endpoint (Telegram-shaped payload) lets any
     chat channel talk to the coordinator without touching the dashboard.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

import duckdb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "data/hub.duckdb"

# ---- tenancy --------------------------------------------------------------

@dataclass
class Org:
    id: str
    name: str
    api_key: str


ORGS: dict[str, Org] = {}
ORGS_BY_KEY: dict[str, Org] = {}


def create_org(name: str) -> Org:
    org = Org(id=uuid.uuid4().hex[:8], name=name, api_key=uuid.uuid4().hex)
    ORGS[org.id] = org
    ORGS_BY_KEY[org.api_key] = org
    return org


def org_from_key(api_key: str) -> Org:
    org = ORGS_BY_KEY.get(api_key)
    if not org:
        raise HTTPException(401, "invalid org api key")
    return org


# ---- agent roster + deterministic router -----------------------------------

@dataclass
class Agent:
    id: str
    role: str
    keywords: list[str]


ROSTER: list[Agent] = [
    Agent("da", "Data Analyst", ["revenue", "lead", "conversion", "kpi", "metric", "channel"]),
    Agent("gm", "Growth Manager", ["funnel", "retention", "experiment", "cac", "growth"]),
    Agent("sup", "Support Agent", ["help", "issue", "problem", "bantuan", "error"]),
    Agent("ops", "Ops Agent", ["schedule", "capacity", "process", "sla"]),
]
BY_ID = {a.id: a for a in ROSTER}


def route(org: Org, question: str) -> dict:
    q = question.lower()
    scored = sorted(
        ((a, sum(kw in q for kw in a.keywords)) for a in ROSTER),
        key=lambda t: -t[1],
    )
    agent = scored[0][0] if scored[0][1] > 0 else BY_ID["da"]

    if agent.id == "da":
        data = kpis(org.id)
        text = (
            f"[{agent.role}] leads={data['leads']}, revenue=${data['revenue']:.0f}, "
            f"conversion={data['conversion']:.1%}"
        )
    else:
        text = f"[{agent.role}] noted — routing '{question}' to {agent.role} playbook."

    return {"agent": agent.id, "role": agent.role, "text": text}


# ---- data layer (DuckDB, synthetic, per-org) --------------------------------

def _conn():
    return duckdb.connect(DB_PATH)


def ensure_schema():
    con = _conn()
    con.execute(
        "CREATE TABLE IF NOT EXISTS leads "
        "(org_id VARCHAR, channel VARCHAR, stage VARCHAR, revenue DOUBLE)"
    )
    con.close()


def seed_org(org_id: str, n: int = 200):
    con = _conn()
    channels = ["ads", "organic", "referral"]
    stages = ["lead", "trial", "customer"]
    rows = [
        (org_id, random.choice(channels), random.choice(stages), round(random.uniform(0, 500), 2))
        for _ in range(n)
    ]
    con.executemany("INSERT INTO leads VALUES (?, ?, ?, ?)", rows)
    con.close()


def kpis(org_id: str) -> dict:
    con = _conn()
    leads, customers, revenue = con.execute(
        "SELECT count(*), sum(stage='customer'), coalesce(sum(revenue), 0) "
        "FROM leads WHERE org_id = ?",
        [org_id],
    ).fetchone()
    con.close()
    leads = leads or 0
    customers = customers or 0
    return {
        "leads": leads,
        "customers": customers,
        "revenue": revenue or 0.0,
        "conversion": (customers / leads) if leads else 0.0,
    }


# ---- channel adapter: Telegram-shaped webhook -------------------------------

def parse_telegram_update(payload: dict) -> str | None:
    msg = payload.get("message") or {}
    text = msg.get("text")
    return text.strip() if isinstance(text, str) else None


# ---- FastAPI ----------------------------------------------------------------

app = FastAPI(title="Analytics Agent Hub")


@app.on_event("startup")
def _startup():
    ensure_schema()


class OrgBody(BaseModel):
    name: str


class AskBody(BaseModel):
    question: str


@app.post("/api/orgs")
def api_create_org(body: OrgBody):
    org = create_org(body.name)
    seed_org(org.id)
    return {"id": org.id, "name": org.name, "api_key": org.api_key}


@app.get("/api/agents")
def api_agents():
    return {"agents": [{"id": a.id, "role": a.role} for a in ROSTER]}


@app.post("/api/ask")
def api_ask(body: AskBody, x_org_key: str):
    org = org_from_key(x_org_key)
    return route(org, body.question)


@app.get("/api/kpis")
def api_kpis(x_org_key: str):
    org = org_from_key(x_org_key)
    return kpis(org.id)


@app.post("/webhooks/telegram/{api_key}")
def webhook_telegram(api_key: str, payload: dict):
    org = org_from_key(api_key)
    text = parse_telegram_update(payload)
    if not text:
        return {"ok": True}
    answer = route(org, text)
    chat_id = (payload.get("message") or {}).get("chat", {}).get("id")
    return {"ok": True, "chat_id": chat_id, "reply": answer["text"]}
