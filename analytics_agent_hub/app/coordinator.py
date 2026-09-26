"""AI Coordinator — fan-out multi-agent routing engine.

Receives a user query, scores it against every agent in `agents.ROSTER`,
selects the top-N (max 3) most relevant agents, dispatches to each
individually, then synthesises a unified response.  All deterministic —
no LLM dependency for routing decisions.
"""
from __future__ import annotations

import re
from typing import Any

from . import agents, analyst, queries

# --------------------------------------------------------------------------
# Keyword → agent scoring vocabulary
# --------------------------------------------------------------------------

_AGENT_KEYWORDS: dict[str, list[str]] = {
    "pm": [
        "prd", "roadmap", "prioritisation", "prioritization", "feature",
        "product", "okr", "user story", "backlog", "sprint", "release",
    ],
    "proj": [
        "timeline", "deadline", "dependency", "risk", "milestone",
        "delivery", "schedule", "gantt", "project plan", "standup",
    ],
    "ba": [
        "requirement", "brd", "process map", "gap analysis", "workflow",
        "business rule", "use case", "as-is", "to-be",
    ],
    "da": [
        "sql", "kpi", "dashboard", "cohort", "a/b test", "ab test",
        "metric", "analytics", "insight", "trend", "conversion",
        "revenue", "lead", "cac", "roas", "member", "churn",
        "retention", "funnel", "cpl", "spend", "forecast",
    ],
    "de": [
        "pipeline", "warehouse", "dbt", "airflow", "etl", "elt",
        "orchestration", "data contract", "duckdb", "ingestion",
        "staging", "schema", "migration",
    ],
    "ae": [
        "semantic layer", "dimensional model", "metrics", "lineage",
        "data model", "mart", "dimension", "fact", "scd", "slowly changing",
    ],
    "ml": [
        "model", "training", "feature", "lightgbm", "drift",
        "evaluation", "serving", "ml", "machine learning", "forecast",
        "prediction", "anomaly", "z-score",
    ],
    "fs": [
        "full-stack", "end-to-end", "feature", "api", "ui", "deploy",
        "docker", "ci/cd", "cicd", "frontend", "backend", "ship",
    ],
    "fe": [
        "frontend", "ui", "typescript", "component", "accessibility",
        "a11y", "animation", "responsive", "css", "design system",
    ],
    "be": [
        "backend", "api", "service", "auth", "database", "cache",
        "security", "scaling", "endpoint",
    ],
    "qa": [
        "test", "qa", "regression", "playwright", "automation",
        "edge case", "bug", "quality assurance", "test plan",
    ],
    "uxr": [
        "user research", "interview", "usability", "persona",
        "synthesis", "user insight", "ethnography",
    ],
    "uxd": [
        "ux", "user experience", "flow", "wireframe", "interaction",
        "prototype", "information architecture", "ia",
    ],
    "uid": [
        "ui", "visual design", "design system", "motion", "polish",
        "token", "layout", "typography", "colour", "color",
    ],
    "gm": [
        "growth", "experiment", "funnel", "retention", "cac/ltv",
        "cac ltv", "a/b test", "ab test", "optimisation", "optimization",
        "conversion rate", "activation",
    ],
    "mkt": [
        "marketing", "positioning", "gtm", "go-to-market", "channel",
        "messaging", "campaign", "brand",
    ],
    "cont": [
        "content", "narrative", "seo", "editorial", "blog",
        "copywriting", "content strategy",
    ],
    "ops": [
        "operations", "process", "capacity", "sla", "forecasting",
        "workflow", "resource",
    ],
    "csm": [
        "customer success", "onboarding", "health score", "retention",
        "qbr", "account", "churn",
    ],
}


def _score_query(query: str) -> list[tuple[str, int]]:
    """Return list of (agent_id, score) sorted descending."""
    q = query.lower()
    scores: list[tuple[str, int]] = []
    for agent_id, kws in _AGENT_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in q:
                score += 1
        # bonus: if the agent role name appears in the query
        roster = agents.BY_ID.get(agent_id)
        if roster:
            role_lower = roster["role"].lower()
            if role_lower in q:
                score += 2
        if score > 0:
            scores.append((agent_id, score))
    scores.sort(key=lambda x: -x[1])
    return scores


def _agent_summary(agent_id: str) -> str:
    a = agents.BY_ID.get(agent_id, {})
    return f"**{a.get('role', agent_id)}** — {a.get('expertise', '')}"


