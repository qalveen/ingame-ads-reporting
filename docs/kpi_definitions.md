# KPI Definitions

_Generated from `config/kpi_definitions.yml` by `src/render_docs.py`. Edit the YAML, not this file._

| KPI | Formula | Source model | Notes |
|---|---|---|---|
| Ad requests (avails) | `count of ad requests logged by the ad server` | `stg_ad_requests.ad_requests` | Proxy for available inventory. Requests that never render are not avails. |
| Fill rate | `ad_server_filled / ad_requests` | `mart_placement_monthly, mart_title_monthly` | Includes house fills. Ad-server count, not client telemetry. |
| Paid impressions | `count of de-duplicated impressions where impression_class = 'paid_in_flight'` | `int_impressions_classified` | Excludes house, test, orphan and out-of-flight impressions. |
| Sell-through rate | `paid_impressions / ad_requests` | `mart_placement_monthly, mart_title_monthly` | Share of avails sold to paying advertisers. |
| Viewable impressions | `display: pct_in_view >= 50 AND in_view_ms >= 1000; video: pct_in_view >= 50 AND in_view_ms >= 2000` | `stg_impressions.is_viewable` | MRC viewability standard applied to in-game client measurement. |
| Viewability rate | `viewable_impressions / paid_impressions` | `marts` | All impressions are measured in-client, so measured rate = 100%. |
| Unique reach | `count(distinct player_id) over the reporting month` | `marts` | Exact distinct count, not additive across titles or months. Null player_id rows excluded. |
| Average frequency | `impressions_with_player / unique_reach` | `marts` | Numerator excludes null player_id rows so the ratio is consistent. |
| Video completion rate (VCR) | `video_completes / video_starts, complete = video_played_ms >= video_duration_ms` | `mart_campaign_monthly, mart_placement_monthly` | Quartile flags (25/50/75%) available in stg_impressions. |
| Expected impressions (month) | `booked_impressions * flight_days_in_month / flight_days` | `dim_campaign_month` | Straight-line proration. Traffic-weighted proration is a planned enhancement. |
| Delivery % (month) | `impressions / expected_impressions_month` | `mart_campaign_monthly` | Month-only view. Use flight-to-date pacing for status. |
| Pacing % (flight-to-date) | `delivered_to_date / (booked_impressions * flight_days_elapsed / flight_days)` | `mart_campaign_monthly` | Status: < 90% UNDER-PACING, > 110% OVER-PACING, 0 impressions NO DELIVERY. |
| Billable impressions | `daily impressions capped so running total over the flight never exceeds booked (window function)` | `int_campaign_daily.billable_impressions` | Over-delivery is treated as bonus / make-good, not billed. |
| Revenue (USD) | `billable_impressions / 1000 * cpm_usd` | `mart_campaign_monthly, mart_title_monthly` | Recognized on billable delivery in the month. |
| eCPM (USD) | `revenue_usd / paid_impressions * 1000` | `mart_title_monthly` | Effective yield per thousand paid impressions, after capping. |
| Telemetry vs ad-server discrepancy | `(telemetry_impressions - ad_server_filled) / ad_server_filled` | `mart_placement_monthly` | > 2% absolute flagged. Negative = client beacons lost; positive = double-firing. |
