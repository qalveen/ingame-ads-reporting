-- severity: warn
-- description: campaigns pacing more than 10% off goal (flight-to-date)
select campaign_id, advertiser, round(pacing_pct_to_date, 3) as pacing_pct_to_date, pacing_status
from mart_campaign_monthly where pacing_status in ('UNDER-PACING', 'OVER-PACING')
