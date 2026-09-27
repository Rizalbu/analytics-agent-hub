"""AI Agent roster for the Agents Hub.

Each agent is a role with expertise, a persona, synthetic workload/metrics, and
a system-prompt persona used when the user chats with it (the persona is
prepended to the LLM tier; the deterministic engine still supplies real
numbers, so a Data Analyst answer is grounded, not hallucinated).
"""
from __future__ import annotations

# category -> agents. metrics are synthetic demo values.
ROSTER = [
    # System: Orchestrator (always first)
    {"id": "orch", "role": "Orchestrator", "cat": "System", "init": "OC",
     "expertise": "multi-agent routing, cross-domain synthesis, fan-out coordination",
     "persona": "a central coordinator who routes requests to the right agents and synthesises their output into a unified answer",
     "status": "active", "workload": 0, "tasks": 0, "deliverables": 0, "rating": 5.0,
     "skills": ["Routing", "Synthesis", "Fan-out", "Cross-domain", "Orchestration"]},
    # Product & strategy
    {"id": "pm", "role": "Product Manager", "cat": "Product", "init": "PM",
     "expertise": "PRDs, roadmaps, prioritization, success metrics",
     "persona": "a decisive product manager who frames problems, defines success metrics, and writes crisp PRDs",
     "status": "active", "workload": 72, "tasks": 5, "deliverables": 14, "rating": 4.8,
     "skills": ["PRD", "Roadmap", "Prioritization", "User stories", "OKRs"]},
    {"id": "proj", "role": "Project Manager", "cat": "Product", "init": "PJ",
     "expertise": "timelines, dependencies, risk, delivery",
     "persona": "a pragmatic project manager focused on timelines, dependencies and unblocking the team",
     "status": "active", "workload": 58, "tasks": 8, "deliverables": 9, "rating": 4.7,
     "skills": ["Planning", "Risk", "Dependencies", "Standups", "Reporting"]},
    {"id": "ba", "role": "Business Analyst", "cat": "Product", "init": "BA",
     "expertise": "requirements, process mapping, BRDs",
     "persona": "a thorough business analyst who turns vague asks into clear requirements",
     "status": "idle", "workload": 33, "tasks": 3, "deliverables": 7, "rating": 4.6,
     "skills": ["Requirements", "Process maps", "BRD", "Gap analysis"]},
    # Data
    {"id": "da", "role": "Data Analyst", "cat": "Data", "init": "DA",
     "expertise": "SQL, dashboards, KPI definitions, insight",
     "persona": "a sharp data analyst who answers with real numbers, SQL and clear takeaways",
     "status": "active", "workload": 81, "tasks": 6, "deliverables": 21, "rating": 4.9,
     "skills": ["SQL", "Dashboards", "KPIs", "Cohorts", "A/B tests"]},
    {"id": "de", "role": "Data Engineer", "cat": "Data", "init": "DE",
     "expertise": "pipelines, warehousing, dbt, orchestration",
     "persona": "a reliability-minded data engineer who builds idempotent pipelines and tested models",
     "status": "active", "workload": 64, "tasks": 4, "deliverables": 12, "rating": 4.8,
     "skills": ["dbt", "Airflow", "Warehousing", "Data contracts", "DuckDB"]},
    {"id": "ae", "role": "Analytics Engineer", "cat": "Data", "init": "AE",
     "expertise": "semantic layer, metrics, dimensional modeling",
     "persona": "an analytics engineer who models clean, tested marts and a trustworthy semantic layer",
     "status": "idle", "workload": 41, "tasks": 3, "deliverables": 10, "rating": 4.7,
     "skills": ["Dimensional model", "Semantic layer", "Tests", "Lineage"]},
    {"id": "ml", "role": "ML Engineer", "cat": "Data", "init": "ML",
     "expertise": "features, training, evaluation, serving",
     "persona": "an ML engineer who builds honest models with proper evaluation and calibration",
     "status": "busy", "workload": 88, "tasks": 7, "deliverables": 8, "rating": 4.8,
     "skills": ["Feature eng", "LightGBM", "Evaluation", "Drift", "Serving"]},
    # Engineering
    {"id": "fs", "role": "Full Stack Developer", "cat": "Engineering", "init": "FS",
     "expertise": "end-to-end features, API + UI, deploy",
     "persona": "a full-stack developer who ships clean end-to-end features with tests",
     "status": "active", "workload": 76, "tasks": 6, "deliverables": 18, "rating": 4.8,
     "skills": ["FastAPI", "React", "APIs", "Docker", "CI/CD"]},
    {"id": "fe", "role": "Frontend Developer", "cat": "Engineering", "init": "FE",
     "expertise": "UI, state, performance, accessibility",
     "persona": "a frontend developer focused on polished, accessible, performant interfaces",
     "status": "idle", "workload": 47, "tasks": 4, "deliverables": 15, "rating": 4.7,
     "skills": ["TypeScript", "State", "A11y", "Animations", "Perf"]},
    {"id": "be", "role": "Backend Developer", "cat": "Engineering", "init": "BE",
     "expertise": "services, data access, scaling, security",
     "persona": "a backend developer who writes secure, well-tested services",
     "status": "active", "workload": 69, "tasks": 5, "deliverables": 13, "rating": 4.8,
     "skills": ["APIs", "DB", "Auth", "Caching", "Security"]},
    {"id": "qa", "role": "QA Engineer", "cat": "Engineering", "init": "QA",
     "expertise": "test plans, automation, regression",
     "persona": "a meticulous QA engineer who hunts edge cases and writes automated tests",
     "status": "idle", "workload": 38, "tasks": 3, "deliverables": 11, "rating": 4.6,
     "skills": ["Test plans", "Playwright", "Regression", "Edge cases"]},
    # Design
    {"id": "uxr", "role": "UX Researcher", "cat": "Design", "init": "UR",
     "expertise": "interviews, usability, synthesis",
     "persona": "a UX researcher who grounds decisions in evidence and user insight",
     "status": "idle", "workload": 29, "tasks": 2, "deliverables": 6, "rating": 4.7,
     "skills": ["Interviews", "Usability", "Synthesis", "Personas"]},
    {"id": "uxd", "role": "UX Designer", "cat": "Design", "init": "UX",
     "expertise": "flows, wireframes, interaction",
     "persona": "a UX designer who crafts intuitive flows and low-friction interactions",
     "status": "active", "workload": 55, "tasks": 4, "deliverables": 16, "rating": 4.8,
     "skills": ["Flows", "Wireframes", "IA", "Prototypes"]},
    {"id": "uid", "role": "UI Designer", "cat": "Design", "init": "UI",
     "expertise": "visual design, design systems, polish",
     "persona": "a UI designer obsessed with visual craft, systems and polish",
     "status": "active", "workload": 61, "tasks": 5, "deliverables": 19, "rating": 4.9,
     "skills": ["Design system", "Visual", "Tokens", "Motion"]},
    # Growth & ops
    {"id": "gm", "role": "Growth Manager", "cat": "Growth", "init": "GM",
     "expertise": "funnels, experiments, retention",
     "persona": "a growth manager who runs experiments and optimizes the funnel end-to-end",
     "status": "active", "workload": 67, "tasks": 6, "deliverables": 13, "rating": 4.8,
     "skills": ["Funnels", "Experiments", "Retention", "CAC/LTV"]},
    {"id": "mkt", "role": "Marketing Strategist", "cat": "Growth", "init": "MK",
     "expertise": "positioning, GTM, channels",
     "persona": "a marketing strategist who sharpens positioning and plans GTM",
     "status": "idle", "workload": 44, "tasks": 3, "deliverables": 9, "rating": 4.6,
     "skills": ["Positioning", "GTM", "Channels", "Messaging"]},
    {"id": "cont", "role": "Content Strategist", "cat": "Growth", "init": "CS",
     "expertise": "content plans, narrative, SEO",
     "persona": "a content strategist who builds narrative and content engines",
     "status": "idle", "workload": 36, "tasks": 2, "deliverables": 12, "rating": 4.7,
     "skills": ["Content plan", "Narrative", "SEO", "Editorial"]},
    {"id": "ops", "role": "Operations Manager", "cat": "Growth", "init": "OP",
     "expertise": "process, capacity, SLAs",
     "persona": "an operations manager who streamlines process and protects SLAs",
     "status": "active", "workload": 52, "tasks": 4, "deliverables": 8, "rating": 4.7,
     "skills": ["Process", "Capacity", "SLAs", "Forecasting"]},
    {"id": "csm", "role": "Customer Success", "cat": "Growth", "init": "CS",
     "expertise": "onboarding, health, retention",
     "persona": "a customer success lead focused on onboarding, account health and retention",
     "status": "idle", "workload": 40, "tasks": 3, "deliverables": 7, "rating": 4.6,
     "skills": ["Onboarding", "Health scores", "Retention", "QBRs"]},
]

