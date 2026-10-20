"""Render clean portfolio images of the Campaign Detail and Data Quality tables.

    python3 src/export_portfolio_images.py            # writes to portfolio/images/
Requires a prior pipeline run (reads data/warehouse.duckdb).
"""
import json
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "portfolio/images"
NAVY, GRID, INK, SLATE = "#1F2A44", "#D9DDE3", "#18202B", "#5A6573"
STATUS = {"ON PACE": "#D8EFDF", "UNDER-PACING": "#F8D7D7", "NO DELIVERY": "#F8D7D7",
          "OVER-PACING": "#FCEBC8", "PASS": "#D8EFDF", "WARN": "#FCEBC8", "FAIL": "#F8D7D7"}


def draw(rows, headers, aligns, title, subtitle, path, col_w, status_col=None, total_row=None):
    n = len(rows) + (1 if total_row else 0)
    fig_w, row_h = sum(col_w) + 0.4, 0.34
    fig = plt.figure(figsize=(fig_w, row_h * (n + 1) + 1.0), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, fig_w); ax.set_ylim(0, row_h * (n + 1) + 1.0)
    top = row_h * (n + 1) + 1.0
    ax.text(0.2, top - 0.35, title, fontsize=15, weight="bold", color=NAVY, va="center")
    ax.text(0.2, top - 0.68, subtitle, fontsize=9, style="italic", color=SLATE, va="center")
    y = top - 1.0
    ax.add_patch(plt.Rectangle((0.2, y - row_h), sum(col_w), row_h, color=NAVY))
    xs = [0.2 + sum(col_w[:i]) for i in range(len(col_w))]
    for x, w, h, a in zip(xs, col_w, headers, aligns):
        ax.text(x + (w - 0.08 if a == "right" else 0.08), y - row_h / 2, h, ha=a, va="center",
                fontsize=8.5, weight="bold", color="white")
    all_rows = rows + ([total_row] if total_row else [])
    for i, r in enumerate(all_rows):
        yy = y - row_h * (i + 2)
        bold = total_row is not None and i == len(rows)
        if status_col is not None and r[status_col] in STATUS:
            ax.add_patch(plt.Rectangle((xs[status_col], yy), col_w[status_col], row_h,
                                       color=STATUS[r[status_col]]))
        ax.plot([0.2, 0.2 + sum(col_w)], [yy, yy], color=INK if bold else GRID, lw=0.8 if bold else 0.6)
        for x, w, v, a in zip(xs, col_w, r, aligns):
            ax.text(x + (w - 0.08 if a == "right" else 0.08), yy + row_h / 2, v, ha=a, va="center",
                    fontsize=8.5, color=INK, weight="bold" if bold else "normal")
    fig.savefig(path, facecolor="white", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def pct(v): return "-" if v is None else f"{v:.1%}"
def num(v): return "-" if not v else f"{v:,.0f}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True)
    month = con.execute("select strftime(month_start, '%B %Y') from params").fetchone()[0]

    # Campaign Detail
    df = con.execute("""
        select campaign_id, advertiser, title_id, flight_start, flight_end, booked_impressions,
               impressions, delivery_pct_month, pacing_pct_to_date, pacing_status,
               viewability_rate, unique_reach, revenue_usd
        from mart_campaign_monthly order by title_id, campaign_id""").fetchall()
    rows = [[c, a, t, f"{fs:%b %d}", f"{fe:%b %d}", num(b), num(i), pct(d), pct(p), s, pct(v), num(u), f"${r:,.2f}"]
            for c, a, t, fs, fe, b, i, d, p, s, v, u, r in df]
    tot = [sum(x[k] or 0 for x in df) for k in (5, 6, 11, 12)]
    total = ["Total", "", "", "", "", num(tot[0]), num(tot[1]), "", "", "", "", "", f"${tot[3]:,.2f}"]
    draw(rows,
         ["Campaign", "Advertiser", "Title", "Start", "End", "Booked", "Impressions", "Delivery %",
          "Pacing %", "Pacing Status", "Viewability", "Unique Reach", "Revenue"],
         ["left", "left", "left", "left", "left"] + ["right"] * 4 + ["left"] + ["right"] * 3,
         f"Campaign Detail — {month}",
         "In-scope campaigns. Pacing = flight-to-date delivery vs straight-line goal (90–110% tolerance).",
         OUT / "03-campaign-detail.png",
         [1.05, 1.55, 0.55, 0.65, 0.65, 0.85, 1.0, 0.9, 0.85, 1.2, 0.95, 1.05, 0.95],
         status_col=9, total_row=total)

    # Data Quality
    month_key = con.execute("select strftime(month_start, '%Y-%m') from params").fetchone()[0]
    tests = json.loads((ROOT / f"output/{month_key}/run_log.json").read_text())["tests"]
    dq = con.execute("select check_name, value, note from mart_dq_summary").fetchall()
    rows = [[n, f"{v:,.0f}", "", note] for n, v, note in dq]
    rows += [["", "", "", ""]]
    rows += [[t["test"], str(t["failing_rows"]), t["status"], t["description"]] for t in tests]
    draw(rows, ["Check", "Rows", "Status", "Description"], ["left", "right", "left", "left"],
         f"Data Quality & Automated Checks — {month}",
         "Error-severity failures block publication; warnings are routed to AdOps / AdTech.",
         OUT / "04-data-quality.png", [2.9, 0.9, 0.8, 6.6], status_col=2)


if __name__ == "__main__":
    main()
