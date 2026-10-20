-- stg_adops_scope
-- Grain: one row per campaign AdOps reviewed for the reporting month.
select
    campaign_id,
    advertiser,
    upper(trim(include_in_report)) = 'Y' as include_in_report,
    coalesce(adops_note, '')             as adops_note
from raw_adops_scope
