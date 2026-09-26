# ADR-005: AI Coordinator (fan-out routing)

**Status:** accepted

## Context

The AI Agents workspace has 18 role agents. Forcing the user to pick the right
agent for every request is friction, and single-agent answers miss
cross-domain questions ("analyze retention **then** propose a growth plan"
needs Data Analyst **and** Growth Manager).

## Decision

Add an **Orchestrator** agent + `app/coordinator.py` that routes requests
deterministically (no LLM needed for the routing decision):

1. **Score** the request against every agent by keyword overlap with the
   agent's `skills`/`expertise`/`role` (vocabulary in `_AGENT_KEYWORDS`).
2. **Select** the top-N most relevant agents, **capped at 3**, so the UI and
   token cost stay bounded.
3. **Dispatch** to each selected agent. Data-shaped questions route through
   `analyst.answer()` so numbers stay grounded ("no naked numbers"); other
   roles return role-templated output, optionally narrated by the configured
   LLM in the agent's persona voice.
4. **Synthesize** a unified summary and return `{routed_to, plan[], summary}`.
   Results are logged to the agent activity feed.

Endpoint: `POST /api/agents/coordinate`. Frontend: an "Ask the Orchestrator"
bar on the AI Agents page showing routing chips → per-agent contributions →
summary.

## Consequences

- Keyless by default (routing is pure Python) → fast, testable, demoable.
- Fan-out (max 3) covers cross-domain asks without unbounded cost.
- Numbers always come from the deterministic engine, never invented.
- Limitation: keyword routing is a heuristic, not semantic. Upgrade path:
  embeddings/LLM classifier behind the same `coordinate()` interface if recall
  becomes insufficient.
