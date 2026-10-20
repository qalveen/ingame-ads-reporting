-- BigQuery landing tables for the A&S reporting warehouse.
-- Replace `your-project` with your GCP project ID.
create schema if not exists `your-project.as_raw`;
create schema if not exists `your-project.as_marts`;

create or replace table `your-project.as_raw.impressions` (
  impression_id      string    not null,
  event_ts           timestamp not null,
  title_id           string,
  platform           string,
  placement_id       string,
  campaign_id        string,
  creative_id        string,
  player_id          string,
  ad_format          string,
  pct_in_view        float64,
  in_view_ms         int64,
  video_duration_ms  float64,
  video_played_ms    float64,
  sdk_version        string
)
partition by date(event_ts)
cluster by title_id, campaign_id, placement_id
options (description = "Client ad-render telemetry. One row per beacon; may contain SDK retry duplicates.");

create or replace table `your-project.as_raw.ad_requests` (
  event_date       date,
  title_id         string,
  placement_id     string,
  ad_requests      int64,
  filled_requests  int64
)
partition by event_date;

create or replace table `your-project.as_raw.campaign_manifest` (
  campaign_id         string,
  advertiser          string,
  vertical            string,
  title_id            string,
  placement_ids       string,
  flight_start        date,
  flight_end          date,
  booked_impressions  int64,
  cpm_usd             float64,
  is_test             bool,
  sold_by             string
);

create or replace table `your-project.as_raw.adops_scope` (
  report_month       date,       -- one table, all months (vs. one CSV per month locally)
  campaign_id        string,
  advertiser         string,
  include_in_report  string,
  adops_note         string
);
