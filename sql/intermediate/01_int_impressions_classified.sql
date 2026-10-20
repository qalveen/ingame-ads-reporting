-- int_impressions_classified
-- Grain: one row per unique impression. Classifies every impression so nothing is silently dropped:
--   paid_in_flight  -> counted in reporting + billing
--   out_of_flight   -> served outside booked flight (ad server issue; not billable)
--   house           -> house / filler creative
--   test            -> QA lines (excluded per AdOps)
--   orphan          -> campaign_id not in the manifest (quarantined)
select
    i.*,
    m.advertiser,
    m.flight_start,
    m.flight_end,
    m.is_test,
    case
        when i.campaign_id like 'HOUSE-%'                          then 'house'
        when m.campaign_id is null                                 then 'orphan'
        when m.is_test                                             then 'test'
        when i.event_date not between m.flight_start and m.flight_end then 'out_of_flight'
        else 'paid_in_flight'
    end as impression_class
from stg_impressions i
left join stg_campaign_manifest m using (campaign_id)
