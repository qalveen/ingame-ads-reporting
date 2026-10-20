-- mart_placement_monthly
-- Grain: one row per placement for the reporting month. Inventory view: avails, fill, sell-through.
with p as (select * from params),
req as (
    select placement_id,
           sum(ad_requests)     as ad_requests,
           sum(filled_requests) as ad_server_filled
    from stg_ad_requests, p
    where event_date between p.month_start and p.month_end
    group by 1
),
imp as (
    select
        placement_id,
        count(*)                                                                  as telemetry_impressions,
        count(*) filter (where impression_class = 'paid_in_flight')               as paid_impressions,
        count(*) filter (where impression_class = 'house')                        as house_impressions,
        count(*) filter (where impression_class = 'paid_in_flight' and is_viewable) as paid_viewable,
        count(distinct player_id) filter (where impression_class = 'paid_in_flight') as paid_unique_reach,
        count(*) filter (where impression_class = 'paid_in_flight' and is_video_start)    as video_starts,
        count(*) filter (where impression_class = 'paid_in_flight' and is_video_complete) as video_completes
    from int_impressions_classified, p
    where event_date between p.month_start and p.month_end
    group by 1
)
select
    pl.title_id,
    pl.title_name,
    pl.placement_id,
    pl.placement_name,
    pl.ad_format,
    pl.launch_date,
    pl.launch_date between p.month_start and p.month_end         as is_new_inventory,
    coalesce(r.ad_requests, 0)                                   as ad_requests,
    coalesce(r.ad_server_filled, 0)                              as ad_server_filled,
    r.ad_server_filled / nullif(r.ad_requests, 0)                as fill_rate,
    coalesce(i.telemetry_impressions, 0)                         as telemetry_impressions,
    coalesce(i.paid_impressions, 0)                              as paid_impressions,
    coalesce(i.house_impressions, 0)                             as house_impressions,
    i.paid_impressions / nullif(r.ad_requests, 0)                as sell_through_rate,
    i.paid_viewable / nullif(i.paid_impressions, 0)              as viewability_rate,
    coalesce(i.paid_unique_reach, 0)                             as paid_unique_reach,
    i.video_completes / nullif(i.video_starts, 0)                as video_completion_rate,
    (i.telemetry_impressions - r.ad_server_filled) / nullif(r.ad_server_filled, 0) as telemetry_vs_adserver_pct
from stg_placements pl
cross join p
left join req r using (placement_id)
left join imp i using (placement_id)
order by pl.title_id, pl.placement_id
