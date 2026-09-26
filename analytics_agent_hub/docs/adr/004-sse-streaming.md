# ADR 004: SSE Streaming Architecture

## Context
The AI assistant feature (`/api/ask/stream`) provides conversational insights over the data. Generating an LLM response can take several seconds, which degrades the perceived performance of the UI. Furthermore, we want to ensure that the core numbers and charts presented to the user are 100% accurate and not hallucinated by the LLM.

## Decision
We implemented a **Server-Sent Events (SSE)** streaming architecture with a "deterministic-first" approach:
1. **Immediate Structured Data:** The backend first resolves the user's intent deterministically (mapping to SQL/DuckDB queries) and yields the raw data, chart configurations, and provenance immediately as the first SSE event (`event: answer`).
2. **LLM Narration:** Once the data is shipped, the system passes the structured answer to the LLM. The LLM acts purely as a narrator, summarizing the pre-computed facts. These tokens are streamed back incrementally (`event: token`).
3. **Fallback:** If the LLM is disabled or fails, the system yields a deterministic text summary instead.

## Consequences
- **UX Improvement:** The user instantly sees the chart and data table, making the UI feel snappy, while the text explanation streams in naturally.
- **Trust and Grounding:** The LLM cannot hallucinate the numbers because the UI renders the data directly from the deterministic step. The LLM is constrained to only narrate the facts already established.
