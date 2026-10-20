-- stg_campaign_placements
-- Grain: one row per campaign x placement (manifest stores placements pipe-delimited).
select
    campaign_id,
    unnest(string_split(placement_ids, '|')) as placement_id
from stg_campaign_manifest
