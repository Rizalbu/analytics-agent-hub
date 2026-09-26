-- One row per LEAD with funnel stage flags and dates.
-- Stage definitions are unified here and ONLY here (docs/adr/001):
--   qualified : status = 'qualified' OR the lead has a booking
--               (studios disagree on updating status; a booking is proof)
--   booked    : has a non-cancelled trial booking
--   visited   : attended = true on the trial visit
--   purchased : has a membership sale
-- Stages are nested subsets by construction -> funnel monotonicity holds.

with leads as (
    select * from {{ ref('stg_leads') }}
),

first_booking as (
    select *
    from {{ ref('stg_bookings') }}
    qualify row_number() over (partition by lead_id order by booked_date, booking_id) = 1
),

visits as (
    select * from {{ ref('stg_visits') }}
),

first_sale as (
    select *
    from {{ ref('stg_sales') }}
    qualify row_number() over (partition by lead_id order by sold_date, sale_id) = 1
),

joined as (
    select
        l.lead_id,
        l.studio_code,
        l.channel_raw,
        l.created_date,
        m.channel_key,
        m.channel_name,
        m.channel_group,

        (l.status = 'qualified' or b.booking_id is not null) as is_qualified,
        (b.booking_id is not null
            and b.booking_status != 'cancelled')             as is_booked,
        coalesce(v.attended, false)                          as is_visited,
        (s.sale_id is not null)                              as is_purchased,

        b.booking_id,
        b.trial_date,
        v.visit_date,
        s.sale_id,
        s.sold_date,
        s.plan_code,
        s.amount
    from leads l
    left join {{ ref('int_channel_mapping') }} m
        on l.channel_raw = m.channel_raw
    left join first_booking b
        on l.lead_id = b.lead_id
    left join visits v
        on b.booking_id = v.booking_id
    left join first_sale s
        on l.lead_id = s.lead_id
)

select
    *,
    -- enforce nesting: a purchase implies visit implies booking implies qualified
    is_qualified or is_booked or is_visited or is_purchased as stage_qualified,
    is_booked or is_visited or is_purchased                 as stage_booked,
    is_visited or is_purchased                              as stage_visited,
    is_purchased                                            as stage_purchased
from joined
