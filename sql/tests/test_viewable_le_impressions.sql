-- severity: error
-- description: viewable impressions can never exceed impressions
select campaign_id as key, impressions, viewable_impressions from mart_campaign_monthly where viewable_impressions > impressions
union all
select placement_id, paid_impressions, null from mart_placement_monthly where viewability_rate > 1
