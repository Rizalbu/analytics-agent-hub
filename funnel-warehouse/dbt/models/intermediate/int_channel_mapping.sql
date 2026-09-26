-- Current view of the SCD2 channel mapping snapshot:
-- raw label -> conformed channel + surrogate key.
select
    channel_raw,
    channel_name,
    channel_group,
    -- key from NAME only: channel_group is a mutable attribute (SCD2 demo
    -- remaps it); deriving the key from it would orphan historical facts
    {{ surrogate_key(["channel_name"]) }} as channel_key
from {{ ref('snap_channel_mapping') }}
where dbt_valid_to is null
