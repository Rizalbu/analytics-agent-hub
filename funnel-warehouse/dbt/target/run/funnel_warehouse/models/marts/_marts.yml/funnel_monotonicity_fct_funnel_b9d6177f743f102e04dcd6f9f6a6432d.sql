
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  

-- Business-rule contract: funnel stage counts must be non-increasing
-- left-to-right at every grain row. A violation means a stage definition
-- regressed (e.g. someone counted visits no longer tied to a lead cohort).
select *
from "funnel"."main_marts"."fct_funnel_daily"
where false

   or leads < qualified

   or qualified < booked

   or booked < visited

   or visited < purchased



  
  
      
    ) dbt_internal_test