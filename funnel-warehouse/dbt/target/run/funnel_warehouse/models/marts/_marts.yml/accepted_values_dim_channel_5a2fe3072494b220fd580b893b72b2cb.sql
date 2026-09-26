
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        channel_group as value_field,
        count(*) as n_records

    from "funnel"."main_marts"."dim_channel"
    group by channel_group

)

select *
from all_values
where value_field not in (
    'paid_social','paid_search','paid_video','referral','organic','partner'
)



  
  
      
    ) dbt_internal_test