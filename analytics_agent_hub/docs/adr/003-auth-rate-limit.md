# ADR 003: Auth & Rate Limiting

## Context
The Growth Command Hub provides endpoints that could be resource-intensive (e.g., DuckDB analytical queries, LLM inferences). As a portfolio project, we need to protect these endpoints from casual abuse while ensuring the application remains easy to demo.

## Decision
1. **Bearer Token Gate:** We implemented a demo-grade Bearer token gate using FastAPI's `HTTPBearer`. All `/api/*` routes (except `/api/health`) require the `Authorization: Bearer tryon` header.
2. **Token Bucket Rate Limiting:** A lightweight in-memory Token Bucket rate limiter is used to restrict the number of requests per IP address.
3. **Frontend Integration:** The vanilla JS frontend automatically intercepts `fetch` calls and injects the `Authorization` header only for same-origin or `/api` requests, preventing cross-origin CORS failures (e.g., map data, fonts).

## Consequences
- **Security Posture:** This is a *demo-grade* protection. The shared secret (`tryon`) is visible in the frontend source code. This is an intentional design choice to lower the friction for reviewers while preventing automated bots from immediately scraping the API.
- **Simplicity:** No external dependencies (like Redis or JWT libraries) are required. The entire stack remains easily portable.
