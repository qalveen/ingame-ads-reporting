-- stg_impressions
-- Grain: one row per unique impression_id. SDK retry duplicates collapsed to first event.
-- Applies MRC viewability standard and video quartile flags.
with ranked as (
    select
        *,
        row_number() over (partition by impression_id order by event_ts) as rn,
        count(*)     over (partition by impression_id)                   as copies
    from raw_impressions
)
select
    impression_id,
    cast(event_ts as timestamp)                       as event_ts,
    cast(event_ts as date)                            as event_date,
    title_id,
    platform,
    placement_id,
    campaign_id,
    creative_id,
    player_id,
    ad_format,
    pct_in_view,
    in_view_ms,
    video_duration_ms,
    video_played_ms,
    sdk_version,
    -- MRC: >=50% of pixels in view for >=1s (display) / >=2s continuous (video)
    case
        when ad_format = 'display' then pct_in_view >= 50 and in_view_ms >= 1000
        when ad_format = 'video'   then pct_in_view >= 50 and in_view_ms >= 2000
    end                                               as is_viewable,
    ad_format = 'video'                               as is_video_start,
    ad_format = 'video' and video_played_ms >= 0.25 * video_duration_ms as reached_q1,
    ad_format = 'video' and video_played_ms >= 0.50 * video_duration_ms as reached_mid,
    ad_format = 'video' and video_played_ms >= 0.75 * video_duration_ms as reached_q3,
    ad_format = 'video' and video_played_ms >= video_duration_ms        as is_video_complete,
    copies > 1                                        as had_retry_duplicate
from ranked
where rn = 1
