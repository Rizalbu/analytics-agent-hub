# ADR-002: Two SCD strategies, on purpose

**Status:** accepted

Two slowly-changing inputs are handled with two different mechanisms. The
contrast is deliberate and interview-ready.

## Price book: effective-dated source (no snapshot)

`seeds/price_book.csv` carries `valid_from`/`valid_to` because price changes
are *planned business events* announced ahead of time. The source of truth
already has validity windows, so snapshotting would only degrade them into
"when did dbt happen to run". `fct_revenue` does a point-in-time join
(`sold_date BETWEEN valid_from AND valid_to`); the
`assert_sale_price_sane` test proves every sale matched exactly one version
(July 2025 price increase is in the seed, so the join is exercised both sides).

## Channel mapping: dbt snapshot (check strategy)

Channel → group remaps are *unplanned drift* (marketing reclassifies TikTok
from paid_social to paid_video). The source is current-state only, so history
must be captured at observation time: `snap_channel_mapping`, strategy
`check` on (`channel_name`, `channel_group`), keyed by `channel_raw`.
`scripts/demo_scd2.py` performs a live remap and shows the resulting
validity windows.

## Lesson the demo taught (kept honest)

The first cut derived `channel_key` from `(channel_name, channel_group)`.
Running the remap demo then orphaned 3,858 historical fact rows, caught by
the `relationships` test, exactly as it should be. Surrogate keys must hang
off the *stable identity* (`channel_name`); mutable attributes belong in the
dimension/snapshot, never in the key.

## Rule of thumb encoded here

> If the source system knows the validity window, keep it (effective-dated).
> If only you can observe the change, snapshot it (SCD2).
