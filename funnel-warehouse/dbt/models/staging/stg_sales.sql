with src as (
    select * from {{ source('raw', 'sales') }}
),

typed as (
    select
        upper(trim(sale_id))             as sale_id,
        upper(trim(lead_id))             as lead_id,
        upper(trim(plan_code))           as plan_code,
        try_cast(sold_at as date)        as sold_date,
        try_cast(amount as bigint)       as amount,
        lower(trim(payment_status))      as payment_status,
        _source_file,
        _loaded_at
    from src
),

deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by sale_id
        order by _loaded_at, _source_file
    ) = 1
)

select * from deduped