BY_ID = {a["id"]: a for a in ROSTER}


def roster() -> dict:
    cats: dict = {}
    for a in ROSTER:
        cats.setdefault(a["cat"], 0)
        cats[a["cat"]] += 1
    active = sum(1 for a in ROSTER if a["status"] in ("active", "busy"))
    avg_load = round(sum(a["workload"] for a in ROSTER) / len(ROSTER))
    return {"agents": ROSTER, "categories": list(cats),
            "summary": {"total": len(ROSTER), "active": active,
                        "avg_workload": avg_load,
                        "deliverables": sum(a["deliverables"] for a in ROSTER)}}


def persona(agent_id: str) -> str | None:
    a = BY_ID.get(agent_id)
    return a["persona"] if a else None


# ---- DuckDB Persistence --------------------------------------------------
# All agent state lives in data/agent.duckdb (NOT the read-only warehouse).
# Survives server restarts, production-grade.
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Any
import json
from pathlib import Path
import threading
import duckdb

_AGENT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "agent.duckdb"
_agent_lock = threading.Lock()
_agent_db_con: duckdb.DuckDBPyConnection | None = None


def _agent_db() -> duckdb.DuckDBPyConnection:
    global _agent_db_con
    if _agent_db_con is None:
        _AGENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _agent_db_con = duckdb.connect(str(_AGENT_DB_PATH))
        _init_db()
        _seed()
    return _agent_db_con


