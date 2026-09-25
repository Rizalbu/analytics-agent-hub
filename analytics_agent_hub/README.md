# Analytics Agent Hub

New project, original code, combining two architectural ideas from separate
public repos (not copied — concepts only):

- **Deterministic-first multi-agent routing**: a question is scored against
  an agent roster by keyword; the Data Analyst agent always answers from real
  DuckDB numbers first, an LLM (not wired up here) would only polish wording.
- **Multi-tenant + channel adapters**: every org gets its own API key and
  data slice; a Telegram-shaped webhook lets a chat channel reach the same
  coordinator the dashboard API uses.

## Run

```bash
pip install fastapi uvicorn duckdb
uvicorn app:app --reload
```

## Try it

```bash
curl -X POST localhost:8000/api/orgs -d '{"name":"Acme"}' -H 'content-type: application/json'
# -> {"id": "...", "api_key": "..."}

curl -X POST "localhost:8000/api/ask?x_org_key=<key>" \
  -d '{"question":"revenue this month?"}' -H 'content-type: application/json'
```

## Test

```bash
pytest tests/ -q
```
