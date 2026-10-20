-- severity: error
-- description: stg_impressions must have exactly one row per impression_id
select impression_id, count(*) as n from stg_impressions group by 1 having count(*) > 1
