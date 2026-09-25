# BRIEF — analytics_agent_hub

> Dokumen ini adalah **permintaan produk**, bukan catatan. Kalau ada konflik antara
> kode yang sudah ada di branch ini dan isi BRIEF ini, **BRIEF yang menang.**
> Tulis dalam bahasa Indonesia di chat, English untuk nama file/kode.

## Kondisi sekarang

`analytics_agent_hub/` (192 baris `app.py` + 45 baris tes + halaman statis 296 baris)
terlalu tipis untuk disebut "menggabungkan dua konsep". Yang hilang bukan polesan —
mekanisme intinya tidak ada. Lihat bagian *Bug yang harus dibetulkan lebih dulu*
untuk bukti hasil uji nyata.

## Sumber kebenaran

Semua publik, bisa dibaca langsung tanpa login.

### 1. `https://github.com/rizalmachine/growth_analytics_platform` — app yang SUDAH JALAN (~4.006 baris)

Ini basis fiturnya. **Baca `docs/adr/001..006` sebelum menulis kode apa pun** —
di situ alasan desainnya:

| ADR | Isi |
|---|---|
| 001 | Two-tier AI Analyst (deterministik dulu, LLM menyusul) |
| 002 | Sheet-sync contracts |
| 003 | Auth & rate limiting |
| 004 | SSE streaming |
| 005 | AI Coordinator — fan-out routing |
| 006 | SQL Workspace guardrails |

File yang menentukan perilaku:

| File | Baris | Yang harus ditiru |
|---|---|---|
| `app/coordinator.py` | 279 | Orchestrator: skor pertanyaan ke roster → fan-out **top-N (maks 3)** → **sintesis** jawaban |
| `app/agents.py` | 519 | 18 agen + Orchestrator: role, expertise, persona, skills |
| `app/analyst.py` | 433 | NL→SQL deterministik bilingual (metrik × dimensi × periode × perbandingan), parameterized, **hanya mart** |
| `app/llm.py` | 194 | Tier-2 polish opsional; angka tetap dari engine ("no naked numbers") |
| `app/queries.py` | 428 | 26 tabel / 5 schema / 198 kolom |
| `app/quality.py` | 276 | dbt tests + lineage graph |
| `app/insights.py` | 236 | Auto-insight feed |
| `app/sql_workspace.py` | 140 | SQL workspace read-only + guardrail |
| `app/rate_limit.py` | 33 | Rate limiting |
| `app/funnel_detail.py` | 307 | Funnel multi-tahap + sumber akuisisi |
| `web/` | — | SPA: SSE streaming, chart di dalam bubble chat, ⌘K palette, tema light/dark |

Halaman yang harus ada: Overview · Funnel Explorer · Channels & Spend · Studios ·
Revenue & Targets · Forecast · Anomalies · Member Origins (peta) · AI Agents ·
SQL Workspace · Data Sources · Model Lineage · Data Quality · Data Sync · AI Analyst.

### 2. `https://github.com/ahmadrosid/nakama` — lisensi **MIT**, boleh ambil KODE (bukan cuma konsep)

Baca `ARCHITECTURE.md`. Yang diambil:

- **org = isolation boundary.** Semua entity org-scoped: profiles, sessions, tools,
  automations, usage.
- **Org context lewat header `X-Org-Id` + middleware** — bukan API key di query string.
- **auth + CSRF middleware**, roles / invites / members.
- **Channel worker Telegram / WhatsApp / Discord yang BENAR-BENAR MENGIRIM balasan.**
- Profile "soul": identitas, instructions, memory; tools, skills, MCP.

## Fitur yang diminta di `analytics_agent_hub`

1. **Routing** = fan-out top-N + sintesis seperti `coordinator.py`, dengan threshold
   dan penanganan skor seri yang eksplisit — **bukan** "yang pertama di daftar menang".
   Setiap agen yang menjawab harus menjawab dengan **data nyata**, bukan teks template.
2. **Multi-tenancy persisten**: org disimpan di DB, **API key di-hash**, org context
   via header `X-Org-Id`. Tiap org punya data slice sendiri. Tidak boleh hilang saat
   proses restart.
3. **Channel adapter yang benar-benar mengirim balasan** ke chat (Telegram), bukan
   hanya mengembalikan HTTP body ke pemanggil.
4. **Basis fitur** = daftar halaman di bagian Sumber kebenaran #1. Jangan bikin versi
   mini dari router keyword.
5. **Tidak boleh ada agen placeholder.** Kalau belum bisa diimplementasikan, hapus.
   3 agen kosong lebih buruk daripada 1 agen yang benar.

## Bug yang harus dibetulkan lebih dulu (hasil uji nyata, bukan dugaan)

