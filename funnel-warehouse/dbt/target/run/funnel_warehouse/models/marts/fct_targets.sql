
    

    create  table
      "funnel"."main_marts"."fct_targets__dbt_tmp"
  
    
    as (
      select
    t.month                       as year_month,
    s.studio_key,
    t.target_leads,
    t.target_visits,
    t.target_revenue
from "funnel"."main_seeds"."monthly_targets" t
join "funnel"."main_marts"."dim_studio" s
    on t.studio_code = s.studio_code
    );
    
  