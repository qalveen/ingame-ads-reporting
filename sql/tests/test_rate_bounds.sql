-- severity: error
-- description: all rates fall within [0, 1]
select title_id as key, 'fill_rate' as metric, fill_rate as value from mart_title_monthly where fill_rate not between 0 and 1
union all select title_id, 'sell_through_rate', sell_through_rate from mart_title_monthly where sell_through_rate not between 0 and 1
union all select campaign_id, 'video_completion_rate', video_completion_rate from mart_campaign_monthly where video_completion_rate not between 0 and 1
