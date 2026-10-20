-- severity: warn
-- description: telemetry vs ad-server fill differs by more than 2% (beacon loss or double-firing)
select placement_id, ad_server_filled, telemetry_impressions, round(telemetry_vs_adserver_pct, 4) as diff_pct
from mart_placement_monthly where abs(telemetry_vs_adserver_pct) > 0.02
