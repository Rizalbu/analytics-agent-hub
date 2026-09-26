
    
    

select
    funnel_row_key as unique_field,
    count(*) as n_records

from "funnel"."main_marts"."fct_funnel_daily"
where funnel_row_key is not null
group by funnel_row_key
having count(*) > 1


