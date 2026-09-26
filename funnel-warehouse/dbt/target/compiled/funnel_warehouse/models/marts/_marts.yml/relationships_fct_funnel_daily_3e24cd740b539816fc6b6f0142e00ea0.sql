
    
    

with child as (
    select channel_key as from_field
    from "funnel"."main_marts"."fct_funnel_daily"
    where channel_key is not null
),

parent as (
    select channel_key as to_field
    from "funnel"."main_marts"."dim_channel"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