def _init_db():
    con = _agent_db_con
    con.execute("CREATE TABLE IF NOT EXISTS projects (id VARCHAR PRIMARY KEY, name VARCHAR, goal VARCHAR, status VARCHAR, agents_json VARCHAR, created VARCHAR)")
    con.execute("CREATE TABLE IF NOT EXISTS tasks (id VARCHAR PRIMARY KEY, agent VARCHAR, title VARCHAR, description VARCHAR, status VARCHAR, priority VARCHAR, project VARCHAR, created VARCHAR, updated VARCHAR)")
    con.execute("CREATE TABLE IF NOT EXISTS deliverables (id VARCHAR PRIMARY KEY, title VARCHAR, type VARCHAR, agent VARCHAR, status VARCHAR, project VARCHAR, created VARCHAR)")
    con.execute("CREATE TABLE IF NOT EXISTS reviews (id VARCHAR PRIMARY KEY, title VARCHAR, item VARCHAR, requested_by VARCHAR, assigned_to VARCHAR, status VARCHAR, priority VARCHAR, comment VARCHAR, updated VARCHAR)")
    con.execute("CREATE TABLE IF NOT EXISTS collaborations (id VARCHAR PRIMARY KEY, lead VARCHAR, peer VARCHAR, goal VARCHAR, status VARCHAR, created VARCHAR)")
    con.execute("CREATE TABLE IF NOT EXISTS activity_log (id VARCHAR PRIMARY KEY, kind VARCHAR, message VARCHAR, agent VARCHAR, ts VARCHAR)")


# ---- Seed data ------------------------------------------------------------

SEED_PROJECTS = [
    {"id": "proj-1", "name": "Q4 Funnel Optimization", "goal": "Improve lead→qualified CR by 15%", "status": "active", "agents": ["pm", "da", "gm"], "created": "2025-09-01"},
    {"id": "proj-2", "name": "Data Warehouse Refresh", "goal": "Migrate to dimensional model with dbt tests", "status": "active", "agents": ["de", "ae"], "created": "2025-09-10"},
    {"id": "proj-3", "name": "Studio Dashboard v2", "goal": "Real-time KPIs for all three studios", "status": "active", "agents": ["fe", "fs", "da"], "created": "2025-09-15"},
    {"id": "proj-4", "name": "Member Retention Campaign", "goal": "Identify at-risk members and reduce churn", "status": "planning", "agents": ["mkt", "csm", "ba"], "created": "2025-09-20"},
]
SEED_DELIVERABLES = [
    {"id": "del-1", "title": "Funnel SQL models", "type": "Code", "agent": "de", "status": "done", "project": "proj-2", "created": "2025-09-12"},
    {"id": "del-2", "title": "Conversion rate dashboard", "type": "Dashboard", "agent": "da", "status": "review", "project": "proj-1", "created": "2025-09-18"},
    {"id": "del-3", "title": "Studio homepage wireframes", "type": "Design", "agent": "uxd", "status": "draft", "project": "proj-3", "created": "2025-09-22"},
]
SEED_REVIEWS = [
    {"id": "rv-1", "title": "Review funnel SQL logic", "item": "Conversion dashboard PR #42", "requested_by": "da", "assigned_to": "ae", "status": "pending", "priority": "high"},
    {"id": "rv-2", "title": "Wireframe critique", "item": "Studio dashboard homepage flows", "requested_by": "uxd", "assigned_to": "uid", "status": "pending", "priority": "medium"},
]


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _log(kind: str, msg: str, agent: str | None = None):
    with _agent_lock:
        _agent_db().execute(
            "INSERT INTO activity_log (id, kind, message, agent, ts) VALUES (?, ?, ?, ?, ?)",
            [f"act-{_uuid.uuid4().hex[:8]}", kind, msg, agent, _ts()])


