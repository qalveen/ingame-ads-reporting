# Automation Log — Monthly Cycle

Baseline is a typical manual process (exports + spreadsheets), used to define requirements with AdTech.

| # | Step | Manual baseline | Now | Status |
|---|---|---|---|---|
| 1 | Pull telemetry per title | Query each studio table, export CSV | Single raw feed, `stg_impressions` | Automated |
| 2 | Remove duplicates | Manual pivot checks | `row_number()` dedup + `test_unique_impression_id` | Automated |
| 3 | Filter to AdOps-approved campaigns | Copy/paste list into VLOOKUP | `stg_adops_scope` join + scope tests | Automated |
| 4 | Prorate booked goals into month | Hand-calculated per campaign | `dim_campaign_month` | Automated |
| 5 | Cap billable at booked | Manual per campaign | Running-total window in `int_campaign_daily` | Automated |
| 6 | Viewability / VCR calc | Formula per tab | Defined once in `stg_impressions` | Automated |
| 7 | Reconcile totals across tabs | Eyeball sums | `test_*_reconcile` | Automated |
| 8 | Flag pacing issues | Conditional formatting by hand | `pacing_status` + `warn_pacing` + callouts | Automated |
| 9 | Format and publish workbook | ~9 tabs built by hand | `build_report.py` | Automated |
| 10 | Confirm scope with AdOps | Email thread | Scope CSV committed to repo | Semi-automated (human approval stays) |
| 11 | Mobile titles (ad server vs telemetry) | Not reported | `telemetry_vs_adserver_pct` + warning | Partial: needs mediation feed |

## Next automation candidates (AdTech requirements)
1. Land ad server exports directly in the warehouse (remove CSV hand-off).
2. AdOps scope via a form/sheet sync instead of a committed CSV.
3. Mobile mediation feed so mobile inventory reconciles at impression level.
4. Traffic-weighted goal proration (forecast-based) instead of straight-line.
