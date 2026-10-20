"""
Synthetic in-game ad telemetry generator.

Produces the three raw feeds the monthly A&S report depends on:
  data/raw/impressions.parquet       impression-level telemetry (game clients -> pipeline)
  data/raw/ad_requests.csv           daily ad-request / fill counts per placement (ad server)
  config/campaign_manifest.csv       booked campaigns (AdOps trafficking sheet)
  config/adops_scope_YYYY-MM.csv     AdOps-approved campaign list per reporting month

Realism built in:
  * per-title seasonality (launches, season drops, weekend uplift, diurnal curve)
  * engagement skew (heavy players see far more ads -> real frequency distributions)
  * traffic-proportional pacing with per-campaign under/over-delivery
  * new inventory launched mid-month (GRD-SKILLS-CHAL)
  * known data-quality defects: SDK retry duplicates, orphan campaign IDs,
    null player IDs, out-of-flight serving, a booked-but-never-trafficked campaign

All titles, advertisers, and numbers are fictional.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA_START = date(2026, 8, 1)
DATA_END = date(2026, 9, 30)          # telemetry available through end of reporting month

# --------------------------------------------------------------------------------------
# Campaign book (what AdOps trafficked). share = target share of placement avails.
# pace = delivery multiplier vs. goal (1.0 = on pace). Booked impressions are derived.
# --------------------------------------------------------------------------------------
CAMPAIGNS = [
    # id,         advertiser,          vertical,     title, placements,                            start,        end,          share, pace, cpm
    ("CMP-26-001", "Voltage Energy",    "beverage",   "PFC", ["PFC-LED-STADIUM", "PFC-KIT-SPONSOR"],   "2026-08-01", "2026-09-30", 0.25, 1.02, 12.0),
    ("CMP-26-002", "Summit Motors",     "auto",       "PFC", ["PFC-HALFTIME-VID"],                    "2026-08-15", "2026-10-15", 0.35, 0.78, 28.0),
    ("CMP-26-003", "Peak Athletic",     "apparel",    "PFC", ["PFC-KIT-SPONSOR"],                     "2026-09-01", "2026-10-31", 0.30, 1.05, 14.0),
    ("CMP-26-004", "Nimbus Streaming",  "media",      "PFC", ["PFC-LED-STADIUM"],                     "2026-09-20", "2026-10-20", 0.30, 1.00, 11.0),
    ("CMP-26-005", "Crisp Chips",       "cpg",        "GRD", ["GRD-ENDZONE"],                         "2026-08-10", "2026-09-10", 0.30, 1.00, 13.0),
    ("CMP-26-006", "Ironclad Insurance","finance",    "GRD", ["GRD-BROADCAST"],                       "2026-08-01", "2026-09-30", 0.40, 1.16, 30.0),
    ("CMP-26-007", "Orbit Wireless",    "telecom",    "GRD", ["GRD-MENU-BANNER"],                     "2026-09-01", "2026-09-30", 0.35, 0.97, 9.0),
    ("CMP-26-008", "Summit Motors",     "auto",       "GRD", ["GRD-ENDZONE", "GRD-BROADCAST"],        "2026-09-05", "2026-10-31", 0.25, 1.00, 22.0),
    ("CMP-26-009", "Peak Athletic",     "apparel",    "GRD", ["GRD-SKILLS-CHAL"],                     "2026-09-10", "2026-10-31", 0.45, 0.66, 18.0),
    ("CMP-26-010", "Halo Headphones",   "electronics","DZL", ["DZL-LOBBY-BILL"],                      "2026-08-01", "2026-08-31", 0.30, 1.00, 10.0),
    ("CMP-26-011", "Voltage Energy",    "beverage",   "DZL", ["DZL-LOBBY-BILL", "DZL-LOADING-VID"],   "2026-09-01", "2026-09-30", 0.30, 1.03, 15.0),
    ("CMP-26-012", "Nimbus Streaming",  "media",      "DZL", ["DZL-LOADING-VID"],                     "2026-08-20", "2026-09-25", 0.30, 0.88, 24.0),
    ("CMP-26-013", "Lumen Bank",        "finance",    "DZL", ["DZL-LOBBY-BILL"],                      "2026-09-15", "2026-10-15", 0.25, 1.00, 10.0),
    ("CMP-26-014", "FreshCart Grocery", "retail",     "HTL", ["HTL-REWARDED-VID"],                    "2026-08-01", "2026-09-30", 0.40, 1.00, 16.0),
    ("CMP-26-015", "Crisp Chips",       "cpg",        "HTL", ["HTL-INTERSTITIAL"],                    "2026-09-01", "2026-10-31", 0.35, 1.12, 8.0),
    ("CMP-26-016", "Orbit Wireless",    "telecom",    "HTL", ["HTL-REWARDED-VID"],                    "2026-09-10", "2026-10-10", 0.25, 0.90, 17.0),
    ("CMP-26-017", "Lumen Bank",        "finance",    "HTL", ["HTL-INTERSTITIAL"],                    "2026-08-01", "2026-08-31", 0.30, 1.00, 8.0),
    ("CMP-26-018", "Halo Headphones",   "electronics","PFC", ["PFC-HALFTIME-VID"],                    "2026-09-01", "2026-09-28", 0.25, 1.00, 26.0),
    ("CMP-26-019", "Ironclad Insurance","finance",    "DZL", ["DZL-LOADING-VID"],                     "2026-09-01", "2026-09-30", 0.20, 0.00, 25.0),  # booked, never trafficked
    ("CMP-26-T01", "INTERNAL QA",       "test",       "PFC", ["PFC-LED-STADIUM"],                     "2026-09-01", "2026-09-30", 0.03, 1.00, 0.0),   # test line
]
OUT_OF_FLIGHT_OVERRUN = {"CMP-26-018": 2}   # ad server kept serving 2 days past flight end

# Viewability / video behavior per placement
#   display: pct_in_view ~ Beta(a,b), in_view_ms ~ LogNormal(median, sigma)
#   video:   pct_in_view ~ Beta(a,b), completion probability, durations
PLACEMENT_BEHAVIOR = {
    "PFC-LED-STADIUM":  dict(a=6,  b=3,   med_ms=1800, sigma=0.7),
    "PFC-KIT-SPONSOR":  dict(a=4,  b=4,   med_ms=1200, sigma=0.8),
    "PFC-HALFTIME-VID": dict(a=15, b=1,   p_complete=0.62),
    "GRD-ENDZONE":      dict(a=6,  b=3.5, med_ms=1600, sigma=0.7),
    "GRD-BROADCAST":    dict(a=15, b=1,   p_complete=0.55),
    "GRD-MENU-BANNER":  dict(a=7,  b=2,   med_ms=3500, sigma=0.6),
    "GRD-SKILLS-CHAL":  dict(a=8,  b=2,   med_ms=5000, sigma=0.5),
    "DZL-LOBBY-BILL":   dict(a=5,  b=3,   med_ms=2500, sigma=0.7),
    "DZL-LOADING-VID":  dict(a=14, b=1.5, p_complete=0.48),
    "HTL-REWARDED-VID": dict(a=18, b=1,   p_complete=0.93),
    "HTL-INTERSTITIAL": dict(a=12, b=1.5, med_ms=4000, sigma=0.5),
}

DIURNAL = np.array([2, 1.5, 1, 0.8, 0.7, 0.8, 1.2, 1.8, 2.2, 2.5, 2.8, 3.2,
                    3.6, 3.8, 4.0, 4.4, 5.0, 5.8, 6.6, 7.2, 7.0, 6.0, 4.5, 3.0])
DIURNAL = DIURNAL / DIURNAL.sum()


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def decay_spike(day: date, event: date, peak: float, half_life: float) -> float:
    if day < event:
        return 0.0
    return peak * 0.5 ** ((day - event).days / half_life)


def seasonality(title_id: str, d: date) -> float:
    """Traffic multiplier per title/day (no noise)."""
    weekend = 1.25 if d.weekday() >= 5 else 1.0
    if title_id == "PFC":   # new edition launches 2026-09-26 (early access 09-23)
        m = 1.0 + decay_spike(d, date(2026, 9, 23), 0.8, 30) + decay_spike(d, date(2026, 9, 26), 1.4, 10)
    elif title_id == "GRD": # launched 2026-08-14, real-world season kickoff bump 09-10
        m = 0.7 + decay_spike(d, date(2026, 8, 14), 1.6, 12) + decay_spike(d, date(2026, 9, 10), 0.5, 20)
    elif title_id == "DZL": # season drops 08-05 and 09-16
        m = 0.85 + decay_spike(d, date(2026, 8, 5), 0.9, 6) + decay_spike(d, date(2026, 9, 16), 1.1, 6)
    else:                   # mobile: steady with mild growth, stronger weekend
        m = 1.0 + 0.004 * (d - DATA_START).days
        weekend = 1.15 if d.weekday() >= 5 else 1.0
    return m * weekend


def build(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    cfg = yaml.safe_load((ROOT / "config/titles.yml").read_text())
    titles = {t["title_id"]: t for t in cfg["titles"]}
    placements = {p["placement_id"]: {**p, "title_id": t["title_id"]}
                  for t in cfg["titles"] for p in t["placements"]}
    days = list(daterange(DATA_START, DATA_END))

    # ---- 1. ad requests per placement-day ------------------------------------------
    exp_req, act_req = {}, {}
    for pid, p in placements.items():
        launch = date.fromisoformat(str(p["launch_date"]))
        for d in days:
            e = p["base_daily_requests"] * seasonality(p["title_id"], d) if d >= launch else 0.0
            exp_req[(pid, d)] = e
            act_req[(pid, d)] = int(rng.poisson(e * rng.normal(1.0, 0.05))) if e > 0 else 0

    # ---- 2. manifest: booked impressions derived from expected avails over full flight
    def expected_over(pid, a, b):
        p = placements[pid]
        launch = date.fromisoformat(str(p["launch_date"]))
        return sum(p["base_daily_requests"] * seasonality(p["title_id"], d)
                   for d in daterange(max(a, launch), b))

    manifest_rows, line_goal = [], {}
    for cid, adv, vert, tid, pids, s, e, share, pace, cpm in CAMPAIGNS:
        s, e = date.fromisoformat(s), date.fromisoformat(e)
        avail = sum(expected_over(pid, s, e) for pid in pids)
        booked = int(round(share * avail, -3))
        manifest_rows.append(dict(
            campaign_id=cid, advertiser=adv, vertical=vert, title_id=tid,
            placement_ids="|".join(pids), flight_start=s, flight_end=e,
            booked_impressions=booked, cpm_usd=cpm,
            is_test=cid.endswith("T01"), sold_by=rng.choice(["Direct", "Programmatic Guaranteed"]),
        ))
        for pid in pids:
            line_goal[(cid, pid)] = dict(share=share, pace=pace, start=s, end=e)

    # ---- 3. allocate delivered impressions per placement-day -----------------------
    alloc = []   # (date, placement_id, campaign_id, n)
    req_rows = []
    for pid in placements:
        for d in days:
            req = act_req[(pid, d)]
            if req == 0:
                continue
            remaining = int(req * rng.uniform(0.985, 0.998))   # tiny tech-loss: requests that never render
            active = [(cid, g) for (cid, p2), g in line_goal.items() if p2 == pid
                      and g["start"] <= d <= g["end"] + timedelta(days=OUT_OF_FLIGHT_OVERRUN.get(cid, 0))]
            rng.shuffle(active)
            filled = 0
            for cid, g in active:
                goal = g["share"] * req * g["pace"] * rng.normal(1.0, 0.06)
                n = int(max(0, min(goal, remaining)))
                if n:
                    alloc.append((d, pid, cid, n))
                    remaining -= n
                    filled += n
            house = int(remaining * rng.uniform(0.6, 0.85))
            if house:
                alloc.append((d, pid, f"HOUSE-{placements[pid]['title_id']}", house))
                filled += house
            req_rows.append(dict(event_date=d, title_id=placements[pid]["title_id"],
                                 placement_id=pid, ad_requests=req, filled_requests=filled))

    # ---- 4. explode to impression rows ---------------------------------------------
    a = pd.DataFrame(alloc, columns=["event_date", "placement_id", "campaign_id", "n"])
    a["title_id"] = a["placement_id"].map(lambda x: placements[x]["title_id"])
    idx = np.repeat(np.arange(len(a)), a["n"].to_numpy())
    imp = a.iloc[idx].drop(columns="n").reset_index(drop=True)
    N = len(imp)

    # player assignment with engagement skew; platform fixed per player
    imp["player_id"] = None
    imp["platform"] = None
    for tid, t in titles.items():
        mask = (imp["title_id"] == tid).to_numpy()
        pool = t["player_pool"]
        w = rng.lognormal(0, 1.2, pool); w /= w.sum()
        plat = rng.choice(t["platforms"], size=pool,
                          p=[0.45, 0.30, 0.25] if len(t["platforms"]) == 3 else [0.55, 0.45])
        pick = rng.choice(pool, size=mask.sum(), p=w)
        imp.loc[mask, "player_id"] = np.char.add(f"{tid}-P", pick.astype(str).astype("U7"))
        imp.loc[mask, "platform"] = plat[pick]

    # timestamps (UTC) with diurnal curve
    hrs = rng.choice(24, size=N, p=DIURNAL)
    secs = hrs * 3600 + rng.integers(0, 3600, N)
    imp["event_ts"] = pd.to_datetime(imp["event_date"]) + pd.to_timedelta(secs, unit="s")

    # format, viewability, video
    imp["ad_format"] = imp["placement_id"].map(lambda x: placements[x]["ad_format"])
    pct = np.zeros(N); inview = np.zeros(N); dur = np.zeros(N); played = np.zeros(N)
    for pid, b in PLACEMENT_BEHAVIOR.items():
        m = (imp["placement_id"] == pid).to_numpy()
        k = m.sum()
        if not k:
            continue
        pct[m] = rng.beta(b["a"], b["b"], k) * 100
        if "p_complete" in b:
            dmx = rng.choice([15000, 30000], size=k, p=[0.6, 0.4])
            comp = rng.random(k) < b["p_complete"]
            pl = np.where(comp, dmx, rng.uniform(0, 1, k) * dmx)
            dur[m], played[m] = dmx, pl
            inview[m] = pl * rng.uniform(0.85, 1.0, k)
        else:
            inview[m] = rng.lognormal(np.log(b["med_ms"]), b["sigma"], k)
    imp["pct_in_view"] = pct.round(1)
    imp["in_view_ms"] = inview.astype(int)
    imp["video_duration_ms"] = np.where(imp["ad_format"] == "video", dur, np.nan)
    imp["video_played_ms"] = np.where(imp["ad_format"] == "video", played.astype(int), np.nan)
    imp["creative_id"] = imp["campaign_id"] + "-CR" + rng.integers(1, 3, N).astype(str)
    imp["sdk_version"] = np.where(imp["title_id"] == "HTL",
                                  rng.choice(["m4.2.0", "m4.3.1"], N, p=[0.35, 0.65]),
                                  rng.choice(["c2.8.0", "c2.9.2"], N, p=[0.2, 0.8]))
    imp["impression_id"] = ("IMP-" + pd.Series(rng.permutation(N) + 10_000_000).astype(str)).to_numpy()

    # ---- 5. inject known data-quality defects --------------------------------------
    loss = np.where(imp["title_id"] == "HTL", 0.03, 0.006)               # client never sent beacon
    imp = imp[rng.random(N) >= loss].reset_index(drop=True)
    dup =imp.sample(frac=0.004, random_state=seed).copy()               # SDK retry duplicates
    dup["event_ts"] = dup["event_ts"] + pd.to_timedelta(rng.integers(1, 9, len(dup)), unit="s")
    orphan = imp[imp["title_id"] == "DZL"].sample(350, random_state=seed + 1).copy()
    orphan["campaign_id"] = "CMP-26-099"                                 # not in manifest
    orphan["creative_id"] = "CMP-26-099-CR1"
    orphan["impression_id"] = "IMP-ORPH-" + pd.Series(range(len(orphan))).astype(str).to_numpy()
    imp = pd.concat([imp, dup, orphan], ignore_index=True)
    null_mask = rng.random(len(imp)) < 0.002                             # missing player IDs
    imp.loc[null_mask, "player_id"] = None

    cols = ["impression_id", "event_ts", "title_id", "platform", "placement_id", "campaign_id",
            "creative_id", "player_id", "ad_format", "pct_in_view", "in_view_ms",
            "video_duration_ms", "video_played_ms", "sdk_version"]
    imp = imp[cols].sample(frac=1, random_state=seed).reset_index(drop=True)

    # ---- 6. write outputs -----------------------------------------------------------
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.register("imp_df", imp)
    con.execute(f"COPY imp_df TO '{ROOT / 'data/raw/impressions.parquet'}' (FORMAT PARQUET)")
    pd.DataFrame(req_rows).to_csv(ROOT / "data/raw/ad_requests.csv", index=False)
    man = pd.DataFrame(manifest_rows)
    man.to_csv(ROOT / "config/campaign_manifest.csv", index=False)

    # AdOps monthly scope: paid campaigns whose flight overlaps the month; test lines excluded
    for month_start in [date(2026, 8, 1), date(2026, 9, 1)]:
        month_end = (pd.Timestamp(month_start) + pd.offsets.MonthEnd(0)).date()
        sc = man[(man["flight_start"] <= month_end) & (man["flight_end"] >= month_start)].copy()
        sc["include_in_report"] = np.where(sc["is_test"], "N", "Y")
        sc["adops_note"] = np.where(sc["is_test"], "QA test line - exclude", "")
        sc.loc[sc["campaign_id"] == "CMP-26-019", "adops_note"] = "Booked; trafficking not confirmed"
        sc.loc[sc["campaign_id"] == "CMP-26-009", "adops_note"] = "New inventory: GRD skills challenge"
        sc[["campaign_id", "advertiser", "include_in_report", "adops_note"]].to_csv(
            ROOT / f"config/adops_scope_{month_start:%Y-%m}.csv", index=False)

    print(f"impressions rows : {len(imp):,} (dupes {len(dup):,}, orphans {len(orphan):,}, null player {null_mask.sum():,})")
    print(f"ad_request rows  : {len(req_rows):,}")
    print(f"campaigns        : {len(man)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    build(ap.parse_args().seed)
