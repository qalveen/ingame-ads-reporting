-- severity: error
-- description: title-level paid impressions equal the sum of placement-level paid impressions
select t.title_id, t.paid_impressions, sum(p.paid_impressions) as placement_sum
from mart_title_monthly t join mart_placement_monthly p using (title_id)
group by 1, 2 having t.paid_impressions <> sum(p.paid_impressions)
