-- severity: error
-- description: unique reach can never exceed impressions
select campaign_id, impressions, unique_reach from mart_campaign_monthly where unique_reach > impressions
