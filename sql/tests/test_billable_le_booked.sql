-- severity: error
-- description: cumulative billable impressions never exceed the booked goal
select d.campaign_id, sum(d.billable_impressions) as billable, m.booked_impressions
from int_campaign_daily d join stg_campaign_manifest m using (campaign_id)
group by 1, 3 having sum(d.billable_impressions) > m.booked_impressions
