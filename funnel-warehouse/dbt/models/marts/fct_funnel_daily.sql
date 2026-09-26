{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='funnel_row_key',
    )
}}

-- Daily funnel counts, cohort-attributed to the LEAD's creation date
-- (docs/adr/001: downstream stages count against the lead date, so the
-- five columns are nested subsets and monotonicity is testable).
-- Incremental: reprocess a trailing window to absorb late-arriving rows.

with atomic as (
    select * from {{ ref('int_funnel_atomic') }}
    {% if is_incremental() %}
    where created_date >= (
        select coalesce(max(date_day), date '1900-01-01')
               - interval '{{ var("late_arrival_days") }}' day
        from {{ this }}
    )
    {% endif %}
),

agg as (
    select
        created_date                       as date_day,
        s.studio_key,
        a.channel_key,
        count(*)                           as leads,
        count(*) filter (stage_qualified)  as qualified,
        count(*) filter (stage_booked)     as booked,
        count(*) filter (stage_visited)    as visited,
        count(*) filter (stage_purchased)  as purchased
    from atomic a
    join {{ ref('dim_studio') }} s
        on a.studio_code = s.studio_code
    group by 1, 2, 3
)

select
    {{ surrogate_key(["date_day", "studio_key", "channel_key"]) }} as funnel_row_key,
    *
from agg
