-- stg_campaign_manifest
-- Grain: one row per booked campaign (AdOps trafficking sheet).
select
    campaign_id,
    advertiser,
    vertical,
    title_id,
    placement_ids,
    cast(flight_start as date)                         as flight_start,
    cast(flight_end   as date)                         as flight_end,
    date_diff('day', cast(flight_start as date), cast(flight_end as date)) + 1 as flight_days,
    cast(booked_impressions as bigint)                 as booked_impressions,
    cast(cpm_usd as double)                            as cpm_usd,
    cast(is_test as boolean)                           as is_test,
    sold_by
from raw_campaign_manifest
