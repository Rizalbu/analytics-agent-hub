with src as (
    select * from "funnel"."raw"."visits"
),

typed as (
    select
        upper(trim(visit_id))            as visit_id,
        upper(trim(booking_id))          as booking_id,
        try_cast(visit_date as date)     as visit_date,
        
    lower(trim(attended_raw)) in ('y', 'yes', '1', 'true')
 as attended,
        _source_file,
        _loaded_at
    from src
),

deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by visit_id
        order by _loaded_at, _source_file
    ) = 1
)

select * from deduped