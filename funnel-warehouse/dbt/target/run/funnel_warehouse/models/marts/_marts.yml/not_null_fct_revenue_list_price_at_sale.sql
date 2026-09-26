
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select list_price_at_sale
from "funnel"."main_marts"."fct_revenue"
where list_price_at_sale is null



  
  
      
    ) dbt_internal_test