def route(question: str, max_agents: int = 3) -> dict[str, Any]:
    """Score the question, dispatch to top-N agents, and synthesise.

    Returns a dict compatible with the API response:
      { question, agents: [...], synthesis, data?, chart?, table? }
    """
    scored = _score_query(question)

    # Always include DA if the query looks data-ish even without keyword match
    has_data_kw = any(
        kw in question.lower()
        for kw in ("revenue", "lead", "cac", "roas", "member", "spend", "kpi", "metric", "chart")
    )
    selected_ids: list[str] = []
    seen: set[str] = set()
    for aid, _ in scored:
        if aid not in seen:
            selected_ids.append(aid)
            seen.add(aid)
        if len(selected_ids) >= max_agents:
            break

    if has_data_kw and "da" not in seen:
        selected_ids = selected_ids[: max_agents - 1]
        selected_ids.append("da")
        seen.add("da")

    if not selected_ids:
        selected_ids = ["da"]
        seen.add("da")

    # Build contribution payloads
    contributions: list[dict[str, Any]] = []
    data_answer: dict[str, Any] | None = None

    for aid in selected_ids:
        agent = agents.BY_ID.get(aid, {})
        contrib: dict[str, Any] = {
            "agent_id": aid,
            "role": agent.get("role", aid),
            "init": agent.get("init", aid.upper()[:2]),
            "persona": agent.get("persona", ""),
            "response": None,
        }
        # Data agents get the real analyst engine
        if aid == "da" and has_data_kw:
            ans = analyst.answer(question)
            data_answer = ans
            contrib["response"] = ans.get("text", "")
            contrib["type"] = "data"
        else:
            # Templated persona response for non-data agents
            contrib["response"] = _templated_response(aid, question)
            contrib["type"] = "persona"
        contributions.append(contrib)

    # Synthesise
    synthesis = _synthesise(question, contributions)

    # Log to activity feed
    roles = ", ".join(c["role"] for c in contributions)
    agents._log(
        "coordinate",
        f"Orchestrator dispatched to {len(contributions)} agent(s): {roles} — {question[:80]}",
    )

    result: dict[str, Any] = {
        "question": question,
        "agents": contributions,
        "synthesis": synthesis,
    }

    # Forward data chart / table if DA contributed
    if data_answer:
        for key in ("chart", "table", "provenance"):
            if key in data_answer:
                result[key] = data_answer[key]

    return result


def _templated_response(agent_id: str, question: str) -> str:
    """Deterministic persona-based response (no LLM, no data query)."""
    agent = agents.BY_ID.get(agent_id, {})
    role = agent.get("role", agent_id)
    expertise = agent.get("expertise", "")

    templates = {
        "pm": f"As a Product Manager, I'd frame this by defining success metrics and drafting a PRD. "
              f"To answer '{question}', I recommend we start with a problem statement and OKRs.",
        "proj": f"From a project management perspective, '{question}' needs clear milestones, "
                f"dependency mapping, and a risk register. I can set up a timeline.",
        "ba": f"As a Business Analyst, I'd approach '{question}' by mapping current processes, "
              f"gathering requirements, and identifying gaps. Let me prepare a BRD.",
        "fe": f"As a Frontend Developer, I'd tackle '{question}' by focusing on component architecture, "
              f"state management, and accessibility from the start.",
        "be": f"As a Backend Developer, I'd address '{question}' by designing the API contracts, "
              f"data access layer, and security boundaries first.",
        "qa": f"As a QA Engineer, I'd start with a test plan covering edge cases, regression paths, "
              f"and automation scenarios for '{question}'.",
        "uxd": f"As a UX Designer, I'd explore '{question}' by sketching user flows, wireframes, "
               f"and low-fidelity prototypes to validate the interaction model.",
        "uid": f"As a UI Designer, I'd approach '{question}' with visual hierarchy, design tokens, "
               f"and polished component specs aligned to our design system.",
        "gm": f"As a Growth Manager, I'd run experiments around '{question}' — A/B tests, funnel "
              f"analysis, and retention cohorts to find the lever.",
        "de": f"As a Data Engineer, I'd build reliable, idempotent pipelines to answer '{question}' "
              f"with tested data contracts and observable freshness.",
        "ae": f"As an Analytics Engineer, I'd model the data cleanly around '{question}' — "
              f"dimensional marts, clear metrics, and documented lineage.",
        "ml": f"As an ML Engineer, I'd build a feature set, train a model with proper evaluation, "
              f"and monitor drift to answer '{question}' quantitatively.",
        "mkt": f"As a Marketing Strategist, I'd sharpen positioning and plan a GTM that addresses "
               f"'{question}' with channel-level tactics.",
        "cont": f"As a Content Strategist, I'd build a narrative engine around '{question}' — "
                f"editorial calendar, SEO research, and messaging architecture.",
        "csm": f"As a Customer Success lead, I'd look at onboarding health, engagement scores, "
               f"and QBR insights to answer '{question}'.",
        "ops": f"As an Operations Manager, I'd analyse process capacity, SLAs, and resource "
               f"allocation to address '{question}'.",
        "uxr": f"As a UX Researcher, I'd design a study to uncover user needs around "
               f"'{question}' — interviews, usability tests, and synthesis.",
    }
    return templates.get(agent_id,
                         f"As a {role} specialising in {expertise}, I can contribute to "
                         f"'{question}' with domain expertise.")


def _synthesise(question: str, contributions: list[dict[str, Any]]) -> str:
    """Combine multiple agent responses into one coherent summary."""
    if len(contributions) == 1:
        c = contributions[0]
        return f"**{c['role']}** responded: {c['response']}"

    lines: list[str] = [
        f"I routed your question to **{len(contributions)} agents** whose expertise matches your request.\n"
    ]
    for c in contributions:
        role = c["role"]
        resp = c["response"]
        # Truncate long responses for the synthesis overview
        if len(resp) > 200:
            resp = resp[:200] + "…"
        lines.append(f"• **{role}**: {resp}")

    lines.append(
        "\n*Each agent contributed from their domain. "
        "You can chat with any agent individually for deeper discussion.*"
    )
    return "\n\n".join(lines)
