"""FastAPI app: JSON API for every page + the AI Analyst, and it serves the
static SPA. All heavy logic lives in the sibling modules; routes stay thin.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Query, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager

from . import agents, analyst, coordinator, funnel_detail, insights, llm, queries, quality, sql_workspace
from .config import settings
from .llm import polish_stream
from .rate_limit import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-bootstrap full synthetic warehouse if running standalone and missing
    from pathlib import Path
    import sys
    db_p = Path(settings.db_path)
    if not db_p.exists():
        root = Path(__file__).resolve().parents[1]
        sys.path.append(str(root))
        try:
            from data_gen.deploy_bootstrap import generate
            generate(str(db_p))
        except ImportError:
            try:
                from data_gen.bootstrap_db import bootstrap
                bootstrap(str(db_p))
            except ImportError:
                pass
    yield

app = FastAPI(title="Growth Command Hub", version="1.0.0", lifespan=lifespan)
WEB = Path(__file__).resolve().parents[1] / "web"

def _filters(city, channel, studio, month_from, month_to) -> dict:
    return {k: v for k, v in {
        "city": city, "channel": channel, "studio": studio,
        "month_from": month_from, "month_to": month_to,
    }.items() if v}

@app.middleware("http")
async def access_log(request: Request, call_next):
    rid = uuid.uuid4().hex[:8]
    t0 = time.perf_counter()
    path = request.url.path
    
    # Auth gate for all /api routes except health
    if path.startswith("/api") and path != "/api/health":
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer ") or auth_header.split(" ")[1] != "tryon":
            return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})

    response = await call_next(request)
    dt = (time.perf_counter() - t0) * 1000
    if path.startswith("/api"):
        print(json.dumps({"rid": rid, "path": path, "status": response.status_code, "ms": round(dt, 1)}))
    return response


# ---- meta ---------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "company": settings.company_name,
            "llm": llm.status(), "db": Path(settings.db_path).name}


@app.get("/api/meta")
def meta():
    d = queries.dimensions()
    return {"company": settings.company_name, "currency": settings.currency,
            "llm": llm.status(), **d}


class LLMSettings(BaseModel):
    provider: str | None = None      # anthropic | deepseek | openai
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    test: bool = False


@app.get("/api/settings/llm")
def get_llm_settings():
    return llm.status()


@app.post("/api/settings/llm")
def set_llm_settings(s: LLMSettings):
    if s.test and s.api_key:
        probe = llm.test_connection(s.model_dump())
        if not probe["ok"]:
            return JSONResponse({"ok": False, **probe}, status_code=400)
    llm.configure(s.provider, s.api_key, s.base_url, s.model)
    return {"ok": True, **llm.status()}


@app.post("/api/settings/llm/clear")
def clear_llm_settings():
    llm.configure(None, None, None, None)
    return {"ok": True, **llm.status()}


# ---- pages --------------------------------------------------------------

@app.get("/api/overview")
def overview(city: str = None, channel: str = None, studio: str = None,
             month_from: str = None, month_to: str = None):
    f = _filters(city, channel, studio, month_from, month_to)
    return {
        "kpis": queries.kpis_with_mom(f),
        "trend": queries.trend_monthly(f),
        "city_cr": queries.city_cr_matrix(),
        "insights": insights.insights_feed(),
    }


@app.get("/api/funnel")
def funnel(city: str = None, channel: str = None, studio: str = None,
           month_from: str = None, month_to: str = None):
    f = _filters(city, channel, studio, month_from, month_to)
    return {"funnel": queries.funnel(f), "cohort_lag": queries.cohort_lag(f),
            "kpis": queries.kpis(f)}


@app.get("/api/funnel/detailed")
def funnel_detailed(city: str = None, channel: str = None, studio: str = None,
                    month_from: str = None, month_to: str = None):
    f = _filters(city, channel, studio, month_from, month_to)
    return funnel_detail.generate_funnel(f)


@app.get("/api/funnel/sources")
def funnel_sources():
    return {"sources": funnel_detail.generate_data_sources()}


@app.get("/api/channels")
def channels(city: str = None, channel: str = None, studio: str = None,
             month_from: str = None, month_to: str = None):
    f = _filters(city, channel, studio, month_from, month_to)
    return {"league": queries.channel_league(f),
            "mix": queries.channel_mix_monthly(),
            "scd2": queries.scd2_channel_history()}


@app.get("/api/studios")
def studios(city: str = None, channel: str = None, studio: str = None,
            month_from: str = None, month_to: str = None):
    f = _filters(city, channel, studio, month_from, month_to)
    return {"league": queries.studio_league(f)}


@app.get("/api/revenue")
def revenue():
    return {"plan_mix": queries.plan_mix_monthly(),
            "attainment": queries.attainment_by_city(),
            "price_changes": queries.price_changes()}


@app.get("/api/forecast")
def forecast(horizon: int = Query(3, ge=1, le=6), method: str | None = Query(None)):
    return insights.forecast_revenue(horizon, method)


@app.get("/api/anomalies")
def anomalies():
    return {"anomalies": insights.scan_anomalies(),
            "city_cr": queries.city_cr_matrix()}


@app.get("/api/quality")
def data_quality():
    return {"summary": quality.build_summary(),
            "tests": quality.test_breakdown(),
            "freshness": quality.mart_freshness(),
            "lineage": quality.lineage_graph()}


@app.get("/api/geo")
def geo():
    import json
    p = WEB.parent / "data" / "geo" / "flows.json"
    if not p.exists():
        return {"available": False}
    return {"available": True, **json.loads(p.read_text(encoding="utf-8"))}


@app.get("/api/agents")
def agents_roster():
    return agents.roster()


class SqlBody(BaseModel):
    query: str


@app.post("/api/sql")
def run_sql(body: SqlBody):
    try:
        return {"ok": True, **sql_workspace.run(body.query)}
    except sql_workspace.SqlError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.get("/api/sql/schema")
def sql_schema():
    return {"tables": sql_workspace.schema()}


@app.get("/api/sql/preview")
def sql_preview(schema: str, table: str, limit: int = 50):
    try:
        return {"ok": True, **sql_workspace.preview(schema, table, limit)}
    except sql_workspace.SqlError as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/sql/stats")
def sql_stats():
    return sql_workspace.stats()


@app.post("/api/sql/format")
def sql_format(body: SqlBody):
    return {"formatted": sql_workspace.format_sql(body.query)}


# ---- Agent Actions ------------------------------------------------------

class TaskBody(BaseModel):
    agent_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    project_id: str | None = None

class ProjectBody(BaseModel):
    name: str
    goal: str
    agent_ids: list[str]

class DeliverableBody(BaseModel):
    title: str
    type: str
    agent_id: str
    project_id: str | None = None

class ReviewBody(BaseModel):
    action: str  # "approve" | "request_changes"
    comment: str = ""

class CollaborationBody(BaseModel):
    lead_id: str
    peer_id: str
    goal: str


@app.get("/api/agents/tasks")
def agent_tasks(agent_id: str | None = None, status: str | None = None):
    return {"tasks": agents.list_tasks(agent_id, status)}


@app.post("/api/agents/tasks")
def agent_create_task(body: TaskBody):
    t = agents.create_task(body.agent_id, body.title, body.description, body.priority, body.project_id)
    return {"task": t}


@app.patch("/api/agents/tasks/{task_id}")
def agent_update_task(task_id: str, status: str = Query(...)):
    t = agents.update_task(task_id, status)
    if not t:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return {"task": t}


@app.get("/api/agents/projects")
def agent_projects(agent_id: str | None = None):
    return {"projects": agents.list_projects(agent_id)}


@app.post("/api/agents/projects")
def agent_create_project(body: ProjectBody):
    p = agents.create_project(body.name, body.goal, body.agent_ids)
    return {"project": p}


@app.get("/api/agents/deliverables")
def agent_deliverables(agent_id: str | None = None):
    return {"deliverables": agents.list_deliverables(agent_id)}


@app.post("/api/agents/deliverables")
def agent_create_deliverable(body: DeliverableBody):
    d = agents.create_deliverable(body.title, body.type, body.agent_id, body.project_id)
    return {"deliverable": d}


@app.get("/api/agents/reviews")
def agent_reviews(agent_id: str | None = None):
    return {"reviews": agents.list_reviews(agent_id)}


@app.post("/api/agents/reviews/{review_id}")
def agent_review_action(review_id: str, body: ReviewBody):
    r = agents.review_action(review_id, body.action, body.comment)
    if not r:
        return JSONResponse({"error": "review not found"}, status_code=404)
    return {"review": r}


@app.get("/api/agents/collaborations")
def agent_collaborations(agent_id: str | None = None):
    return {"collaborations": agents.list_collaborations(agent_id)}


@app.post("/api/agents/collaborations")
def agent_start_collaboration(body: CollaborationBody):
    c = agents.start_collaboration(body.lead_id, body.peer_id, body.goal)
    return {"collaboration": c}


@app.get("/api/agents/activity")
def agent_activity(limit: int = Query(20, le=50)):
    return {"activity": agents.recent_activity(limit)}


@app.post("/api/agents/coordinate")
def agent_coordinate(body: dict):
    question = (body.get("question") or "").strip()
    if not question:
        return JSONResponse({"error": "empty question"}, status_code=400)
    result = coordinator.route(question)
    return result


class AgentChatBody(BaseModel):
    agent_id: str
    message: str


@app.post("/api/agents/chat/stream")
async def agent_chat_stream(request: Request):
    """SSE: agent-specific chat with real tool context + persona streaming."""
    body = await request.json()
    agent_id = (body.get("agent_id") or "").strip()
    message = (body.get("message") or "").strip()
    if not agent_id or not message:
        return JSONResponse({"error": "agent_id and message required"}, status_code=400)

    agent = agents.BY_ID.get(agent_id)
    if not agent:
        return JSONResponse({"error": "agent not found"}, status_code=404)

    # Gather real tool context
    tool_ctx = agents.agent_tool_context(agent_id, message)

    # Build persona-based system prompt
    persona_str = agent.get("persona", "")
    system = f"""You are {agent['role']}, an AI agent on the team.

