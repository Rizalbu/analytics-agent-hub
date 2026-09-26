
    
    

with child as (
    select booking_id as from_field
    from "funnel"."main_staging"."stg_visits"
    where booking_id is not null
),

parent as (
    select booking_id as to_field
    from "funnel"."main_staging"."stg_bookings"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


