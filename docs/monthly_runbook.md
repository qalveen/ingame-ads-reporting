# Monthly Reporting Runbook

Target: report published by business day 3 of the following month.

| Day | Step | Owner | Command / artifact |
|---|---|---|---|
| BD-2 | Send AdOps the draft campaign list (all flights overlapping the month) | A&S Analyst | `config/campaign_manifest.csv` filtered to month |
| BD 1 | AdOps confirms include/exclude + notes; commit scope file | AdOps → Analyst | `config/adops_scope_YYYY-MM.csv` |
| BD 1 | Confirm any new placements with Product Mgmt; add to catalog | PM → Analyst | `config/titles.yml` |
| BD 2 | Run pipeline | Automated (CI) or Analyst | `make report MONTH=YYYY-MM` |
| BD 2 | Review `FAIL` tests (publication blocked) and `WARN` tests | Analyst | `output/YYYY-MM/run_log.json`, Data Quality tab |
| BD 2 | Raise warnings: orphans/zero delivery → AdOps; out-of-flight/discrepancy → AdTech | Analyst | Ticket per warning |
| BD 3 | Publish report + dashboard refresh; note any restatements | Analyst | `output/YYYY-MM/AS_Inventory_Report_YYYY-MM.xlsx` |

## Triage guide for warnings
| Warning | Likely cause | Action |
|---|---|---|
| warn_zero_delivery | Line booked but not trafficked, or creative rejected | AdOps confirms trafficking; keep row in report with note |
| warn_orphan_campaigns | Line trafficked in ad server before manifest update | AdOps adds to manifest; rerun |
| warn_out_of_flight | Ad server end date mis-set | AdTech fixes; impressions stay excluded from billing |
| warn_source_discrepancy | Beacon loss (negative) or double-firing (positive) | AdTech/studio telemetry investigates by SDK version |
| warn_pacing | Goal or frequency-cap mis-set, inventory shortfall | AdOps adjusts; Sales notified if make-good likely |

## Restatements
If a prior month changes after publication, rerun with the same `--month`, diff `run_log.json`, and add a restatement note to the next report's Summary.
