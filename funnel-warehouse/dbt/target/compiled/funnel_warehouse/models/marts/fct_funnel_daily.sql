

-- Daily funnel counts, cohort-attributed to the LEAD's creation date
-- (docs/adr/001: downstream stages count against the lead date, so the
-- five columns are nested subsets and monotonicity is testable).
-- Incremental: reprocess a trailing window to absorb late-arriving rows.

with atomic as (
    select * from "funnel"."main_intermediate"."int_funnel_atomic"
    
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
    join "funnel"."main_marts"."dim_studio" s
        on a.studio_code = s.studio_code
    group by 1, 2, 3
)

select
    
    md5(concat_ws('||', date_day, studio_key, channel_key))
 as funnel_row_key,
    *
from agg