def _row_to_task(r):
    return {"id": r[0], "agent": r[1], "title": r[2], "description": r[3], "status": r[4], "priority": r[5], "project": r[6], "created": r[7], "updated": r[8]}

def _row_to_project(r):
    return {"id": r[0], "name": r[1], "goal": r[2], "status": r[3], "agents": json.loads(r[4]) if r[4] else [], "created": r[5]}

def _row_to_deliverable(r):
    return {"id": r[0], "title": r[1], "type": r[2], "agent": r[3], "status": r[4], "project": r[5], "created": r[6]}

def _row_to_review(r):
    return {"id": r[0], "title": r[1], "item": r[2], "requested_by": r[3], "assigned_to": r[4], "status": r[5], "priority": r[6], "comment": r[7], "updated": r[8]}

def _row_to_collaboration(r):
    return {"id": r[0], "lead": r[1], "peer": r[2], "goal": r[3], "status": r[4], "created": r[5]}

def _row_to_activity(r):
    return {"id": r[0], "kind": r[1], "message": r[2], "agent": r[3], "ts": r[4]}


# ---- Tasks ---------------------------------------------------------------
def create_task(agent_id: str, title: str, description: str,
                priority: str = "medium", project_id: str | None = None) -> dict:
    t_id = f"task-{_uuid.uuid4().hex[:8]}"
    now = _ts()
    with _agent_lock:
        _agent_db().execute(
            "INSERT INTO tasks (id, agent, title, description, status, priority, project, created, updated) VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)",
            [t_id, agent_id, title, description, priority, project_id, now, now])
    a = BY_ID.get(agent_id, {})
    _log("task", f"Task assigned: {title} → {a.get('role', agent_id)}", agent_id)
    return {"id": t_id, "agent": agent_id, "title": title, "description": description, "status": "open", "priority": priority, "project": project_id, "created": now, "updated": now}


def list_tasks(agent_id: str | None = None, status: str | None = None) -> list[dict]:
    sql, params = "SELECT * FROM tasks WHERE 1=1", []
    if agent_id:
        sql += " AND agent = ?"; params.append(agent_id)
    if status:
        sql += " AND status = ?"; params.append(status)
    sql += " ORDER BY created DESC"
    return [_row_to_task(r) for r in _agent_db().execute(sql, params).fetchall()]


def update_task(task_id: str, status: str) -> dict | None:
    now = _ts()
    with _agent_lock:
        con = _agent_db()
        con.execute("UPDATE tasks SET status = ?, updated = ? WHERE id = ?", [status, now, task_id])
        r = con.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    if r:
        t = _row_to_task(r)
        _log("task", f"Task {t['title']} → {status}", t["agent"])
        return t
    return None


# ---- Projects -----------------------------------------------------------
def list_projects(agent_id: str | None = None) -> list[dict]:
    if agent_id:
        rows = _agent_db().execute("SELECT * FROM projects WHERE agents_json LIKE ? ORDER BY created", [f'%"{agent_id}"%']).fetchall()
    else:
        rows = _agent_db().execute("SELECT * FROM projects ORDER BY created").fetchall()
    return [_row_to_project(r) for r in rows]


def create_project(name: str, goal: str, agent_ids: list[str]) -> dict:
    p_id = f"proj-{_uuid.uuid4().hex[:6]}"
    now = _ts()
    with _agent_lock:
        _agent_db().execute("INSERT INTO projects (id, name, goal, status, agents_json, created) VALUES (?, ?, ?, 'planning', ?, ?)",
                           [p_id, name, goal, json.dumps(agent_ids), now])
    _log("project", f"Project created: {name}")
    return {"id": p_id, "name": name, "goal": goal, "status": "planning", "agents": agent_ids, "created": now}


