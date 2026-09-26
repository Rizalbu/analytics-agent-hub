with src as (
    select * from {{ source('raw', 'bookings') }}
),

typed as (
    select
        upper(trim(booking_id))        as booking_id,
        upper(trim(lead_id))           as lead_id,
        try_cast(booked_at as date)    as booked_date,
        try_cast(trial_date as date)   as trial_date,
        lower(trim(booking_status))    as booking_status,
        _source_file,
        _loaded_at
    from src
),

deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by booking_id
        order by _loaded_at, _source_file
    ) = 1
)

select * from deduped
