-- Month x city rollup powering the exec dashboard.
-- Metric definitions: docs/metric_definitions.md (single source of truth).

with funnel as (
    select
        d.year_month,
        s.city,
        sum(f.leads)      as leads,
        sum(f.qualified)  as qualified,
        sum(f.booked)     as booked,
        sum(f.visited)    as visited,
        sum(f.purchased)  as purchased
    from {{ ref('fct_funnel_daily') }} f
    join {{ ref('dim_date') }} d on f.date_day = d.date_day
    join {{ ref('dim_studio') }} s on f.studio_key = s.studio_key
    group by 1, 2
),

revenue as (
    select
        d.year_month,
        s.city,
        sum(r.amount) as revenue
    from {{ ref('fct_revenue') }} r
    join {{ ref('dim_date') }} d on r.sold_date = d.date_day
    join {{ ref('dim_studio') }} s on r.studio_key = s.studio_key
    group by 1, 2
),

spend as (
    -- ad platforms don't report spend per studio; allocate per city by
    -- that city's share of paid leads in the month (documented choice)
    select
        d.year_month,
        s.city,
        sum(
            sp_m.spend * f.leads / nullif(sp_m.month_paid_leads, 0)
        ) as spend_alloc
    from {{ ref('fct_funnel_daily') }} f
    join {{ ref('dim_date') }} d on f.date_day = d.date_day
    join {{ ref('dim_studio') }} s on f.studio_key = s.studio_key
    join {{ ref('dim_channel') }} c on f.channel_key = c.channel_key
    join (
        select d2.year_month, sum(sp.spend) as spend,
               sum(fl.leads) as month_paid_leads
        from {{ ref('fct_ad_spend') }} sp
        join {{ ref('dim_date') }} d2 on sp.date_day = d2.date_day
        join (
            select d3.year_month, f3.channel_key, sum(f3.leads) as leads
            from {{ ref('fct_funnel_daily') }} f3
            join {{ ref('dim_date') }} d3 on f3.date_day = d3.date_day
            group by 1, 2
        ) fl on d2.year_month = fl.year_month and sp.channel_key = fl.channel_key
        group by 1
    ) sp_m on d.year_month = sp_m.year_month
    where c.channel_group in ('paid_social', 'paid_search')
    group by 1, 2
),

targets as (
    select
        t.year_month,
        s.city,
        sum(t.target_leads)   as target_leads,
        sum(t.target_visits)  as target_visits,
        sum(t.target_revenue) as target_revenue
    from {{ ref('fct_targets') }} t
    join {{ ref('dim_studio') }} s on t.studio_key = s.studio_key
    group by 1, 2
)

select
    f.year_month,
    f.city,
    f.leads, f.qualified, f.booked, f.visited, f.purchased,
    round(f.qualified * 100.0 / nullif(f.leads, 0), 1)    as cr_lead_qualified_pct,
    round(f.booked * 100.0 / nullif(f.qualified, 0), 1)   as cr_qualified_booked_pct,
    round(f.visited * 100.0 / nullif(f.booked, 0), 1)     as cr_booked_visited_pct,
    round(f.purchased * 100.0 / nullif(f.visited, 0), 1)  as cr_visited_purchased_pct,
    r.revenue,
    round(sp.spend_alloc)                                  as paid_spend,
    round(sp.spend_alloc / nullif(f.purchased, 0))         as cac,
    round(r.revenue * 1.0 / nullif(sp.spend_alloc, 0), 2)  as roas,
    t.target_revenue,
    round(r.revenue * 100.0 / nullif(t.target_revenue, 0), 1) as revenue_attainment_pct
from funnel f
left join revenue r using (year_month, city)
left join spend sp using (year_month, city)
left join targets t using (year_month, city)
order by f.year_month, f.city
