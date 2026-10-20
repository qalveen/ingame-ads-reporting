-- mart_dq_summary
-- Grain: one row per data-quality check for the reporting month (feeds the DQ tab).
with p as (select * from params),
raw_m as (
    select count(*) as raw_rows
    from raw_impressions, p
    where cast(event_ts as date) between p.month_start and p.month_end
),
cls as (
    select impression_class, count(*) as n
    from int_impressions_classified, p
    where event_date between p.month_start and p.month_end
    group by 1
),
other as (
    select
        count(*) filter (where player_id is null) as null_player_rows,
        count(distinct campaign_id) filter (where impression_class = 'orphan') as orphan_campaign_ids
    from int_impressions_classified, p
    where event_date between p.month_start and p.month_end
),
dedup as (select (select raw_rows from raw_m) - (select sum(n) from cls) as dupes)
select 'Raw telemetry rows'                         as check_name, (select raw_rows from raw_m) as value, 'info' as status, 'All rows received for the month' as note
union all select 'Retry duplicates removed',        (select dupes from dedup), 'fixed', 'Same impression_id sent >1x by client SDK; first event kept'
union all select 'Paid in-flight impressions',      (select coalesce(sum(n),0) from cls where impression_class='paid_in_flight'), 'info', 'Reported + billable base'
union all select 'House impressions',               (select coalesce(sum(n),0) from cls where impression_class='house'), 'info', 'Filler creative; counted in fill, not in sold'
union all select 'Out-of-flight impressions',       (select coalesce(sum(n),0) from cls where impression_class='out_of_flight'), 'flag', 'Served outside booked flight - excluded, raise with AdOps/AdTech'
union all select 'Test-line impressions',           (select coalesce(sum(n),0) from cls where impression_class='test'), 'info', 'Excluded per AdOps scope'
union all select 'Orphan impressions (quarantined)', (select coalesce(sum(n),0) from cls where impression_class='orphan'), 'flag', 'campaign_id missing from manifest - confirm with AdOps'
union all select 'Orphan campaign IDs',             (select orphan_campaign_ids from other), 'flag', 'Distinct unknown campaign IDs'
union all select 'Null player_id rows',             (select null_player_rows from other), 'info', 'Counted in impressions, excluded from reach/frequency'
