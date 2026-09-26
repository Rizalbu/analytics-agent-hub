
      
    

    create  table
      "funnel"."snapshots"."snap_channel_mapping"
  
    
    as (
      
    

    select *,
        md5(coalesce(cast(channel_raw as varchar ), '')
         || '|' || coalesce(cast(now()::timestamp as varchar ), '')
        ) as dbt_scd_id,
        now()::timestamp as dbt_updated_at,
        now()::timestamp as dbt_valid_from,
        
  
  coalesce(nullif(now()::timestamp, now()::timestamp), null)
  as dbt_valid_to
from (
        



-- SCD2 over the current-state mapping table: every remap (e.g. TikTok Ads
-- moving from paid_social to paid_video) is captured with validity windows.
-- Demo: scripts/demo_scd2.py mutates the mapping, then re-runs this snapshot.
select
    trim(channel_raw)    as channel_raw,
    trim(channel_name)   as channel_name,
    trim(channel_group)  as channel_group
from "funnel"."raw"."channel_mapping_current"

    ) sbq



    );
    
  
  