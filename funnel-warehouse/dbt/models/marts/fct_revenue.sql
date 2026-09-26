-- One row per membership sale, with the list price effective AT SALE TIME
-- (point-in-time join against the effective-dated price book seed).
-- discount_amount falling out negative would mean the join matched the
-- wrong price version, guarded by tests.

with sales as (
    select * from {{ ref('stg_sales') }}
),

atomic as (
    select lead_id, studio_code, channel_key
    from {{ ref('int_funnel_atomic') }}
),

priced as (
    select
        sa.sale_id,
        sa.lead_id,
        sa.plan_code,
        sa.sold_date,
        sa.amount,
        sa.payment_status,
        pb.plan_name,
        pb.monthly_price as list_price_at_sale,
        pb.monthly_price - sa.amount as discount_amount
    from sales sa
    left join {{ ref('price_book') }} pb
        on sa.plan_code = pb.plan_code
        and sa.sold_date between pb.valid_from and pb.valid_to
)

select
    p.*,
    s.studio_key,
    a.channel_key
from priced p
left join atomic a
    on p.lead_id = a.lead_id
left join {{ ref('dim_studio') }} s
    on a.studio_code = s.studio_code
