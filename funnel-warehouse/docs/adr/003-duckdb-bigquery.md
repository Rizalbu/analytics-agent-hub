# ADR-003: DuckDB locally, BigQuery as the documented prod path

**Status:** accepted

## Decision

The repo runs end-to-end on DuckDB: zero cost, zero accounts, anyone can
clone and reproduce the 60-test build in ~3 minutes. That reproducibility
*is* the portfolio feature.

The BigQuery path is documented rather than wired:

- swap `profiles.yml` to the `dbt-bigquery` adapter
- `fct_funnel_daily`: add `partition_by={'field':'date_day','data_type':'date'}`
  and `cluster_by=['studio_key','channel_key']`; incremental strategy
  `insert_overwrite` replaces `delete+insert`
- seeds stay seeds; the loader becomes a GCS external-table or `bq load` step
- cost note: at this volume (~50 MB/year) BigQuery runs comfortably inside
  the free tier; partition pruning matters from ~10 GB upward

## Known engine quirk (documented honestly)

DuckDB 1.5.x mis-executes CTAS when a QUALIFY window and a
`try_cast(replace(...))` projection share one SELECT (it eagerly casts the
raw string). `stg_ad_spend` therefore dedupes on raw columns first, then
types instead, equivalent at this grain. See the model header comment.
