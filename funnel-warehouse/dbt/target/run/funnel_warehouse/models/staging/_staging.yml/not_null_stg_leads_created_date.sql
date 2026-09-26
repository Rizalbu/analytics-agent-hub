
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select created_date
from "funnel"."main_staging"."stg_leads"
where created_date is null



  
  
      
    ) dbt_internal_test