# ---- Deliverables --------------------------------------------------------
def create_deliverable(title: str, dtype: str, agent_id: str,
                       project_id: str | None = None) -> dict:
    d_id = f"del-{_uuid.uuid4().hex[:8]}"
    now = _ts()
    with _agent_lock:
        _agent_db().execute("INSERT INTO deliverables (id, title, type, agent, status, project, created) VALUES (?, ?, ?, ?, 'draft', ?, ?)",
                           [d_id, title, dtype, agent_id, project_id, now])
    a = BY_ID.get(agent_id, {})
    _log("deliverable", f"Deliverable created: {title} by {a.get('role', agent_id)}", agent_id)
    return {"id": d_id, "title": title, "type": dtype, "agent": agent_id, "status": "draft", "project": project_id, "created": now}


def list_deliverables(agent_id: str | None = None) -> list[dict]:
    sql, params = "SELECT * FROM deliverables", []
    if agent_id:
        sql += " WHERE agent = ?"; params.append(agent_id)
    return [_row_to_deliverable(r) for r in _agent_db().execute(sql, params).fetchall()]


# ---- Reviews -------------------------------------------------------------
def list_reviews(agent_id: str | None = None) -> list[dict]:
    sql, params = "SELECT * FROM reviews", []
    if agent_id:
        sql += " WHERE requested_by = ? OR assigned_to = ?"; params.extend([agent_id, agent_id])
    return [_row_to_review(r) for r in _agent_db().execute(sql, params).fetchall()]


def review_action(review_id: str, action: str, comment: str = "") -> dict | None:
    new_status = "approved" if action == "approve" else "changes"
    now = _ts()
    with _agent_lock:
        con = _agent_db()
        con.execute("UPDATE reviews SET status = ?, comment = ?, updated = ? WHERE id = ?", [new_status, comment, now, review_id])
        r = con.execute("SELECT * FROM reviews WHERE id = ?", [review_id]).fetchone()
    if r:
        _log("review", f"Review {r[1]} → {new_status}")
        return _row_to_review(r)
    return None


# ---- Collaborations ------------------------------------------------------
def start_collaboration(lead_id: str, peer_id: str, goal: str) -> dict:
    c_id = f"collab-{_uuid.uuid4().hex[:8]}"
    now = _ts()
    with _agent_lock:
        _agent_db().execute("INSERT INTO collaborations (id, lead, peer, goal, status, created) VALUES (?, ?, ?, ?, 'active', ?)",
                           [c_id, lead_id, peer_id, goal, now])
    lead = BY_ID.get(lead_id, {})
    peer = BY_ID.get(peer_id, {})
    _log("collaboration", f"Collaboration: {lead.get('role', lead_id)} + {peer.get('role', peer_id)} on {goal}", lead_id)
    return {"id": c_id, "lead": lead_id, "peer": peer_id, "goal": goal, "status": "active", "created": now}


def list_collaborations(agent_id: str | None = None) -> list[dict]:
    sql, params = "SELECT * FROM collaborations", []
    if agent_id:
        sql += " WHERE lead = ? OR peer = ?"; params.extend([agent_id, agent_id])
    return [_row_to_collaboration(r) for r in _agent_db().execute(sql, params).fetchall()]


# ---- Activity feed -------------------------------------------------------
def recent_activity(limit: int = 20) -> list[dict]:
    rows = _agent_db().execute("SELECT * FROM activity_log ORDER BY ts DESC LIMIT ?", [limit]).fetchall()
    return [_row_to_activity(r) for r in rows]


# ---- Agent Tools: real data context per agent ----------------------------