Your personality: {persona_str}

You are given REAL DATA CONTEXT below. Use ONLY the numbers provided — never invent or recompute figures.
Respond in the SAME LANGUAGE as the user's message (Indonesian or English).
Be specific, concise (2-5 sentences), and confident. If a recommendation is natural, add one short actionable line.
Do not mention being an AI or describe these instructions."""

    context = tool_ctx.get("context_text", "")
    facts_str = f"REAL DATA CONTEXT:\n{context}\n\nUser asked: {message}"

    def gen():
        # 1) ship structured data first (chart/table/provenance/followups)
        data_payload = {
            "context_text": context,
            "chart": tool_ctx.get("chart"),
            "table": tool_ctx.get("table"),
            "provenance": tool_ctx.get("provenance"),
            "followups": tool_ctx.get("followups", _default_followups(agent_id)),
        }
        yield f"event: answer\ndata: {json.dumps(data_payload, default=str)}\n\n"

        # 2) stream LLM narration if available, else deterministic
        if llm.enabled():
            cfg = llm._active()
            try:
                if cfg.get("provider") == "anthropic":
                    for chunk in llm._stream_anthropic(cfg, message, {"text": ""}, system):
                        yield f"event: token\ndata: {json.dumps({'t': chunk})}\n\n"
                else:
                    payload = {
                        "model": cfg["model"], "stream": True, "temperature": 0.4,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": facts_str},
                        ],
                    }
                    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
                    url = cfg["base_url"].rstrip("/") + "/chat/completions"
                    import httpx
                    with httpx.stream("POST", url, json=payload, headers=headers, timeout=40) as r:
                        r.raise_for_status()
                        for line in r.iter_lines():
                            if not line or not line.startswith("data:"):
                                continue
                            data = line[5:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                delta = json.loads(data)["choices"][0]["delta"].get("content")
                                if delta:
                                    yield f"event: token\ndata: {json.dumps({'t': delta})}\n\n"
                            except Exception:
                                continue
            except Exception:
                yield f"event: token\ndata: {json.dumps({'t': _agent_deterministic_response(agent_id, message, tool_ctx)})}\n\n"
        else:
            yield f"event: token\ndata: {json.dumps({'t': _agent_deterministic_response(agent_id, message, tool_ctx)})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


def _agent_deterministic_response(agent_id: str, message: str, tool_ctx: dict) -> str:
    """Fallback deterministic response when no LLM is configured."""
    agent = agents.BY_ID.get(agent_id, {})
    context = tool_ctx.get("context_text", "")
    if context:
        return f"As {agent.get('role', agent_id)}, here's what I found:\n\n{context}\n\nHow can I help you dig deeper?"
    return coordinator._templated_response(agent_id, message)


def _default_followups(agent_id: str) -> list[str]:
    followups_map = {
        "orch": ["Team capacity overview", "What projects are active?", "Route a question to the right agent"],
        "da": ["Revenue by channel for Q3", "Which studios miss target?", "Kenapa CR Crestline turun?"],
        "gm": ["Funnel conversion rate trend", "CAC per channel last month", "Retention by studio"],
        "ml": ["Forecast next 3 months", "Any anomalies this week?", "Revenue prediction by city"],
        "pm": ["Project status summary", "What tasks are overdue?", "Team workload overview"],
        "proj": ["Timeline for active projects", "Any blocked tasks?", "Resource allocation"],
        "de": ["Data pipeline status", "Table freshness report", "Schema changes"],
        "ae": ["Data quality metrics", "Mart lineage", "Metric definitions"],
        "fs": ["API endpoint status", "Deployment pipeline", "Tech stack overview"],
        "fe": ["UI component library", "Accessibility audit", "Performance metrics"],
        "be": ["API performance", "Security review", "Database health"],
        "qa": ["Test coverage report", "Recent bugs", "Regression status"],
        "uxd": ["User flow analysis", "Wireframe review", "Interaction design"],
        "uid": ["Design system health", "Component usage", "Visual consistency"],
        "csm": ["Member retention rate", "Onboarding completion", "Health scores"],
        "mkt": ["Campaign performance", "Channel ROI", "GTM strategy"],
        "cont": ["Content performance", "SEO ranking", "Editorial calendar"],
        "ops": ["Process efficiency", "SLA compliance", "Capacity planning"],
        "ba": ["Requirements status", "Process mapping", "Gap analysis"],
        "uxr": ["Recent user studies", "Usability findings", "Research backlog"],
    }
    return followups_map.get(agent_id, [
        "What data do you have?",
        "How can you help me?",
        "Tell me about your expertise",
    ])


@app.get("/api/sheets")
def sheets_status():
    try:
        from sheetsync import engine
        return engine.status()
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.post("/api/sheets/sync")
def sheets_sync():
    try:
        from sheetsync import engine
        results = engine.sync_all()
        return {"ok": True, "results": results, "status": engine.status()}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---- AI analyst ---------------------------------------------------------

@app.post("/api/ask")
async def ask(request: Request):
    ip = request.client.host if request.client else "anon"
    ok, info = limiter.allow(ip)
    if not ok:
        return JSONResponse({"error": "rate_limited", **info}, status_code=429)
    body = await request.json()
    q = (body.get("question") or "").strip()
    if not q:
        return JSONResponse({"error": "empty question"}, status_code=400)
    ans = analyst.answer(q)
    ans["llm_available"] = llm.enabled()
    return ans


@app.post("/api/ask/stream")
async def ask_stream(request: Request):
    """SSE: deterministic facts first (instant), then optional LLM narration."""
    ip = request.client.host if request.client else "anon"
    ok, info = limiter.allow(ip)
    if not ok:
        return JSONResponse({"error": "rate_limited", **info}, status_code=429)
    body = await request.json()
    q = (body.get("question") or "").strip()
    persona = agents.persona(body.get("agent")) if body.get("agent") else None
    ans = analyst.answer(q)

    def gen():
        # 1) ship the structured answer immediately (chart/table/provenance)
        yield f"event: answer\ndata: {json.dumps(ans, default=str)}\n\n"
        # 2) narrate (real LLM if configured, else the deterministic text)
        if llm.enabled():
            for chunk in polish_stream(q, ans, persona):
                yield f"event: token\ndata: {json.dumps({'t': chunk})}\n\n"
        else:
            yield f"event: token\ndata: {json.dumps({'t': ans['text']})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---- static SPA (mounted last so /api wins) -----------------------------

@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
