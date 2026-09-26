# Data Model

## Star schema

```
                      dim_date
                         │
 dim_studio ──┐          │          ┌── dim_channel (SCD2-backed)
              ├── fct_funnel_daily ─┤
              │   (date×studio×channel)
              │
              ├── fct_revenue (grain: sale)──── price_book (effective-dated)
              │        │
              │     dim_member (purchasers, PII-free)
              │
              ├── fct_ad_spend (date×channel)
              └── fct_targets (month×studio)

 mart_executive_scorecard = month×city rollup over all facts
```

## Grains & keys

| Table | Grain | Key | SCD |
|---|---|---|---|
| `dim_studio` | studio | `studio_key` (md5 of code) | SCD1 (static master) |
| `dim_channel` | conformed channel | `channel_key` | current view of SCD2 snapshot |
| `snap_channel_mapping` | raw label × version | `channel_raw` + validity | **SCD2** (check strategy) |
| `dim_member` | purchasing member | `member_key` | SCD1 |
| `dim_date` | day | `date_day` | n/a |
| `fct_funnel_daily` | lead-date × studio × channel | `funnel_row_key` | incremental, 7-day lookback |
| `fct_revenue` | sale | `sale_id` | full rebuild (small) |
| `fct_ad_spend` | day × conformed channel | (date_day, channel_key) | full rebuild |
| `fct_targets` | month × studio | (year_month, studio_key) | seed-derived |

## Cardinality

- `fct_funnel_daily` N:1 `dim_studio`, `dim_channel`, `dim_date`
- `fct_revenue` N:1 `dim_studio`, `dim_channel` (via lead), 1:1 `stg_sales`
- many raw channel labels N:1 conformed channel (`int_channel_mapping`)

## Late-arriving data

`fct_funnel_daily` is incremental (`delete+insert` on `funnel_row_key`) and
reprocesses a trailing `late_arrival_days` (default 7) window each run, so
paper-form sales entered days later still land in the right lead cohort.

## Lineage columns

Every raw table carries `_source_file` and `_loaded_at`; staging preserves
them, so any mart number can be traced to the CSV that produced it.
