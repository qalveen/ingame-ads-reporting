# Data Dictionary

## Lineage

```
raw_impressions (client telemetry, parquet) ─┐
raw_campaign_manifest (AdOps sheet)  ────────┼─> stg_* ─> int_impressions_classified ─> int_campaign_daily
raw_adops_scope (monthly AdOps list) ────────┤                       │                          │
raw_ad_requests (ad server export) ──────────┤                       ▼                          ▼
raw_placements (Product catalog, YAML) ──────┘        mart_placement_monthly      mart_campaign_monthly
                                                      mart_title_monthly          mart_frequency_distribution
                                                      mart_daily_title            mart_dq_summary
```

## Raw sources

### raw_impressions — client telemetry, one event per ad render
| Column | Type | Description |
|---|---|---|
| impression_id | string | Client-generated ID. Can repeat when the SDK retries a beacon. |
| event_ts | timestamp (UTC) | Render time. |
| title_id | string | `PFC`, `GRD`, `DZL`, `HTL`. |
| platform | string | ps5, xbox, pc, ios, android. |
| placement_id | string | Inventory unit, joins to the placement catalog. |
| campaign_id | string | Joins to the AdOps manifest. `HOUSE-*` = house filler. |
| creative_id | string | Creative variant. |
| player_id | string | Pseudonymous player ID. Null when the client could not resolve it. |
| ad_format | string | `display` or `video`. |
| pct_in_view | float | Max % of creative pixels on screen. |
| in_view_ms | int | Continuous ms at ≥50% in view. |
| video_duration_ms | int | Video only. |
| video_played_ms | int | Video only. |
| sdk_version | string | `c*` console SDK, `m*` mobile SDK. |

### raw_campaign_manifest — booked campaigns (`config/campaign_manifest.csv`)
campaign_id, advertiser, vertical, title_id, placement_ids (pipe-delimited), flight_start, flight_end, booked_impressions, cpm_usd, is_test, sold_by

### raw_adops_scope — monthly reporting scope (`config/adops_scope_YYYY-MM.csv`)
campaign_id, advertiser, include_in_report (Y/N), adops_note

### raw_ad_requests — ad server export (`data/raw/ad_requests.csv`)
event_date, title_id, placement_id, ad_requests, filled_requests

### raw_placements — inventory catalog (`config/titles.yml`)
placement_id, placement_name, title_id, title_name, ad_format, base_daily_requests, launch_date

## Modeled tables

| Model | Grain | Purpose |
|---|---|---|
| stg_impressions | impression_id | De-duplicated telemetry + MRC viewability + video quartile flags |
| stg_campaign_manifest | campaign | Typed manifest + flight_days |
| stg_campaign_placements | campaign × placement | Unnests pipe-delimited placements |
| stg_placements | placement | Catalog incl. launch_date (new inventory detection) |
| stg_ad_requests | placement × day | Typed ad server counts |
| stg_adops_scope | campaign | Reporting month scope |
| int_impressions_classified | impression | Adds `impression_class`: paid_in_flight / out_of_flight / house / test / orphan |
| int_campaign_daily | campaign × day | Daily delivery + running total + **billable (capped at booked)** |
| dim_campaign_month | campaign | Booked goal prorated to month and to-date |
| mart_campaign_monthly | campaign | Campaign report rows (in-scope only, zero-delivery kept) |
| mart_placement_monthly | placement | Avails, fill, sell-through, viewability, telemetry vs ad-server gap |
| mart_title_monthly | title | Title KPIs with MoM |
| mart_frequency_distribution | title × bucket | Reach by exposure bucket |
| mart_daily_title | title × day | Trend + 7-day moving average |
| mart_dq_summary | check | Monthly DQ counts for the report |
