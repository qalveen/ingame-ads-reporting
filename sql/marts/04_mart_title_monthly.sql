-- mart_title_monthly
-- Grain: one row per title for the reporting month, with month-over-month deltas.
with p as (select * from params),
months as (
    select 'current' as period, month_start, month_end from p
    union all
    select 'prior',              prev_month_start, prev_month_end from p
),
req as (
    select m.period, r.title_id, sum(r.ad_requests) as ad_requests, sum(r.filled_requests) as ad_server_filled
    from stg_ad_requests r join months m on r.event_date between m.month_start and m.month_end
    group by 1, 2
),
imp as (
    select
        m.period,
        i.title_id,
        count(*) filter (where impression_class = 'paid_in_flight')                 as paid_impressions,
        count(*) filter (where impression_class = 'house')                          as house_impressions,
        count(*) filter (where impression_class = 'paid_in_flight' and is_viewable) as paid_viewable,
        count(distinct player_id) filter (where impression_class = 'paid_in_flight') as paid_unique_reach,
        count(*) filter (where impression_class = 'paid_in_flight' and player_id is not null) as paid_imps_with_player,
        count(distinct campaign_id) filter (where impression_class = 'paid_in_flight') as live_campaigns
    from int_impressions_classified i join months m on i.event_date between m.month_start and m.month_end
    group by 1, 2
),
rev as (
    select m.period, c.title_id, sum(d.billable_impressions / 1000.0 * c.cpm_usd) as revenue_usd
    from int_campaign_daily d
    join stg_campaign_manifest c using (campaign_id)
    join months m on d.event_date between m.month_start and m.month_end
    group by 1, 2
),
base as (
    select
        r.period, r.title_id,
        r.ad_requests, r.ad_server_filled,
        r.ad_server_filled / nullif(r.ad_requests, 0)         as fill_rate,
        i.paid_impressions, i.house_impressions,
        i.paid_impressions / nullif(r.ad_requests, 0)         as sell_through_rate,
        i.paid_viewable / nullif(i.paid_impressions, 0)       as viewability_rate,
        i.paid_unique_reach,
        i.paid_imps_with_player / nullif(i.paid_unique_reach, 0) as avg_frequency,
        i.live_campaigns,
        round(coalesce(v.revenue_usd, 0), 2)                  as revenue_usd,
        coalesce(v.revenue_usd, 0) / nullif(i.paid_impressions, 0) * 1000 as ecpm_usd
    from req r
    left join imp i using (period, title_id)
    left join rev v using (period, title_id)
)
select
    t.title_id,
    pl.title_name,
    c.ad_requests,
    c.fill_rate,
    c.paid_impressions,
    c.house_impressions,
    c.sell_through_rate,
    c.viewability_rate,
    c.paid_unique_reach,
    c.avg_frequency,
    c.live_campaigns,
    c.revenue_usd,
    c.ecpm_usd,
    c.paid_impressions / nullif(pr.paid_impressions, 0) - 1  as paid_impressions_mom,
    c.revenue_usd      / nullif(pr.revenue_usd, 0) - 1       as revenue_mom,
    c.viewability_rate - pr.viewability_rate                 as viewability_mom_pts,
    c.sell_through_rate - pr.sell_through_rate               as sell_through_mom_pts
from (select distinct title_id from stg_placements) t
join (select distinct title_id, title_name from stg_placements) pl using (title_id)
left join base c  on c.title_id = t.title_id  and c.period = 'current'
left join base pr on pr.title_id = t.title_id and pr.period = 'prior'
order by t.title_id
