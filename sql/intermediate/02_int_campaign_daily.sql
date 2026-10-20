-- int_campaign_daily
-- Grain: campaign x day (paid, in-flight only, all available history).
-- Billable impressions are capped at booked using a running total over the flight.
with daily as (
    select
        campaign_id,
        event_date,
        count(*)                                   as impressions,
        count(*) filter (where is_viewable)        as viewable_impressions
    from int_impressions_classified
    where impression_class = 'paid_in_flight'
    group by 1, 2
),
running as (
    select
        d.*,
        m.booked_impressions,
        sum(d.impressions) over (
            partition by d.campaign_id order by d.event_date
            rows between unbounded preceding and current row
        ) as cum_impressions
    from daily d
    join stg_campaign_manifest m using (campaign_id)
)
select
    campaign_id,
    event_date,
    impressions,
    viewable_impressions,
    cum_impressions,
    -- only bill up to the booked goal; over-delivery is make-good / bonus
    greatest(0, least(impressions, booked_impressions - (cum_impressions - impressions))) as billable_impressions
from running
