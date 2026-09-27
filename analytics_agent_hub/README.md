# Growth Analytics Platform (analytics_agent_hub base)

> Ported in as-is from `growth_analytics_platform` (own repo) as the feature
> base for **analytics-agent-hub**. Multi-tenant layer (org isolation via
> `X-Org-Id`, auth/CSRF, real channel-sending workers, inspired by
> `ahmadrosid/nakama`, MIT) is the next layer to add on top; see
> [`../docs/BRIEF.md`](../docs/BRIEF.md) for the full spec.

> *Repo folder is `growth-command-hub/`; the product is **Growth Analytics Platform**.*

A premium **analytics command center** for *FitFlow Studios*, a fictional
12-studio fitness chain. Solarized light/dark themes, a 3D login landing,
executive scorecard, funnel explorer, channel economics, revenue forecasting,
a statistical anomaly scanner, a global member-flow map, a governed data-sync
layer, dbt lineage + data-quality, a live **read-only SQL workspace**, and an
**AI Agents workspace** with an Orchestrator that routes work across 18
specialized agents. The **AI Analyst** answers in Indonesian or English with
real numbers, charts, and the SQL behind them, **no API key required**, with
one-click upgrade to DeepSeek or Claude.

**Demo login:** `try` / `tryon`.

> **100% synthetic data. Fictional company.** No real brands, customers, or
> numbers. The warehouse is auto-bootstrapped on first run (no external
> dependency); it mirrors the companion `funnel-warehouse` schema.

---

## Why it's interesting

- **AI Analyst that works with no key, upgrades to a real LLM in one click.**
  A deterministic natural-language-to-SQL engine parses intent (metric ×
  dimension × period × comparison) from bilingual text, runs *parameterized,
  mart-only* queries, and returns prose + an ECharts chart + the query
  provenance. Open ⚙️ to plug in **DeepSeek or Claude** (or any
  OpenAI-compatible endpoint); the model narrates. Every number still comes
  from the engine ("no naked numbers").
- **AI Agents workspace.** 18 role agents + an **Orchestrator** that scores a
  request against the roster, fans out to the top-N (max 3), and synthesises a
  unified answer. Actions: chat, assign task, create deliverable, review work,
  collaborate, persisted in a DuckDB state store.
- **Live SQL Workspace.** Write `SELECT` against the warehouse with a schema
  browser, results grid, and CSV export, guarded read-only (SELECT-only,
  file-function blocklist, row cap, statement timeout).
- **Member Origins map.** ECharts world map with animated origin→hub flow
  lines + member bubbles, from a self-made geo dataset (real city lat/lng →
  fictional FitFlow hubs).
- **It finds the story itself.** A rolling z-score scanner flags that
  *Crestline's* lead-quality collapses from September while blended averages
  stay flat, deep-linking into a pre-filtered funnel view.
- **Real data engineering on screen.** Data Quality + Model Lineage parse dbt
  artifacts (or synthesize equivalents from live row counts on a standalone
  deploy); governed spreadsheet ingestion with schema-drift quarantine,
  validation, idempotent MERGE, and deletion detection.
- **Premium, themeable UI.** Solarized light/dark, ⌘K palette, streaming chat
  with inline charts, skeleton loaders, guided tour (`?tour=1`).

## Stack

FastAPI · DuckDB (read-only) · vanilla JS SPA + ECharts · sqlglot (SQL
guardrails) · pytest. No build step, no framework lock-in. Runs locally or in
Docker.

## Quickstart

```bash
cd growth-command-hub
uv venv -p 3.12 .venv
uv pip install -r requirements.txt

# warehouse auto-bootstraps on first boot if missing; seed the sync demo:
.venv/Scripts/python -m sheetsync.seed
.venv/Scripts/python -m sheetsync.run

.venv/Scripts/python -m uvicorn app.main:app --port 8077
# open http://127.0.0.1:8077   (login try / tryon · add ?tour=1 for the tour)
```

(macOS/Linux: use `.venv/bin/...`. Docker: `docker compose up`.)

## Connect a real AI model (optional)

Chat works with **zero config**. To add LLM narration, click ⚙️ → pick a
provider → paste key → *Test & connect*:

