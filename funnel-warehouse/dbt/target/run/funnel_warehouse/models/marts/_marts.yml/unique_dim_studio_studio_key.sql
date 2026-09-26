
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    studio_key as unique_field,
    count(*) as n_records

from "funnel"."main_marts"."dim_studio"
where studio_key is not null
group by studio_key
having count(*) > 1



  
  
      
    ) dbt_internal_test