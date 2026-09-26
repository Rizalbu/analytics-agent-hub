-- One row per purchasing member. Deliberately PII-free:
-- name/phone exist only in staging (see docs/adr/001 privacy note).
select
    {{ surrogate_key(["f.lead_id"]) }}        as member_key,
    f.lead_id,
    f.created_date                            as lead_date,
    f.sold_date                               as joined_date,
    f.plan_code                               as first_plan_code,
    s.studio_key                              as home_studio_key,
    f.channel_key                             as acquisition_channel_key
from {{ ref('int_funnel_atomic') }} f
join {{ ref('dim_studio') }} s
    on f.studio_code = s.studio_code
where f.is_purchased
