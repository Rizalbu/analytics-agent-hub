
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select studio_code
from "funnel"."main_staging"."stg_leads"
where studio_code is null



  
  
      
    ) dbt_internal_test