| Provider | Picks | Default model |
|---|---|---|
| **DeepSeek** | OpenAI-compatible | `deepseek-chat` |
| **Claude** | Anthropic `/v1/messages` | `claude-opus-4-8` |
| **OpenAI-compat** | OpenAI / OpenRouter / Groq / Ollama | `gpt-4o-mini` |

Key stays in server memory for the session, never sent to the browser, never
committed. Can also preset via `.env` (see `.env.example`).

## Pages

| Section | Page | Highlights |
|---|---|---|
| Analytics | Overview | KPI tiles + MoM deltas, revenue vs spend, auto-insights feed |
| | Funnel Explorer | multi-stage funnel + acquisition sources, drop-off, cohort lag |
| | Channels & Spend | CAC/CPL/ROAS league, spend→revenue scatter, SCD2 history |
| | Studios | league table with target attainment bars |
| | Revenue & Targets | plan-mix stack, attainment vs target, price-book changes |
| | Forecast | 3-method forecast + rolling-origin backtest (MAPE) |
| | Anomalies | rolling z-score scanner + city×month CR heatmap |
| | Member Origins | world map, animated origin→hub flows, location intelligence |
| Workspace | AI Agents | 18 agents + Orchestrator; tasks, deliverables, reviews, collaborations; owner-only Engineering Loop with a staged review queue (live "try it" preview, promote/reject, per-org rollout + kill switch) |
| | SQL Workspace | read-only SQL editor, schema browser, results, CSV export |
| Engineering | Data Sources | multi-source connector catalog |
| | Model Lineage | dbt model graph (staging → marts) |
| | Data Quality | dbt tests + freshness |
| | Data Sync | contracts, drift quarantine, deletion detection |
| Everywhere | AI Analyst | streaming chat, charts in-bubble, SQL provenance |

## Ask the AI Analyst / Orchestrator

```
revenue Brightwater Q3
kenapa CR Crestline turun September?
CAC per channel last month
which studios miss target?
analyze retention then propose a growth plan   # → Orchestrator fans out
```

## Architecture

```
Browser SPA (web/) ──fetch (Bearer auth)──▶ FastAPI (app/)
  ECharts · ⌘K · chat        ├─ queries.py       parameterized, mart-only SQL
                             ├─ analyst.py       NL→SQL engine (tier-1) ─┐
  SSE stream  ◀──────────────┤  llm.py           optional narration      │ no
                             ├─ coordinator.py   fan-out agent routing    │ naked
                             ├─ agents.py        roster + state store     │ numbers
                             ├─ sql_workspace.py guarded read-only SQL    │
                             ├─ funnel_detail.py multi-stage funnel       │
                             ├─ insights.py      z-score + forecast       │
                             └─ quality.py       dbt artifacts / synth    ┘
                                   │ read-only
                                   ▼
        DuckDB warehouse (auto-bootstrap)  +  sheetsync/ (governed CSV→DuckDB)
```

## Tests

```bash
.venv/Scripts/python -m pytest tests/ -q     # NLQ, anomaly, forecast, sheet-sync
```

## Docs

- [ADR-001: Two-tier AI Analyst (deterministic-first)](docs/adr/001-two-tier-analyst.md)
- [ADR-002: Sheet-sync contracts](docs/adr/002-sheetsync-contracts.md)
- [ADR-003: Auth & rate limiting](docs/adr/003-auth-rate-limit.md)
- [ADR-004: SSE streaming](docs/adr/004-sse-streaming.md)
- [ADR-005: AI Coordinator (fan-out routing)](docs/adr/005-ai-coordinator.md)
- [ADR-006: SQL Workspace guardrails](docs/adr/006-sql-workspace.md)
- [ADR-007: Engineering Loop staging pipeline](docs/adr/007-engineering-loop-staging.md)
- [AI Studio design blueprint](docs/ai-studio.md) · [LinkedIn kit](docs/linkedin_kit.md)

## Privacy

Anonymized reimagining of a generic growth-ops pattern. No employer, brand,
product, or person names; no real schemas or data. All figures synthetic.
Optional external connectors (Google Sheets, LLM providers) are off by default.
