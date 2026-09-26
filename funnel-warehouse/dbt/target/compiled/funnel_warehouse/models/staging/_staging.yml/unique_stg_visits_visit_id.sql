
    
    

select
    visit_id as unique_field,
    count(*) as n_records

from "funnel"."main_staging"."stg_visits"
where visit_id is not null
group by visit_id
having count(*) > 1


