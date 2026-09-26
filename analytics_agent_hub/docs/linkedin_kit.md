# Demo capture checklist + LinkedIn kit

## Record this (≈75 seconds, in order)

1. **Overview** (`?tour=1` optional) — KPI tiles animate in; pan the
   revenue-vs-spend chart. *Beat:* "every number is a live warehouse query."
2. **The story** — point at *Lead→Qualified CR by City*; Crestline's red line
   diving from September. *Beat:* "the blended average hides it."
3. **AI Analyst** — open chat, type `kenapa CR Crestline turun September?`
   Let the answer stream in with the chart + `ƒ` provenance. *Beat:* "no API
   key — deterministic NL→SQL."
4. **Ctrl/⌘K** — palette, jump to *Data Quality* → the **lineage graph**.
   *Beat:* "parsed live from dbt manifest."
5. **Sheet Sync** — the red **schema-drift** card: `omzet → cash_collected`
   quarantined with a confidence score. *Beat:* "ops keep their spreadsheets;
   we govern the boundary."

Tool: ScreenToGif / OBS at 1280×800, dark room background. Trim to <90s.

---

## LinkedIn draft — English

> I built a Growth Command Center with an AI analyst that answers data
> questions in Indonesian *and* English — and it needs **zero API key**.
>
> The chat parses your question into a metric × dimension × period intent,
> runs parameterized SQL over a dbt warehouse, and replies with the real
> number, a chart, and the exact query it used. (Plug in an LLM and it also
> narrates — but the numbers always come from SQL, never the model.)
>
> It also *finds* problems: a rolling z-score scanner caught one city's lead
> quality collapsing −27% while the company average looked fine.
>
> Stack: FastAPI · DuckDB · vanilla-JS SPA · ECharts. 100% synthetic data.
> Bonus page: governed Google-Sheets → warehouse sync with schema-drift
> quarantine (because ops will never leave spreadsheets 😄).
>
> Repo + 75-sec demo 👇  #dataengineering #analytics #AI

## LinkedIn draft — Bahasa Indonesia

> Gw bikin Growth Command Center dengan AI analyst yang bisa jawab pertanyaan
> data dalam Bahasa Indonesia & Inggris — dan **tanpa API key sama sekali**.
>
> Chat-nya nge-parse pertanyaan jadi intent (metrik × dimensi × periode),
> jalanin SQL ter-parameter ke warehouse dbt, terus balas dengan angka asli +
> chart + query yang dipakai. (Pasang LLM, dia juga narasiin — tapi angkanya
> selalu dari SQL, bukan dari model.)
>
> Dia juga *nemuin* masalah sendiri: scanner z-score nangkep kualitas lead
> satu kota anjlok −27% padahal rata-rata perusahaan kelihatan aman.
>
> Stack: FastAPI · DuckDB · SPA vanilla-JS · ECharts. Data 100% sintetis.
> Bonus: sync Google-Sheets → warehouse yang ter-governance, lengkap dengan
> karantina schema-drift.
>
> Repo + demo 75 detik 👇  #dataengineering #analytics #AI

---

## Follow-up comment seeds (drive engagement)

- *Architecture:* "The 'no naked numbers' rule: the LLM only ever sees the
  facts object, never the DB. Here's how the SSE stream ships the deterministic
  answer first, then narration…"
- *How the NLQ works:* "No semantic-parsing magic — it's vocabulary maps +
  intent dispatch to the same query functions the dashboard uses. 200 lines,
  fully unit-tested. Thread 🧵"
- *Lesson learned:* "First version derived a surrogate key from a mutable
  column and orphaned facts on a remap — the dbt relationship test caught it.
  Keys hang off stable identity only."
