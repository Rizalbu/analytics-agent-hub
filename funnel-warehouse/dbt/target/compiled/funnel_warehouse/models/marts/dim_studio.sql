select
    
    md5(concat_ws('||', studio_code))
 as studio_key,
    studio_code,
    studio_name,
    city,
    open_date,
    capacity_tier
from "funnel"."main_seeds"."studio_master"