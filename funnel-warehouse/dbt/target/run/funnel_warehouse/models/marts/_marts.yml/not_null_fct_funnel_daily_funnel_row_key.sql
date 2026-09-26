
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select funnel_row_key
from "funnel"."main_marts"."fct_funnel_daily"
where funnel_row_key is null



  
  
      
    ) dbt_internal_test