
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    member_key as unique_field,
    count(*) as n_records

from "funnel"."main_marts"."dim_member"
where member_key is not null
group by member_key
having count(*) > 1



  
  
      
    ) dbt_internal_test