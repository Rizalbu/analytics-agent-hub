
    

    create  table
      "funnel"."main_staging"."stg_leads__dbt_tmp"
  
    
    as (
      with src as (
    select * from "funnel"."raw"."leads"
),

typed as (
    select
        upper(trim(lead_id))                          as lead_id,
        upper(trim(studio_code))                      as studio_code,
        trim(channel_raw)                             as channel_raw,
        
    coalesce(
        try_strptime(created_at_raw, '%Y-%m-%d'),
        try_strptime(created_at_raw, '%d/%m/%Y'),
        try_strptime(created_at_raw, '%d-%b-%Y')
    )::date
      as created_date,
        trim(full_name)                               as full_name,
        regexp_replace(trim(phone), '[^0-9]', '', 'g') as phone,
        lower(trim(status))                           as status,
        _source_file,
        _loaded_at
    from src
),

-- exact duplicate rows exist in the drops; keep one deterministically
deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by lead_id
        order by _loaded_at, _source_file
    ) = 1
)

select * from deduped
    );
    
  