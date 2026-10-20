"""
Monthly A&S inventory reporting pipeline.

    python src/run_pipeline.py --month 2026-09            # build models, run tests, publish report
    python src/run_pipeline.py --month 2026-09 --generate # regenerate synthetic raw data first

Steps
  1. load raw feeds (telemetry, ad server, manifest, AdOps scope, placement catalog)
  2. build staging -> intermediate -> mart models (sql/, run in filename order)
  3. run data tests (sql/tests): any `error` failure stops publication
  4. publish the Excel report + charts to output/<month>/
  5. write a run log (row counts, test results, timings) for auditability
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"
LAYERS = ["staging", "intermediate", "marts"]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def month_bounds(month: str) -> dict:
    start = pd.Timestamp(f"{month}-01")
    end = start + pd.offsets.MonthEnd(0)
    prev_start = start - pd.offsets.MonthBegin(1)
    prev_end = start - pd.Timedelta(days=1)
    return {k: v.date() for k, v in dict(month_start=start, month_end=end,
                                          prev_month_start=prev_start, prev_month_end=prev_end).items()}


def load_raw(con: duckdb.DuckDBPyConnection, month: str) -> None:
    scope = ROOT / f"config/adops_scope_{month}.csv"
    if not scope.exists():
        sys.exit(f"Missing AdOps scope file: {scope}\n"
                 "Align with AdOps on in-scope campaigns before running the monthly report.")
    con.execute(f"create or replace view raw_impressions as select * from read_parquet('{ROOT / 'data/raw/impressions.parquet'}')")
    con.execute(f"create or replace view raw_ad_requests as select * from read_csv_auto('{ROOT / 'data/raw/ad_requests.csv'}')")
    con.execute(f"create or replace view raw_campaign_manifest as select * from read_csv_auto('{ROOT / 'config/campaign_manifest.csv'}')")
    con.execute(f"create or replace view raw_adops_scope as select * from read_csv_auto('{scope}', all_varchar=true)")

    cfg = yaml.safe_load((ROOT / "config/titles.yml").read_text())
    placements = pd.DataFrame([{**p, "title_id": t["title_id"], "title_name": t["title_name"]}
                               for t in cfg["titles"] for p in t["placements"]])
    con.register("placements_df", placements)
    con.execute("create or replace table raw_placements as select * from placements_df")

    b = month_bounds(month)
    con.execute("create or replace table params as select "
                f"date '{b['month_start']}' as month_start, date '{b['month_end']}' as month_end, "
                f"date '{b['prev_month_start']}' as prev_month_start, date '{b['prev_month_end']}' as prev_month_end")


def build_models(con: duckdb.DuckDBPyConnection) -> list[dict]:
    built = []
    for layer in LAYERS:
        for f in sorted((SQL / layer).glob("*.sql")):
            name = re.sub(r"^\d+_", "", f.stem)
            t0 = time.time()
            con.execute(f"create or replace table {name} as\n{f.read_text()}")
            rows = con.execute(f"select count(*) from {name}").fetchone()[0]
            built.append(dict(layer=layer, model=name, rows=rows, seconds=round(time.time() - t0, 2)))
            log(f"  built {layer}.{name:<32} {rows:>10,} rows")
    return built


def run_tests(con: duckdb.DuckDBPyConnection) -> list[dict]:
    results = []
    for f in sorted((SQL / "tests").glob("*.sql")):
        text = f.read_text()
        sev = re.search(r"--\s*severity:\s*(\w+)", text).group(1)
        desc = re.search(r"--\s*description:\s*(.+)", text).group(1).strip()
        df = con.execute(text).df()
        status = "PASS" if df.empty else ("FAIL" if sev == "error" else "WARN")
        results.append(dict(test=f.stem, severity=sev, status=status, failing_rows=len(df),
                            description=desc, sample=df.head(5).astype(str).to_dict("records")))
        log(f"  {status:<4} {f.stem} ({len(df)} rows)")
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True, help="Reporting month, YYYY-MM")
    ap.add_argument("--generate", action="store_true", help="Regenerate synthetic raw data")
    ap.add_argument("--force-publish", action="store_true", help="Publish even if error tests fail")
    args = ap.parse_args()

    t_start = time.time()
    if args.generate:
        log("Generating synthetic raw data")
        sys.path.insert(0, str(ROOT / "src"))
        from generate_data import build
        build()

    con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"))
    log(f"Loading raw feeds for {args.month}")
    load_raw(con, args.month)
    log("Building models")
    models = build_models(con)
    log("Running data tests")
    tests = run_tests(con)

    failed = [t for t in tests if t["status"] == "FAIL"]
    out_dir = ROOT / "output" / args.month
    out_dir.mkdir(parents=True, exist_ok=True)

    published = None
    if failed and not args.force_publish:
        log(f"BLOCKED: {len(failed)} error-severity test(s) failed — report not published")
    else:
        from build_report import build_report
        log("Publishing report")
        published = build_report(con, args.month, tests, out_dir)
        log(f"  wrote {published.relative_to(ROOT)}")

    run_log = dict(
        month=args.month, run_at=datetime.now().isoformat(timespec="seconds"),
        runtime_seconds=round(time.time() - t_start, 1),
        published=str(published.relative_to(ROOT)) if published else None,
        models=models, tests=tests,
    )
    (out_dir / "run_log.json").write_text(json.dumps(run_log, indent=2, default=str))
    log(f"Done in {run_log['runtime_seconds']}s — "
        f"{sum(t['status']=='PASS' for t in tests)} pass, "
        f"{sum(t['status']=='WARN' for t in tests)} warn, {len(failed)} fail")
    sys.exit(1 if failed and not args.force_publish else 0)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
