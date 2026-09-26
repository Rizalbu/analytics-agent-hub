-- Calendar spine covering the generated horizon.
with spine as (
    select unnest(generate_series(
        date '2025-01-01', date '2026-12-31', interval 1 day
    ))::date as date_day
)

select
    date_day,
    extract(year from date_day)::int          as year,
    extract(month from date_day)::int         as month,
    strftime(date_day, '%Y-%m')               as year_month,
    extract(isodow from date_day)::int        as iso_weekday,
    extract(isodow from date_day) in (6, 7)   as is_weekend,
    date_trunc('month', date_day)::date       as month_start
from spine
