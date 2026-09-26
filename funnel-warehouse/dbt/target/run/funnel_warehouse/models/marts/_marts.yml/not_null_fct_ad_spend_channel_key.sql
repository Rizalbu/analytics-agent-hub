
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select channel_key
from "funnel"."main_marts"."fct_ad_spend"
where channel_key is null



  
  
      
    ) dbt_internal_test