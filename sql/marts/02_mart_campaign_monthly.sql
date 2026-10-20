-- mart_campaign_monthly
-- Grain: one row per IN-SCOPE campaign for the reporting month (zero-delivery campaigns kept).
with p as (select * from params),
imps as (
    select *
    from int_impressions_classified, p
    where impression_class = 'paid_in_flight'
      and event_date between p.month_start and p.month_end
),
agg as (
    select
        campaign_id,
        count(*)                                                as impressions,
        count(*) filter (where is_viewable)                     as viewable_impressions,
        count(distinct player_id)                               as unique_reach,
        count(*) filter (where player_id is not null)           as impressions_with_player,
        count(*) filter (where is_video_start)                  as video_starts,
        count(*) filter (where is_video_complete)               as video_completes,
        count(distinct placement_id)                            as placements_delivered
    from imps
    group by 1
),
bill as (
    select d.campaign_id,
           sum(d.billable_impressions) filter (where d.event_date between p.month_start and p.month_end) as billable_impressions_month,
           sum(d.impressions)          filter (where d.event_date <= p.month_end)                       as delivered_to_date
    from int_campaign_daily d, p
    group by 1
)
select
    c.campaign_id,
    c.advertiser,
    c.vertical,
    c.title_id,
    c.placement_ids,
    c.sold_by,
    c.flight_start,
    c.flight_end,
    c.booked_impressions,
    c.cpm_usd,
    c.adops_note,
    round(c.expected_impressions_month)                               as expected_impressions_month,
    coalesce(a.impressions, 0)                                        as impressions,
    coalesce(a.viewable_impressions, 0)                               as viewable_impressions,
    a.viewable_impressions / nullif(a.impressions, 0)                 as viewability_rate,
    coalesce(a.unique_reach, 0)                                       as unique_reach,
    a.impressions_with_player / nullif(a.unique_reach, 0)             as avg_frequency,
    coalesce(a.video_starts, 0)                                       as video_starts,
    a.video_completes / nullif(a.video_starts, 0)                     as video_completion_rate,
    coalesce(a.impressions, 0) / nullif(c.expected_impressions_month, 0) as delivery_pct_month,
    coalesce(b.delivered_to_date, 0)                                  as delivered_to_date,
    round(c.expected_impressions_to_date)                             as expected_impressions_to_date,
    coalesce(b.delivered_to_date, 0) / nullif(c.expected_impressions_to_date, 0) as pacing_pct_to_date,
    coalesce(b.billable_impressions_month, 0)                         as billable_impressions,
    round(coalesce(b.billable_impressions_month, 0) / 1000.0 * c.cpm_usd, 2) as revenue_usd,
    case
        when coalesce(a.impressions, 0) = 0                                 then 'NO DELIVERY'
        when coalesce(b.delivered_to_date, 0) / nullif(c.expected_impressions_to_date, 0) < 0.90 then 'UNDER-PACING'
        when coalesce(b.delivered_to_date, 0) / nullif(c.expected_impressions_to_date, 0) > 1.10 then 'OVER-PACING'
        else 'ON PACE'
    end                                                               as pacing_status
from dim_campaign_month c
left join agg  a using (campaign_id)
left join bill b using (campaign_id)
where c.include_in_report
order by c.title_id, c.campaign_id
