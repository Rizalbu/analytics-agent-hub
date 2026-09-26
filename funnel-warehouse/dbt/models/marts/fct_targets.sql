select
    t.month                       as year_month,
    s.studio_key,
    t.target_leads,
    t.target_visits,
    t.target_revenue
from {{ ref('monthly_targets') }} t
join {{ ref('dim_studio') }} s
    on t.studio_code = s.studio_code
