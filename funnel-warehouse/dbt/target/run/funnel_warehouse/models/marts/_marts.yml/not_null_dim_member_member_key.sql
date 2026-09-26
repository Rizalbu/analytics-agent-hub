
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select member_key
from "funnel"."main_marts"."dim_member"
where member_key is null



  
  
      
    ) dbt_internal_test