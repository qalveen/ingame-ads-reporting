-- severity: warn
-- description: telemetry references campaign IDs missing from the AdOps manifest
with p as (select * from params)
select campaign_id, title_id, count(*) as impressions
from int_impressions_classified, p
where impression_class = 'orphan' and event_date between p.month_start and p.month_end
group by 1, 2
