-- severity: error
-- description: campaign report total equals paid in-flight impressions for in-scope campaigns (no leakage)
with p as (select * from params),
src as (
    select count(*) as n from int_impressions_classified i
    join stg_adops_scope s using (campaign_id)
    cross join p
    where s.include_in_report and i.impression_class = 'paid_in_flight'
      and i.event_date between p.month_start and p.month_end
),
rpt as (select sum(impressions) as n from mart_campaign_monthly)
select src.n as source_total, rpt.n as report_total from src, rpt where src.n <> rpt.n
