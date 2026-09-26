# analytics-agent-hub

Multi-tenant agent hub untuk analytics growth: orchestrator fan-out, analyst
deterministik-first (NL→SQL), SQL workspace read-only, dan adapter channel.

**Status:** `analytics_agent_hub/` sudah versi penuh (FastAPI + DuckDB, 18 agen,
NL→SQL analyst, SQL workspace, data quality/lineage), auth beneran (password
hash + session token), dan isolasi data per-organisasi (`X-Org-Id` → warehouse
terpisah). Yang masih kurang ada di **[docs/BRIEF.md](docs/BRIEF.md)**: org
switcher di UI, user↔org membership, roles/invites, CSRF, channel
Telegram/WhatsApp beneran, dan deploy publik.

`funnel-warehouse/` di-vendor di sini (source **dan** hasil build: warehouse
DuckDB + dbt artifacts) supaya satu `git clone` langsung dapet data +
lineage/quality **asli** (bukan simulasi) — termasuk anomali Crestline yang
di-skrip di datanya, yang dipakai `analytics_agent_hub`'s anomaly scanner dan
test suite (15/15 pass dengan data ini vs 10/15 dengan fallback generator-nya
sendiri).

## Sumber konsep

| Sumber | Lisensi | Yang diambil |
|---|---|---|
| [rizalmachine/growth_analytics_platform](https://github.com/rizalmachine/growth_analytics_platform) | — | Basis fitur: `coordinator.py` (fan-out top-N + sintesis), `analyst.py`, `agents.py` (18 agen + Orchestrator), `llm.py`, `queries.py`, `quality.py`, `insights.py`, `sql_workspace.py`, `rate_limit.py`, `funnel_detail.py`, `web/` (SPA + SSE). Baca juga `docs/adr/001..006`. |
| [rizalmachine/funnel-warehouse](https://github.com/Rizalbu/funnel-warehouse) | — | Warehouse dbt asli yang dikonsumsi `analytics_agent_hub` (lihat `app/config.py`'s sibling-path default): generator sintetis, staging→marts, SCD2 snapshot, 60 dbt tests. |
| [ahmadrosid/nakama](https://github.com/ahmadrosid/nakama) | MIT | Arsitektur multi-tenant: org sebagai isolation boundary, org context via header `X-Org-Id` (sudah diadaptasi — lihat `app/tenancy.py`), auth + CSRF middleware, channel worker (Telegram/WhatsApp/Discord) yang benar-benar mengirim balasan, roles/invites, profile soul + memory. Lihat `ARCHITECTURE.md`. |

## Jalankan

```bash
cd analytics_agent_hub
pip install -r requirements.txt python-dotenv
python -m uvicorn app.main:app --port 8077
# buka http://127.0.0.1:8077, login try / tryon
```

Warehouse & dbt artifacts sudah ke-vendor di `funnel-warehouse/` — nggak perlu
build ulang dbt buat coba app-nya.

## Jalankan tes

```bash
cd analytics_agent_hub && pytest tests/ -q   # 15/15
```

## Multi-tenant

```bash
curl -X POST localhost:8077/api/orgs -H "Authorization: Bearer <token>" \
  -d '{"name":"Acme"}' -H 'content-type: application/json'
# ~1-2 menit, generate warehouse terpisah buat org ini

curl localhost:8077/api/overview -H "Authorization: Bearer <token>" \
  -H "X-Org-Id: <org id dari respons di atas>"
```

## Demo statis

[`docs/analytics-agent-hub/index.html`](docs/analytics-agent-hub/index.html)
(GitHub Pages dari folder `docs/`) — versi ringan tanpa backend, buat preview cepat.

---

Semua data sintetis. Tidak ada data pelanggan nyata.
