# analytics-agent-hub

Multi-tenant agent hub untuk analytics growth: orchestrator fan-out, analyst
deterministik-first (NL→SQL), SQL workspace read-only, dan adapter channel.

**Status: kerangka awal.** `analytics_agent_hub/` masih versi tipis (192 baris)
dan belum memenuhi target. Apa yang harus dibangun, apa yang sudah ada di sumber
konsepnya, dan bug yang harus dibetulkan lebih dulu ada di
**[docs/BRIEF.md](docs/BRIEF.md)** — baca itu dulu sebelum menulis kode.

## Sumber konsep

| Sumber | Lisensi | Yang diambil |
|---|---|---|
| [rizalmachine/growth_analytics_platform](https://github.com/rizalmachine/growth_analytics_platform) | — | Basis fitur: `coordinator.py` (fan-out top-N + sintesis), `analyst.py`, `agents.py` (18 agen + Orchestrator), `llm.py`, `queries.py`, `quality.py`, `insights.py`, `sql_workspace.py`, `rate_limit.py`, `funnel_detail.py`, `web/` (SPA + SSE). Baca juga `docs/adr/001..006`. |
| [ahmadrosid/nakama](https://github.com/ahmadrosid/nakama) | MIT | Arsitektur multi-tenant: org sebagai isolation boundary, org context via header `X-Org-Id`, auth + CSRF middleware, channel worker (Telegram/WhatsApp/Discord) yang benar-benar mengirim balasan, roles/invites, profile soul + memory. Lihat `ARCHITECTURE.md`. |

## Jalankan tes

```bash
pip install fastapi duckdb pytest httpx uvicorn
mkdir -p analytics_agent_hub/data      # app belum membuat folder ini sendiri
cd analytics_agent_hub && pytest tests/ -q
```

App: `uvicorn app:app --reload` dari dalam `analytics_agent_hub/`.

## Demo

Halaman statis: [`docs/analytics-agent-hub/index.html`](docs/analytics-agent-hub/index.html)
(dipublikasikan lewat GitHub Pages dari folder `docs/`).

---

Semua data sintetis. Tidak ada data pelanggan nyata.
