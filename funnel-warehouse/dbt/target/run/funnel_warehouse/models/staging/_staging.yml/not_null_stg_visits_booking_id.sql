
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select booking_id
from "funnel"."main_staging"."stg_visits"
where booking_id is null



  
  
      
    ) dbt_internal_test