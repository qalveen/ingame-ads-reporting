-- severity: error
-- description: campaigns AdOps excluded (or test lines) never appear in the report
select m.campaign_id from mart_campaign_monthly m
left join stg_adops_scope s using (campaign_id)
left join stg_campaign_manifest c using (campaign_id)
where coalesce(s.include_in_report, false) = false or c.is_test