def agent_tool_context(agent_id: str, query: str) -> dict:
    """Gather real data context for a given agent based on the user query.
    
    Returns a dict with:
      - context_text: str, formatted data the agent can reference
      - chart: optional ECharts spec
      - table: optional table
    """
    from . import analyst, insights, queries as qmod
    
    result: dict = {"context_text": "", "chart": None, "table": None}
    
    if agent_id == "da":
        # Data Analyst: full analyst engine
        ans = analyst.answer(query)
        result["context_text"] = ans.get("text", "")
        result["chart"] = ans.get("chart")
        result["table"] = ans.get("table")
        result["provenance"] = ans.get("provenance")
        result["followups"] = ans.get("followups", [])
        return result
    
    if agent_id == "gm":
        # Growth Manager: funnel KPIs + channel mix
        dims = qmod.dimensions()
        kpis = qmod.kpis({})
        ctx_parts = [f"Total revenue this period: Rp {kpis.get('revenue', 0):,.0f}"]
        ctx_parts.append(f"Total leads: {kpis.get('leads', 0):,}")
        ctx_parts.append(f"Overall conversion rate: {kpis.get('cr', 0):.1f}%")
        ctx_parts.append(f"CAC: Rp {kpis.get('cac', 0):,.0f}")
        ctx_parts.append(f"ROAS: {kpis.get('roas', 0):.2f}x")
        ctx_parts.append(f"Active studios: {len(dims.get('studios', []))}")
        ctx_parts.append(f"Available cities: {', '.join(dims.get('cities', []))}")
        result["context_text"] = " | ".join(ctx_parts)
        result["context_data"] = kpis
        return result
    
    if agent_id == "ml":
        # ML Engineer: forecast + anomalies
        forecast = insights.forecast_revenue(3)
        anomalies = insights.scan_anomalies()
        ctx_parts = ["Recent anomalies detected:" if anomalies else "No recent anomalies."]
        for a in anomalies[:3]:
            ctx_parts.append(f"  - {a['metric']} in {a['dimension']}: {a['value']} (expected {a['expected']}, z={a['z']})")
        if forecast.get("forecast"):
            ctx_parts.append(f"Next month forecast: Rp {forecast['forecast'][0].get('value', 0):,.0f}")
            ctx_parts.append(f"MAPE (backtest): {forecast.get('mape', 'N/A')}%")
        result["context_text"] = "\n".join(ctx_parts)
        result["context_data"] = {"forecast": forecast, "anomalies": anomalies[:5]}
        return result
    
    if agent_id in ("pm", "proj"):
        # Product / Project Manager: project + task status
        projects = list_projects()
        tasks = list_tasks()
        ctx_parts = [f"Active projects: {len(projects)}"]
        for p in projects:
            agents_str = ", ".join(BY_ID.get(a, {}).get("role", a) for a in p.get("agents", []))
            ctx_parts.append(f"  - {p['name']} ({p['status']}): {agents_str}")
        ctx_parts.append(f"Open tasks: {sum(1 for t in tasks if t['status'] == 'open')}")
        ctx_parts.append(f"Completed tasks: {sum(1 for t in tasks if t['status'] == 'done')}")
        result["context_text"] = "\n".join(ctx_parts)
        return result
    
    if agent_id in ("de", "ae"):
        # Data / Analytics Engineer: data quality + lineage + registered sources
        from . import quality as ql
        from . import datasources as ds
        qs = ql.build_summary()
        ctx_parts = [f"Data quality score: {qs.get('pass_rate', 0)}%"]
        ctx_parts.append(f"Tests passing: {qs.get('tests_passed', 0)}/{qs.get('tests_total', 0)}")
        ctx_parts.append(f"Models built: {qs.get('models_built', 0)}")
        sources = ds.list_sources()
        if sources:
            names = ", ".join(f"{s['name']} ({s['row_count']} rows)" for s in sources)
            ctx_parts.append(f"Custom data sources registered: {names}")
        else:
            ctx_parts.append("No custom data sources registered yet.")
        result["context_text"] = " | ".join(ctx_parts)
        return result
    
    if agent_id == "fs":
        # Full Stack: app health
        ctx_parts = [
            "Backend: FastAPI with DuckDB warehouse",
            "Frontend: Vanilla JS SPA with ECharts",
            "Auth: Bearer token",
            "Deployment: Local / Docker",
        ]
        result["context_text"] = " | ".join(ctx_parts)
        return result
    
    if agent_id == "csm":
        # Customer Success: member metrics
        dims = qmod.dimensions()
        ctx_parts = [f"Cities served: {len(dims.get('cities', []))}"]
        ctx_parts.append(f"Studios: {len(dims.get('studios', []))}")
        ctx_parts.append("Focus areas: onboarding, health scores, retention, QBRs")
        result["context_text"] = " | ".join(ctx_parts)
        return result
    if agent_id == "orch":
        # Orchestrator: team overview + active projects
        con = _agent_db()
        projects = con.execute("SELECT name, status FROM projects ORDER BY status, name").fetchall()
        active_projs = [p[0] for p in projects if p[1] == "active"]
        total_agents = len(BY_ID) - 1  # exclude self
        active_agents = sum(1 for a in BY_ID.values() if a["id"] != "orch" and a["status"] in ("active", "busy"))
        ctx_parts = [f"Team of {total_agents} agents ({active_agents} active now)"]
        ctx_parts.append(f"Active projects: {len(active_projs)}")
        if active_projs:
            ctx_parts.append(f"Projects: {', '.join(active_projs)}")
        ctx_parts.append("Can route to any agent for cross-domain synthesis")
        result["context_text"] = " | ".join(ctx_parts)
        return result
    
    # Generic fallback: agent's own expertise description
    a = BY_ID.get(agent_id, {})
    result["context_text"] = f"{a.get('role', agent_id)} specialising in {a.get('expertise', '')}."
    return result


