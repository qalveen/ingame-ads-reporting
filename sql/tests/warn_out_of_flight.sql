-- severity: warn
-- description: impressions served outside the booked flight window
with p as (select * from params)
select campaign_id, min(event_date) as first_day, max(event_date) as last_day, count(*) as impressions
from int_impressions_classified, p
where impression_class = 'out_of_flight' and event_date between p.month_start and p.month_end
group by 1
