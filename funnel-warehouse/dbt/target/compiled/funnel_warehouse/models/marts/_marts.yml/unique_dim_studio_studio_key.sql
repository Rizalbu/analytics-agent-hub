
    
    

select
    studio_key as unique_field,
    count(*) as n_records

from "funnel"."main_marts"."dim_studio"
where studio_key is not null
group by studio_key
having count(*) > 1


