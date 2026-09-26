-- Daily spend per CONFORMED channel (raw labels collapsed via mapping).
select
    sp.spend_date            as date_day,
    m.channel_key,
    sum(sp.spend)            as spend,
    sum(sp.impressions)      as impressions,
    sum(sp.clicks)           as clicks
from {{ ref('stg_ad_spend') }} sp
join {{ ref('int_channel_mapping') }} m
    on sp.channel_raw = m.channel_raw
group by 1, 2
