-- stg_placements
-- Grain: one row per placement (inventory catalog maintained with Product Management).
select
    placement_id,
    placement_name,
    title_id,
    title_name,
    ad_format,
    cast(launch_date as date) as launch_date
from raw_placements
