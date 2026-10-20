-- stg_ad_requests
-- Grain: one row per placement per day (ad server log export).
select
    cast(event_date as date)          as event_date,
    title_id,
    placement_id,
    cast(ad_requests as bigint)       as ad_requests,
    cast(filled_requests as bigint)   as filled_requests
from raw_ad_requests