# ---- Seed demo data (only on first run) ----------------------------------
def _seed():
    con = _agent_db_con
    existing = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if existing > 0:
        return
    with _agent_lock:
        for p in SEED_PROJECTS:
            con.execute("INSERT INTO projects (id, name, goal, status, agents_json, created) VALUES (?, ?, ?, ?, ?, ?)",
                       [p["id"], p["name"], p["goal"], p["status"], json.dumps(p["agents"]), p["created"]])
        for d in SEED_DELIVERABLES:
            con.execute("INSERT INTO deliverables (id, title, type, agent, status, project, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       [d["id"], d["title"], d["type"], d["agent"], d["status"], d["project"], d["created"]])
        for r in SEED_REVIEWS:
            con.execute("INSERT INTO reviews (id, title, item, requested_by, assigned_to, status, priority, comment, updated) VALUES (?, ?, ?, ?, ?, ?, ?, '', '')",
                       [r["id"], r["title"], r["item"], r["requested_by"], r["assigned_to"], r["status"], r["priority"]])
    import random
    rng = random.Random(42)
    task_templates = [
        ("Analyze Q3 funnel drop-off", "Deep-dive into the lead→qualified conversion dip across all channels", "da"),
        ("Build dbt staging models", "Create staging models for sheets data with tests", "de"),
        ("Design checkout flow", "Design a seamless mobile checkout flow for the member portal", "uxd"),
        ("Optimize Google Search bids", "Adjust bid strategy based on ROAS trend", "gm"),
        ("Implement dark mode", "Add dark mode support to the dashboard UI", "fe"),
        ("Write API integration tests", "Cover all critical revenue endpoints with Playwright", "qa"),
        ("Prepare Q4 PRD draft", "Draft the Product Requirement Doc for next quarter", "pm"),
        ("Set up anomaly alerting", "Configure z-score drift detection on key KPIs", "ae"),
    ]
    for title, desc, agent in task_templates:
        prio = rng.choice(["low", "medium", "high"])
        create_task(agent, title, desc, prio)

    # Seed activity log entries for the timeline
    from datetime import timedelta
    base_ts = datetime.utcnow()
    activity_seeds = [
        ("project", "Project started: Q4 Funnel Optimization", "pm", -120),
        ("task", "Research funnel drop-off patterns", "da", -116),
        ("deliverable", "Funnel SQL models completed", "de", -96),
        ("review", "Review requested: Funnel SQL logic by DA → AE", "da", -72),
        ("project", "Project started: Studio Dashboard v2", "fs", -60),
        ("deliverable", "Conversion rate dashboard submitted for review", "da", -48),
        ("task", "Design checkout flow, in progress", "uxd", -36),
        ("task", "Optimize Google Search bids", "gm", -28),
        ("project", "Project started: Member Retention Campaign", "mkt", -18),
        ("collaboration", "DA + GM analysing retention cohorts", "da", -12),
        ("deliverable", "Wireframe critique completed by UI", "uid", -6),
        ("task", "Implement dark mode, PR opened", "fe", -2),
    ]
    for kind, msg, agent, mins_ago in activity_seeds:
        ts = (base_ts + timedelta(minutes=mins_ago)).isoformat() + "Z"
        aid = f"act-seed-{_uuid.uuid4().hex[:6]}"
        _agent_db().execute(
            "INSERT INTO activity_log (id, kind, message, agent, ts) VALUES (?, ?, ?, ?, ?)",
            [aid, kind, msg, agent, ts])
