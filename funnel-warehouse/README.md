# Funnel Warehouse: Dimensional Growth Analytics with dbt

Production-style analytics warehouse for **FitFlow Studios**, a fictional 12-studio fitness chain.
Messy multi-studio operational CSVs → tested star schema → executive scorecard.

**100% synthetic data, generated in-repo.** No real companies, customers, or numbers.

```
generator (Faker, scripted mess & anomalies)
   └─ data/drops/*.csv     3 header variants · 3 date formats · dup rows
                           · "Rp 1.250.000" money-as-text · messy booleans
        └─ pipeline/load_raw.py    structural normalization + lineage cols
             └─ DuckDB raw schema
                  └─ dbt: staging → intermediate → marts (+ SCD2 snapshot,
                     60 tests incl. custom funnel_monotonicity)
                       └─ dashboard/index.html (static, Chart.js)
```

## Quickstart (~3 minutes)

```bash
uv venv -p 3.12 .venv && uv pip install -r requirements.txt
.venv/Scripts/python generator/generate.py --days 365     # ~47K leads
.venv/Scripts/python pipeline/load_raw.py
cd dbt && ../.venv/Scripts/dbt build --profiles-dir . && cd ..
.venv/Scripts/python dashboard/build_dashboard.py          # → dashboard/index.html
```

(macOS/Linux: replace `.venv/Scripts/` with `.venv/bin/`, or just `make demo`.)

## What this demonstrates

| Pattern | Where |
|---|---|
| Conformed dimensions (14 raw channel labels → 7 channels) | `int_channel_mapping`, `dim_channel` |
| SCD Type 2 via dbt snapshot + live demo | `snapshots/`, `scripts/demo_scd2.py` |
| Point-in-time join (sale priced at the price list valid that day) | `fct_revenue` + `assert_sale_price_sane` |
| Incremental fact with late-arrival reprocessing window | `fct_funnel_daily` |
| Business rule as a custom generic test | `tests/generic/funnel_monotonicity.sql` |
| Stage definitions unified once, documented | `int_funnel_atomic`, ADR-001 |
| PII stops at staging; marts are PII-free by design | ADR-001 |
| Deliberate data mess + the cleaning that survives it | `generator/`, `models/staging/` |

## The story in the data

A scripted anomaly: **Crestline city's paid-social lead quality collapses in Sep 2025**
(lead→qualified 59% → 45%) while blended company averages barely move: the
classic case for city × channel funnel marts over single-number dashboards.
Open `dashboard/index.html` and look at the red line.

## SCD2 demo

```bash
.venv/Scripts/python scripts/demo_scd2.py     # remaps TikTok Ads → paid_video, re-snapshots
```

Prints the snapshot history showing both versions with validity windows.
Re-running `pipeline/load_raw.py` restores the source mapping; the next
snapshot records the revert as a third version, proof SCD2 is doing its job.

## Verified results (seed=42, 365 days)

- 47,097 leads → 16,958 bookings → 15,390 visits → 3,829 sales (+ ~1.5% injected dups, all deduped in staging)
- `dbt build`: **60/60 passing** (models, seeds, snapshot, 40 data tests) in ~5s
- `pytest`: 5/5 generator invariants
- Full pipeline from clean clone: ~3 minutes

## Layout

```
generator/          synthetic data + scripted mess (config.py = all knobs)
pipeline/           CSV → DuckDB raw loader (header aliases, lineage)
dbt/                models, snapshots, seeds, macros, tests
dashboard/          static HTML scorecard builder
scripts/            SCD2 live demo
docs/               ADRs, data model, metric definitions
tests/              generator invariant tests (pytest)
```

## Docs

- [ADR-001: Funnel stage definitions & PII boundary](docs/adr/001-funnel-stage-definitions.md)
- [ADR-002: Two SCD strategies, on purpose](docs/adr/002-scd-strategy.md)
- [ADR-003: DuckDB locally, BigQuery as prod path](docs/adr/003-duckdb-bigquery.md)
- [Data model](docs/data_model.md) · [Metric definitions](docs/metric_definitions.md)
