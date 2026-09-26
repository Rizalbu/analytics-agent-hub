select
    {{ surrogate_key(["studio_code"]) }} as studio_key,
    studio_code,
    studio_name,
    city,
    open_date,
    capacity_tier
from {{ ref('studio_master') }}
