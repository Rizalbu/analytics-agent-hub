
    
    

select
    sale_id as unique_field,
    count(*) as n_records

from "funnel"."main_marts"."fct_revenue"
where sale_id is not null
group by sale_id
having count(*) > 1


