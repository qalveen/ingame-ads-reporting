-- severity: warn
-- description: in-scope campaigns with zero delivery this month (check trafficking with AdOps)
select campaign_id, advertiser, adops_note from mart_campaign_monthly where impressions = 0