1. **App gagal boot di clone bersih.** Folder `data/` tidak dibuat oleh aplikasi —
   hanya di dalam `tests/test_app.py` — sementara `.gitignore` mengecualikan
   `analytics_agent_hub/data/`, jadi folder itu tidak pernah ada di git.
   ```
   folder data/ ada? False
   startup event: GAGAL -> IOException: Cannot open file "...\data\hub.duckdb":
     The system cannot find the path specified.
   # setelah mkdir data:
   startup event: BERHASIL
   ```
   Artinya quickstart README (`uvicorn app:app --reload`) gagal di clone baru.

2. **API key dikirim di URL.** `x_org_key` jalan sebagai *query parameter*, bukan header
   (diverifikasi: sebagai header → `422`, sebagai query → `200`). Nama variabelnya
   berawalan `x_` padahal bukan header. Key = 32 hex, bocor ke access log &
   header `Referer`.

3. **Webhook tanpa verifikasi apa pun.** Tidak ada cek
   `X-Telegram-Bot-Api-Secret-Token`, dan key malah ada di **path URL**
   (`/webhooks/telegram/{api_key}`). Payload bukan-Telegram dibalas
   `200 {"ok": true}` — gagal senyap. Dan **tidak ada pengiriman balasan keluar**:
   balasan hanya jadi HTTP body, tidak pernah sampai ke chat.

4. **Tenancy in-memory.** `ORGS` itu `dict` biasa:
   `org sebelum=1 sesudah=0 | baris leads di DuckDB sebelum=200 sesudah=200 | key lama -> 401`
   → setiap restart semua pelanggan kehilangan akses, datanya tetap menumpuk.

5. **Tidak ada rate limit.** 60 request beruntun ke `/api/ask` → semuanya `200`.

6. **KPI tidak bermakna.** `leads=200 customers=74 conversion=0.370` — `leads`
   dihitung `count(*)` **semua** baris, termasuk yang sudah jadi customer. Tidak ada
   tahap funnel berurutan. Data sintetis `random.choice` tanpa seed → tidak reproducible,
   padahal halaman demo mengklaim "grounded in the warehouse".

7. **Router diduplikasi di JavaScript dan sudah melenceng.** Sup agent:
   Python `['bantuan','error','help','issue','problem']` vs JS
   `['error','help','issue','problem','support']` → pertanyaan "ada bantuan?"
   dirutekan **beda** antara API dan halaman demo.

8. **XSS di halaman demo.** `docs/analytics-agent-hub/index.html:240` memakai
   `div.innerHTML = text` untuk pesan user (`addMsg(null, question, true)`, baris 246).

9. **Kualitas kode**: `@app.on_event("startup")` deprecated (3 warning di pytest,
   pakai `lifespan`); `_conn()` tanpa `try/finally` → koneksi bocor saat error di tengah;
   `DB_PATH` relatif ke CWD; README `pip install fastapi uvicorn duckdb` tidak
   menyertakan `pytest` + `httpx` yang dibutuhkan tes.

## Aturan kerja

1. **Bukti, bukan klaim.** Setiap "selesai" harus disertai perintah yang dijalankan + output.
   Tes harus lulus dari **clone bersih** — bukan dari direktori kerja yang sudah siap.
2. **Jangan duplikasi logika** antara backend dan halaman demo. Halaman demo memanggil API.
3. **Tulis tes untuk jalur gagal**, bukan hanya happy path: key salah (`401`), header
   vs query (`422`), isolasi antar-org (org A tidak bisa baca data org B), restart
   proses, payload webhook ngawur.
4. **Jangan commit atau push ke repo ini tanpa diminta eksplisit.** Kalau diminta, sebut
   file yang berubah di akhir jawaban.
5. Sumber konsep boleh dibaca dan kodenya boleh diambil (nakama = MIT), tapi sebut jelas
   mana yang diambil dari mana.

## Definisi selesai

- [ ] `git clone` bersih → `uvicorn app:app` jalan tanpa langkah manual tambahan.
- [ ] Semua endpoint diuji dari clone bersih, hasilnya dilaporkan (status + contoh output).
- [ ] Multi-tenancy persisten: buat org → restart proses → API key lama masih valid,
      data org lain tidak terlihat.
- [ ] API key di header `X-Org-Id`, bukan di query string atau path URL.
- [ ] Webhook memverifikasi secret token dan benar-benar mengirim balasan ke chat.
- [ ] Routing fan-out top-N + sintesis dengan threshold & penanganan skor seri.
- [ ] Tidak ada agen placeholder; setiap agen menjawab dengan angka nyata.
- [ ] Tidak ada duplikasi router di JavaScript; halaman demo memakai API.
- [ ] Tes mencakup jalur gagal di atas dan lulus dengan `pytest -q`.
- [ ] README mencantumkan semua dependensi (termasuk `pytest`, `httpx`) dan langkah
      menjalankan tes.
