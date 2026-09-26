
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_day
from "funnel"."main_marts"."fct_funnel_daily"
where date_day is null



  
  
      
    ) dbt_internal_test