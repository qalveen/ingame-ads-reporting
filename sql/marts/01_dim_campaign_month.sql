-- dim_campaign_month
-- Grain: one row per campaign reviewed by AdOps for the reporting month.
-- Prorates the booked goal into the month and to-date (straight-line across flight days).
select
    s.campaign_id,
    coalesce(m.advertiser, s.advertiser)                    as advertiser,
    m.vertical,
    m.title_id,
    m.placement_ids,
    m.sold_by,
    m.flight_start,
    m.flight_end,
    m.flight_days,
    m.booked_impressions,
    m.cpm_usd,
    s.include_in_report,
    s.adops_note,
    -- days of the flight that fall inside the reporting month
    greatest(0, date_diff('day', greatest(m.flight_start, p.month_start),
                                 least(m.flight_end, p.month_end)) + 1)          as flight_days_in_month,
    -- days of the flight elapsed as of month end
    greatest(0, date_diff('day', m.flight_start, least(m.flight_end, p.month_end)) + 1) as flight_days_elapsed,
    m.booked_impressions * flight_days_in_month / m.flight_days               as expected_impressions_month,
    m.booked_impressions * flight_days_elapsed  / m.flight_days               as expected_impressions_to_date
from stg_adops_scope s
cross join params p
left join stg_campaign_manifest m using (campaign_id)
