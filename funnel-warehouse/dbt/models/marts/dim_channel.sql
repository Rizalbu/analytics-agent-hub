-- Conformed channel dimension: many raw labels collapse to one channel.
select distinct
    channel_key,
    channel_name,
    channel_group
from {{ ref('int_channel_mapping') }}
