# ADR-001: Two-tier AI Analyst (deterministic-first)

**Status:** accepted

## Context

The headline feature is a chat that answers growth questions over the
warehouse. The obvious build is "text → LLM → SQL → answer". That approach has
three problems for a portfolio/demo product: it requires an API key to work at
all, it can hallucinate numbers, and a reviewer can't see *how* it works.

## Decision

Two tiers, with the LLM strictly optional.

**Tier 1: deterministic NLQ engine (`analyst.py`).** Parse an intent
(metric × dimension × period × comparison × intent-type) from bilingual text
using vocabulary maps, then dispatch to a handler that calls the *same*
`queries.py` functions the dashboard uses. Output is a structured answer:
prose with real numbers, an ECharts spec, an optional table, follow-up chips,
and a provenance string. This works with **no API key** and is fully testable.

**Tier 2: LLM narration (`llm.py`), optional.** If `LLM_API_KEY` is set, the
deterministic answer object is handed to an OpenAI-compatible model that
rephrases it fluently and streams over SSE. The model is shown the **facts**
(headline + table), never the raw warehouse, and is instructed to use only the
numbers given, "no naked numbers". If the call fails, we fall back to the
tier-1 text.

## Consequences

- The demo is impressive **and** keyless; reviewers can read the whole intent
  parser and SQL.
- Numbers are always correct because they come from parameterized SQL, whether
  or not an LLM is attached.
- Bilingual support (ID/EN) is just vocabulary lists, easy to extend.
- Limitation: tier-1 covers the canonical question shapes (metric lookups,
  breakdowns, why/anomaly, miss-target, forecast). Truly open-ended questions
  fall back to guided suggestions rather than guessing, a deliberate honesty
  choice. Tier 2 widens the phrasing it can handle, not the data it can touch.

## Security note

`queries.py` never interpolates user text into SQL; dimension values are
validated against an allow-list and all filters are bound parameters. The DB
connection is opened `read_only`. The chat endpoint is rate-limited per IP.
