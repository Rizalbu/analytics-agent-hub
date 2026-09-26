



-- SCD2 over the current-state mapping table: every remap (e.g. TikTok Ads
-- moving from paid_social to paid_video) is captured with validity windows.
-- Demo: scripts/demo_scd2.py mutates the mapping, then re-runs this snapshot.
select
    trim(channel_raw)    as channel_raw,
    trim(channel_name)   as channel_name,
    trim(channel_group)  as channel_group
from "funnel"."raw"."channel_mapping_current"
