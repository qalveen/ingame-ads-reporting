# Running on BigQuery

Local runs use DuckDB so the project works with zero cloud setup. The SQL is written to port to BigQuery with a few syntax swaps.

## Load
```bash
bq query --use_legacy_sql=false < bigquery/ddl.sql
bq load --source_format=PARQUET your-project:as_raw.impressions data/raw/impressions.parquet
bq load --source_format=CSV --skip_leading_rows=1 your-project:as_raw.ad_requests data/raw/ad_requests.csv
bq load --source_format=CSV --skip_leading_rows=1 your-project:as_raw.campaign_manifest config/campaign_manifest.csv
```

## DuckDB → BigQuery translations
| DuckDB (this repo) | BigQuery |
|---|---|
| `date_diff('day', a, b)` | `date_diff(b, a, day)` |
| `count(*) filter (where x)` | `countif(x)` |
| `count(distinct c) filter (where x)` | `count(distinct if(x, c, null))` |
| `unnest(string_split(s, '\|'))` in select | `cross join unnest(split(s, '\|'))` |
| `greatest` / `least` | same (returns NULL if any arg is NULL in both) |
| `params` table | `declare month_start date default '2026-09-01';` or a dbt var |
| exact `count(distinct player_id)` | consider `approx_count_distinct` or HLL sketches at full scale |

## Cost notes
- Partition filter on `date(event_ts)` keeps monthly runs to ~1/12 of a year's scan.
- Clustering on `title_id, campaign_id, placement_id` matches every mart's group-by.
- Materialize `int_impressions_classified` as a partitioned table; marts read from it, not raw.
