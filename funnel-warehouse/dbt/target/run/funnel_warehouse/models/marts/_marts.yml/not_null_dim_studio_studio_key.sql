
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select studio_key
from "funnel"."main_marts"."dim_studio"
where studio_key is null



  
  
      
    ) dbt_internal_test