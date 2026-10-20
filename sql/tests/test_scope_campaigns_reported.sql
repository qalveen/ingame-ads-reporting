-- severity: error
-- description: every campaign AdOps marked include=Y appears in the campaign report
select s.campaign_id from stg_adops_scope s
left join mart_campaign_monthly m using (campaign_id)
where s.include_in_report and m.campaign_id is null
