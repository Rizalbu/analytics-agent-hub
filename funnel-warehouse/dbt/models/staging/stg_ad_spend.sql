-- NOTE: dedupe happens BEFORE typing here. Combining the QUALIFY window and
-- try_cast(parse_money(...)) in one projection trips a DuckDB 1.5.x CTAS
-- bug that eagerly casts the raw 'Rp 1.250.000' strings. Deduping on raw
-- columns first is equivalent (same grain) and sidesteps it.

with deduped as (
    -- same channel label can never legitimately appear twice per day
    select *
    from {{ source('raw', 'ad_spend') }}
    qualify row_number() over (
        partition by spend_date, channel_raw
        order by _loaded_at
    ) = 1
)

select
    try_cast(spend_date as date)      as spend_date,
    trim(channel_raw)                 as channel_raw,
    {{ parse_money('spend_raw') }}    as spend,
    try_cast(impressions as bigint)   as impressions,
    try_cast(clicks as bigint)        as clicks,
    _source_file,
    _loaded_at
from deduped
