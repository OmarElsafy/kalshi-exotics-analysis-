"""
Regenerate ALL 14 charts in the Predicted theme:
- No orange edge bars (removed per feedback)
- Generous padding to prevent text overlap
- Tight chart layouts
"""
import os
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from matplotlib.patches import Wedge, Patch
from pathlib import Path
import numpy as np

API_KEY = os.environ["DUNE_API_KEY"]  # set via: export DUNE_API_KEY=...
headers = {"X-Dune-API-Key": API_KEY}
CHARTS_DIR = Path("../charts")

BROWN_DARK = "#3B2314"
ORANGE = "#CC5A1A"
BROWN_MUTED = "#8B6F5E"
CREAM = "#FAF6F0"
TAN = "#D4B896"
SAGE = "#9CA88A"
PALETTE = [ORANGE, BROWN_DARK, BROWN_MUTED, TAN, SAGE, "#A65D2A", "#6B4E3D", "#C49968", "#8F9577", "#D9853B", "#5C4636"]

plt.rcParams.update({
    "font.family": "Space Mono",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "-", "grid.color": BROWN_MUTED,
    "figure.facecolor": CREAM, "axes.facecolor": CREAM,
    "text.color": BROWN_DARK,
})

def fetch(qid):
    r = requests.get(f"https://api.dune.com/api/v1/query/{qid}/results", headers=headers)
    return pd.DataFrame(r.json()["result"]["rows"])

def fmt_money(v):
    if v >= 1e9: return f"${v/1e9:.2f}B"
    if v >= 1e6: return f"${v/1e6:,.1f}M"
    if v >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:,.0f}"

def run_sql(name, sql):
    r = requests.post('https://api.dune.com/api/v1/query', headers={**headers, 'Content-Type': 'application/json'},
                      json={'name': name, 'query_sql': sql})
    qid = r.json().get('query_id')
    if not qid:
        return None, None
    r = requests.post(f'https://api.dune.com/api/v1/query/{qid}/execute', headers=headers)
    eid = r.json()['execution_id']
    while True:
        time.sleep(4)
        s = requests.get(f'https://api.dune.com/api/v1/execution/{eid}/status', headers=headers).json()['state']
        if s == 'QUERY_STATE_COMPLETED': break
    return pd.DataFrame(requests.get(f'https://api.dune.com/api/v1/execution/{eid}/results', headers=headers).json()['result']['rows']), qid


# ===== 00 PLATFORM PERSPECTIVE =====
sql = """
SELECT
    SUM(daily_volume) AS total_kalshi,
    SUM(daily_volume) FILTER (WHERE report_ticker LIKE 'KXMVE%') AS exotic_vol,
    SUM(daily_volume) FILTER (WHERE category = 'Sports' AND report_ticker NOT LIKE 'KXMVE%') AS sports_non_exotic,
    SUM(daily_volume) FILTER (WHERE category != 'Sports' AND report_ticker NOT LIKE 'KXMVE%') AS everything_else
FROM kalshi.market_report WHERE DATE(date) >= DATE '2025-09-17'
"""
df, _ = run_sql("NB Platform Composition", sql)
data = df.iloc[0]
total = data['total_kalshi']

fig, ax = plt.subplots(figsize=(13, 5.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
values = [data['exotic_vol'], data['sports_non_exotic'], data['everything_else']]
labels = ["Exotic Parlays", "Sports (single-game, non-exotic)", "Everything Else"]
colors = [ORANGE, BROWN_DARK, BROWN_MUTED]
left = 0
for v, c, label in zip(values, colors, labels):
    pct = v / total * 100
    ax.barh(0, v, left=left, color=c, height=0.55, edgecolor=CREAM, linewidth=3)
    if pct > 5:
        ax.text(left + v/2, 0, f"{pct:.1f}%\n{fmt_money(v)}", ha="center", va="center",
                color=CREAM, fontsize=12, fontweight="bold", fontfamily="Space Mono")
    left += v
ax.set_yticks([])
ax.set_xlim(0, total * 1.04)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1e9:.0f}B"))
ax.set_title("Where Exotic Parlays Fit on Kalshi — Total Platform Volume Since Sep 2025",
             fontsize=13, fontweight="bold", pad=20, loc="left", color=BROWN_DARK)
ax.set_xlabel("USD Notional Volume", fontsize=10, color=BROWN_DARK)
ax.tick_params(axis="x", colors=BROWN_DARK, labelsize=10)
ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED); ax.grid(axis="y", visible=False)
legend_items = [Patch(facecolor=c, label=f"{l}  —  {fmt_money(v)} ({v/total*100:.1f}%)")
                for l, c, v in zip(labels, colors, values)]
ax.legend(handles=legend_items, loc="lower center", bbox_to_anchor=(0.5, -0.55),
          ncol=3, frameon=False, fontsize=10, labelcolor=BROWN_DARK)
ax.set_ylim(-0.5, 0.5)
plt.subplots_adjust(bottom=0.28, top=0.85, left=0.02, right=0.98)
plt.savefig(CHARTS_DIR / "00_platform_perspective.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("00 ✓")


# ===== 01 MONTHLY HANDLE =====
r = requests.get('https://api.dune.com/api/v1/query/7521948/results', headers=headers)
df = pd.DataFrame(r.json()['result']['rows'])
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")
df["handle_m"] = df["handle"] / 1e6

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
nfl_end = pd.Timestamp("2026-02-09")
colors = [ORANGE if m <= nfl_end else BROWN_DARK for m in df["month"]]
bars = ax.bar(df["month"].dt.strftime("%b %Y"), df["handle_m"], color=colors,
              edgecolor=CREAM, linewidth=2)
for bar, val in zip(bars, df["handle_m"]):
    if val >= 1:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(df["handle_m"])*0.02,
                f"${val:,.0f}M", ha="center", va="bottom", fontsize=10,
                color=BROWN_DARK, fontweight="bold", fontfamily="Space Mono")

# NFL season end marker — placed where the visual transition happens
ax.axvline(5.5, color=BROWN_MUTED, linestyle="--", alpha=0.7, linewidth=1.5)
ax.text(5.5, max(df["handle_m"]) * 0.55, "NFL ends\nFeb 9", fontsize=9,
        color=BROWN_MUTED, fontweight="bold", fontfamily="Space Mono", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=CREAM, edgecolor=BROWN_MUTED, linewidth=1))

legend_items = [
    Patch(facecolor=ORANGE, label="NFL season"),
    Patch(facecolor=BROWN_DARK, label="Post-NFL"),
]
ax.legend(handles=legend_items, loc="upper left", frameon=False, fontsize=10, labelcolor=BROWN_DARK)
ax.set_title("Monthly handle has grown post-NFL, May 2026 ran 7.8x larger than December's NFL peak",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Handle (USD millions)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}M"))
ax.tick_params(axis="x", rotation=30, colors=BROWN_DARK, labelsize=9)
ax.tick_params(axis="y", colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False)
ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, df["handle_m"].max() * 1.18)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "01_monthly_handle.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("01 ✓")


# ===== 02 CUMULATIVE =====
df["cum_notional_b"] = df["cumulative_notional"] / 1e9
df["cum_handle_b"] = df["cumulative_handle"] / 1e9

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
ax.fill_between(df["month"], df["cum_notional_b"], color=BROWN_DARK, alpha=0.12)
ax.plot(df["month"], df["cum_notional_b"], color=BROWN_DARK, linewidth=3, label="Notional")
ax.fill_between(df["month"], df["cum_handle_b"], color=ORANGE, alpha=0.20)
ax.plot(df["month"], df["cum_handle_b"], color=ORANGE, linewidth=3, label="Handle (cash)")

last = df.iloc[-1]
ax.annotate(f"${last['cum_notional_b']:.1f}B", xy=(last["month"], last["cum_notional_b"]),
            xytext=(10, 5), textcoords="offset points", fontsize=12, fontweight="bold", color=BROWN_DARK,
            fontfamily="Space Mono")
ax.annotate(f"${last['cum_handle_b']:.2f}B", xy=(last["month"], last["cum_handle_b"]),
            xytext=(10, -5), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono")
ax.set_title(f"Cumulative handle reached ${last['cum_handle_b']:.2f}B against ${last['cum_notional_b']:.1f}B notional since launch",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("USD billions", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}B"))
ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.set_xlim(df["month"].min(), df["month"].max() + pd.Timedelta(days=18))
plt.tight_layout()
plt.savefig(CHARTS_DIR / "02_cumulative_handle_notional.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("02 ✓")


# ===== 03 IMPLIED PROBABILITY DRIFT =====
df = fetch("7516976")
df["week"] = pd.to_datetime(df["week"])
df = df.sort_values("week")

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
ax.plot(df["week"], df["avg_price_pct"], color=ORANGE, linewidth=3, label="Average")
ax.plot(df["week"], df["median_price_pct"], color=BROWN_DARK, linewidth=2.5, linestyle="--", label="Median")

first, last = df.iloc[0], df.iloc[-1]
ax.annotate(f"{first['avg_price_pct']:.1f}%", xy=(first["week"], first["avg_price_pct"]),
            xytext=(10, 12), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono")
ax.annotate(f"{last['avg_price_pct']:.1f}%", xy=(last["week"], last["avg_price_pct"]),
            xytext=(-15, 14), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono", ha="right")
ax.set_title("Average implied probability per trade drifted from 20% to 10% over eight months",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Implied probability (%)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.legend(loc="upper right", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.set_ylim(0, max(df["avg_price_pct"].max(), df["median_price_pct"].max()) * 1.25)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "03_implied_probability_drift.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("03 ✓")


# ===== 04 BET SIZE DISTRIBUTION =====
r = requests.get('https://api.dune.com/api/v1/query/7557750/results', headers=headers)
df = pd.DataFrame(r.json()['result']['rows']).sort_values("bet_size_bucket")
df["label"] = df["bet_size_bucket"].str.split(": ", expand=True)[1]
df["pct_of_trades"] = pd.to_numeric(df["pct_of_trades"])
df["pct_of_cash"] = pd.to_numeric(df["pct_of_cash"])

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
x = list(range(len(df)))
bars1 = ax.bar([i-0.21 for i in x], df["pct_of_trades"], width=0.42, color=ORANGE,
               label="% of trades", edgecolor=CREAM, linewidth=2)
bars2 = ax.bar([i+0.21 for i in x], df["pct_of_cash"], width=0.42, color=BROWN_DARK,
               label="% of total cash", edgecolor=CREAM, linewidth=2)
for bar, val in zip(bars1, df["pct_of_trades"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.0,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color=ORANGE,
            fontweight="bold", fontfamily="Space Mono")
for bar, val in zip(bars2, df["pct_of_cash"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.0,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color=BROWN_DARK,
            fontweight="bold", fontfamily="Space Mono")
ax.set_xticks(x); ax.set_xticklabels(df["label"], fontsize=10, color=BROWN_DARK)
ax.set_title("3.6% of trades over $200 drive 54.8% of all cash exchanged",
             fontsize=13, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Share (%)", fontsize=10, color=BROWN_DARK)
ax.set_xlabel("Bet size (USD)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.legend(loc="upper right", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.set_ylim(0, max(df["pct_of_cash"].max(), df["pct_of_trades"].max()) * 1.18)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "04_bet_size_distribution.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("04 ✓")


# ===== 05 FEE REVENUE BY PRODUCT =====
df = fetch("7576002").sort_values("Est. Kalshi Fee Revenue ($)", ascending=True)
df["fee_m"] = df["Est. Kalshi Fee Revenue ($)"] / 1e6
top = df[df["fee_m"] >= 1].copy()
other_total = df[df["fee_m"] < 1]["fee_m"].sum()
if other_total > 0:
    top = pd.concat([pd.DataFrame([{"Product": "Other (8 products)", "fee_m": other_total}]), top], ignore_index=True)

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
bars = ax.barh(top["Product"], top["fee_m"], color=ORANGE, edgecolor=CREAM, linewidth=2)
for bar, val in zip(bars, top["fee_m"]):
    ax.text(bar.get_width() + max(top["fee_m"])*0.015, bar.get_y() + bar.get_height()/2,
            f"${val:,.1f}M", va="center", fontsize=11, color=BROWN_DARK, fontweight="bold",
            fontfamily="Space Mono")
total_fees = df["fee_m"].sum()
sport_multi_fee = df[df["Product"]=="Sports Multi-Game"]["fee_m"].iloc[0]
ax.set_title(f"Sports Multi-Game alone produced ${sport_multi_fee:.1f}M of an estimated ${total_fees:.0f}M in Kalshi fees",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_xlabel("Estimated fees (USD millions)", fontsize=10, color=BROWN_DARK)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.0f}M"))
ax.grid(axis="y", visible=False); ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=10)
ax.set_xlim(0, max(top["fee_m"]) * 1.18)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "05_fee_revenue_by_product.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("05 ✓")


# ===== Donut helper =====
def make_donut(values, labels, title, save_path, inner_label_threshold=4.0):
    total = sum(values)
    pcts = [v/total*100 for v in values]
    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
    ax.set_aspect('equal')
    ax.set_xlim(-1.6, 4.8); ax.set_ylim(-1.2, 1.2); ax.axis('off')
    cumulative = 90
    for v in values:
        angle = v/total * 360
        ax.add_patch(Wedge((0.04, -0.06), 1.0, cumulative - angle, cumulative,
                       width=0.42, facecolor="#000", alpha=0.13, edgecolor="none", zorder=1))
        cumulative -= angle
    cumulative = 90; wedges = []
    for v, c, pct in zip(values, PALETTE[:len(values)], pcts):
        angle = v/total * 360
        wedge = Wedge((0, 0), 1.0, cumulative - angle, cumulative,
                      width=0.42, facecolor=c, edgecolor=CREAM, linewidth=3, zorder=3)
        ax.add_patch(wedge); wedges.append(wedge)
        if pct >= inner_label_threshold:
            mid = np.radians(cumulative - angle/2)
            r = 0.78
            x, y = r*np.cos(mid), r*np.sin(mid)
            ax.text(x, y, f"{pct:.1f}%", ha="center", va="center",
                    fontsize=15, fontweight="bold", color=CREAM, zorder=5, fontfamily="Space Mono",
                    path_effects=[path_effects.withStroke(linewidth=3, foreground=BROWN_DARK)])
        cumulative -= angle
    ax.text(0, 0.10, fmt_money(total), ha="center", va="center", fontsize=24, fontweight="bold",
            color=BROWN_DARK, fontfamily="Space Mono")
    ax.text(0, -0.12, "Total Handle", ha="center", va="center", fontsize=10, color=BROWN_MUTED, fontfamily="Space Mono")
    ax.text(-1.6, 1.15, title, fontsize=13, fontweight="bold", color=BROWN_DARK, ha="left", va="top",
            fontfamily="Space Mono")
    legend_x = 1.6
    for i, (label, pct, v, c) in enumerate(zip(labels, pcts, values, PALETTE[:len(values)])):
        y = 0.9 - i * 0.16
        ax.add_patch(patches.Rectangle((legend_x, y - 0.04), 0.12, 0.08, facecolor=c, edgecolor="none"))
        ax.text(legend_x + 0.18, y, label, fontsize=11, color=BROWN_DARK, va="center", ha="left", fontfamily="Space Mono")
        ax.text(legend_x + 2.1, y, f"{pct:.2f}%", fontsize=11, color=BROWN_MUTED, va="center", ha="right",
                fontweight="bold", fontfamily="Space Mono")
        ax.text(legend_x + 3.05, y, fmt_money(v), fontsize=11, color=ORANGE, va="center", ha="right",
                fontweight="bold", fontfamily="Space Mono")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight", facecolor=CREAM)
    plt.close()


df = fetch("7506442")
df["Handle ($)"] = pd.to_numeric(df["Handle ($)"])

d = df.sort_values("Handle ($)", ascending=False)
make_donut(d["Handle ($)"].tolist(), d["Series"].tolist(),
    "Sport Multi-Game and Cross Category account for 95% of exotic handle",
    CHARTS_DIR / "06_handle_by_product.png", 8.0)
print("06 ✓")

d = df.groupby("Type")["Handle ($)"].sum().sort_values(ascending=False).reset_index()
make_donut(d["Handle ($)"].tolist(), d["Type"].tolist(),
    "Multi-game parlays alone account for 59% of total exotic handle",
    CHARTS_DIR / "07_handle_by_type.png", 4.0)
print("07 ✓")

d = df.groupby("Category")["Handle ($)"].sum().sort_values(ascending=False).reset_index()
make_donut(d["Handle ($)"].tolist(), d["Category"].tolist(),
    "63% of handle is Sports, with effectively zero outside sports and cross-category",
    CHARTS_DIR / "08_handle_by_category.png", 2.0)
print("08 ✓")


# ===== 09 LAUNCH TIMELINE =====
r = requests.get('https://api.dune.com/api/v1/query/7506442/results', headers=headers)
# Use timeline-specific query results
sql = """
SELECT
    CASE report_ticker
        WHEN 'KXMVESPORTSMULTIGAMEEXTENDED' THEN 'Sport Multi Game'
        WHEN 'KXMVECROSSCATEGORY'           THEN 'Cross Category'
        WHEN 'KXMVENFLSINGLEGAME'           THEN 'NFL Single Game'
        WHEN 'KXMVENFLMULTIGAMEEXTENDED'    THEN 'NFL Multi Game Ext'
        WHEN 'KXMVENBASINGLEGAME'           THEN 'NBA Single Game'
        WHEN 'KXMVECBCHAMPIONSHIP'          THEN 'CBB Championship'
        WHEN 'KXMVEOSCARS'                  THEN 'Oscars'
        WHEN 'KXMVEGRAMMYS'                 THEN 'Grammys'
        WHEN 'KXMVENFLMULTIGAME'            THEN 'NFL Multi Game'
        WHEN 'KXMVEMENTIONSSINGLE'          THEN 'Mention'
        WHEN 'KXMVENBAMULTIGAMEEXTENDED'    THEN 'NBA Multi Game'
        ELSE report_ticker END AS product,
    MIN(DATE(date)) AS launch_date,
    MAX(DATE(date)) AS last_date,
    SUM(daily_volume * (high + low) / 200.0) AS handle
FROM kalshi.market_report
WHERE report_ticker LIKE 'KXMVE%' AND daily_volume > 0
GROUP BY 1 ORDER BY handle DESC
"""
df, _ = run_sql("NB Timeline", sql)
df["launch_date"] = pd.to_datetime(df["launch_date"])
df["last_date"] = pd.to_datetime(df["last_date"])
today = pd.to_datetime("2026-05-28")
df["is_active"] = (today - df["last_date"]).dt.days < 21
df = df.sort_values("handle", ascending=True)

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
for i, row in df.reset_index(drop=True).iterrows():
    color = ORANGE if row["is_active"] else BROWN_MUTED
    width = (row["last_date"] - row["launch_date"]).days
    ax.barh(i, width, left=row["launch_date"], height=0.55, color=color, alpha=0.95, edgecolor=CREAM, linewidth=1)
    ax.plot(row["launch_date"], i, "o", color=CREAM, markersize=8, markeredgecolor=color, markeredgewidth=2)
    label = fmt_money(row["handle"])
    if width > 60:
        midpoint = row["launch_date"] + (row["last_date"] - row["launch_date"]) / 2
        ax.text(midpoint, i, label, ha="center", va="center", fontsize=10,
                color=CREAM, fontweight="bold", fontfamily="Space Mono")
    else:
        ax.text(row["last_date"] + pd.Timedelta(days=4), i, label, ha="left", va="center",
                fontsize=10, color=BROWN_DARK, fontweight="bold", fontfamily="Space Mono")

# Move event labels into the top margin (above plot area)
events = [
    ("Launch", "2025-09-17"),
    ("Grammys", "2026-02-02"),
    ("Super Bowl", "2026-02-08"),
    ("Oscars", "2026-03-15"),
    ("March Madness", "2026-03-16"),
]
y_top = len(df) + 0.1
for name, date in events:
    d = pd.to_datetime(date)
    ax.axvline(d, color=BROWN_DARK, linestyle=":", alpha=0.4, linewidth=1)
    ax.text(d, y_top, name, ha="center", va="bottom", fontsize=8, color=BROWN_DARK,
            fontweight="bold", fontfamily="Space Mono")

ax.axvline(today, color=BROWN_DARK, linewidth=1.5, alpha=0.8)
ax.text(today, -1.2, "TODAY", ha="center", va="top", fontsize=9, color=BROWN_DARK,
        fontweight="bold", fontfamily="Space Mono")

ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["product"].values, fontsize=10, color=BROWN_DARK, fontfamily="Space Mono")
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.set_xlim(pd.to_datetime("2025-08-25"), pd.to_datetime("2026-06-20"))
ax.set_ylim(-1.6, len(df) + 1.0)
ax.set_title("Eleven combo products launched in phases, three still carry the platform",
             fontsize=13, fontweight="bold", pad=14, loc="left", color=BROWN_DARK)
ax.grid(axis="y", visible=False); ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED)
legend_items = [Patch(facecolor=ORANGE, label="Active"), Patch(facecolor=BROWN_MUTED, label="Dormant")]
ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=10, labelcolor=BROWN_DARK)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "09_launch_timeline.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("09 ✓")


# ===== 10 FLOOR TRADES MONTHLY =====
r = requests.get('https://api.dune.com/api/v1/query/7598456/results', headers=headers)
df = pd.DataFrame(r.json()['result']['rows'])
df["month"] = pd.to_datetime(df["month"])
df["pct_floor"] = pd.to_numeric(df["pct_floor"])
df = df.sort_values("month")

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
ax.fill_between(df["month"], df["pct_floor"], color=ORANGE, alpha=0.18)
ax.plot(df["month"], df["pct_floor"], color=ORANGE, linewidth=3, marker="o", markersize=9,
        markeredgecolor=CREAM, markeredgewidth=2)
for idx in [0, len(df)-1]:
    row = df.iloc[idx]
    ax.annotate(f"{row['pct_floor']:.1f}%", xy=(row["month"], row["pct_floor"]),
                xytext=(0, 18), textcoords="offset points", fontsize=13, fontweight="bold",
                color=BROWN_DARK, fontfamily="Space Mono", ha="center")
first, last = df.iloc[0], df.iloc[-1]
ax.set_title(f"Share of trades at the 1¢ floor grew from {first['pct_floor']:.1f}% to {last['pct_floor']:.1f}% over eight months",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("% of trades at 1¢ floor", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, df["pct_floor"].max() * 1.4)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "10_floor_trades_monthly.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("10 ✓")


# ===== 11 OI OVER TIME =====
r = requests.get('https://api.dune.com/api/v1/query/7598460/results', headers=headers)
df = pd.DataFrame(r.json()['result']['rows'])
df["as_of_date"] = pd.to_datetime(df["as_of_date"])
df["exotic_oi_m"] = pd.to_numeric(df["exotic_oi"]) / 1e6
df["total_oi_m"] = pd.to_numeric(df["total_kalshi_oi"]) / 1e6
df = df.sort_values("as_of_date")

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
ax.fill_between(df["as_of_date"], df["total_oi_m"], color=BROWN_DARK, alpha=0.10, label="Total Kalshi OI")
ax.plot(df["as_of_date"], df["total_oi_m"], color=BROWN_DARK, linewidth=2, alpha=0.6)
ax.fill_between(df["as_of_date"], df["exotic_oi_m"], color=ORANGE, alpha=0.30, label="Exotic OI")
ax.plot(df["as_of_date"], df["exotic_oi_m"], color=ORANGE, linewidth=2.5)

# Event markers - put labels INSIDE plot at top to prevent overlap with title
events = [("NFL Opener", "2025-09-17"), ("Super Bowl", "2026-02-08"), ("NBA Playoffs", "2026-04-18")]
y_top = df["total_oi_m"].max() * 1.04
for name, date in events:
    d = pd.to_datetime(date)
    if d >= df["as_of_date"].min() and d <= df["as_of_date"].max():
        ax.axvline(d, color=BROWN_DARK, linestyle=":", alpha=0.45, linewidth=1.2)
        ax.text(d, y_top, name, ha="center", va="bottom", fontsize=9, color=BROWN_DARK,
                fontweight="bold", fontfamily="Space Mono")

# Annotate Super Bowl peak with arrow off to the side
sb_date = pd.to_datetime("2026-02-08")
sb_row = df[df["as_of_date"] == sb_date]
if len(sb_row):
    sb_val = sb_row["exotic_oi_m"].iloc[0]
    ax.annotate(f"Feb 8 peak\n${sb_val:.1f}M", xy=(sb_date, sb_val),
                xytext=(60, -10), textcoords="offset points", fontsize=11, fontweight="bold",
                color=ORANGE, fontfamily="Space Mono",
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))

ax.set_title("Exotic OI peaked at $137.9M during Super Bowl LIX, the largest single-day exotic OI on record",
             fontsize=12, fontweight="bold", pad=28, loc="left", color=BROWN_DARK)
ax.set_ylabel("Open Interest (USD millions)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}M"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, df["total_oi_m"].max() * 1.18)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "11_oi_over_time.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("11 ✓")


# ===== 12 POST-NFL DURABILITY =====
r = requests.get('https://api.dune.com/api/v1/query/7521948/results', headers=headers)
mdf = pd.DataFrame(r.json()['result']['rows'])
mdf["month"] = pd.to_datetime(mdf["month"])
mdf = mdf.sort_values("month")
mdf["handle_m"] = mdf["handle"] / 1e6
categories = ["Dec 2025\n(NFL season)", "Apr 2026\n(post-NFL)", "May 2026\n(post-NFL)"]
values = [mdf[mdf["month"] == "2025-12-01"]["handle_m"].iloc[0],
          mdf[mdf["month"] == "2026-04-01"]["handle_m"].iloc[0],
          mdf[mdf["month"] == "2026-05-01"]["handle_m"].iloc[0]]
colors = [BROWN_MUTED, ORANGE, ORANGE]

fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
bars = ax.bar(categories, values, color=colors, edgecolor=CREAM, linewidth=3, width=0.55)
for bar, val in zip(bars, values):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(values)*0.025,
            f"${val:,.0f}M", ha="center", va="bottom", fontsize=14, fontweight="bold",
            color=BROWN_DARK, fontfamily="Space Mono")
growth_pct = (values[2] - values[0]) / values[0] * 100
ax.set_title(f"Handle grew {growth_pct:+.0f}% from December's NFL peak to May with no major sport in season",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Monthly Handle (USD millions)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}M"))
ax.tick_params(colors=BROWN_DARK, labelsize=10)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, max(values) * 1.22)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "12_post_nfl_durability.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("12 ✓")


# ===== 13 IMPLIED PROBABILITY HISTOGRAM =====
r = requests.get('https://api.dune.com/api/v1/query/7598462/results', headers=headers)
df = pd.DataFrame(r.json()['result']['rows']).sort_values("price_bucket")
df["label"] = df["price_bucket"].str.split(": ", expand=True)[1]
df["pct_of_trades"] = pd.to_numeric(df["pct_of_trades"])

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
bars = ax.bar(df["label"], df["pct_of_trades"], color=ORANGE, edgecolor=CREAM, linewidth=2)
bars[0].set_color(BROWN_DARK)
for bar, val in zip(bars, df["pct_of_trades"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.6,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold",
            color=BROWN_DARK, fontfamily="Space Mono")
ax.set_title("Bettors place more trades at the 1¢ floor than at every implied probability above 50% combined",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("% of all trades", fontsize=10, color=BROWN_DARK)
ax.set_xlabel("Implied probability (%)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, df["pct_of_trades"].max() * 1.22)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "13_parlay_odds_histogram.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("13 ✓")


# ===== 14 IMPLIED PROB BY PRODUCT =====
df = fetch("7506442")
df['Avg Price (%)'] = pd.to_numeric(df['Avg Price (%)'])
df['Median Price (%)'] = pd.to_numeric(df['Median Price (%)'])
df['Handle ($)'] = pd.to_numeric(df['Handle ($)'])
df = df.sort_values('Handle ($)', ascending=False)
df['Product'] = df['Series'].str.replace('MVE ', '')

fig, ax = plt.subplots(figsize=(14, 7.5))
fig.patch.set_facecolor(CREAM); ax.set_facecolor(CREAM)
x = np.arange(len(df)); width = 0.38
for i, (_, row) in enumerate(df.iterrows()):
    is_live = row['Status'] == 'Live'
    avg_color = ORANGE if is_live else "#E8A472"
    med_color = BROWN_DARK if is_live else "#9D8268"
    alpha = 1.0 if is_live else 0.65
    ax.bar(i - width/2, row['Avg Price (%)'], width, color=avg_color, alpha=alpha,
           edgecolor=CREAM, linewidth=2)
    ax.bar(i + width/2, row['Median Price (%)'], width, color=med_color, alpha=alpha,
           edgecolor=CREAM, linewidth=2)
    ax.text(i - width/2, row['Avg Price (%)'] + 0.8, f"{row['Avg Price (%)']:.1f}%",
            ha="center", va="bottom", fontsize=8.5,
            color=ORANGE if is_live else BROWN_MUTED, fontweight="bold", fontfamily="Space Mono")
    ax.text(i + width/2, row['Median Price (%)'] + 0.8, f"{row['Median Price (%)']:.1f}%",
            ha="center", va="bottom", fontsize=8.5,
            color=BROWN_DARK if is_live else BROWN_MUTED, fontweight="bold", fontfamily="Space Mono")

labels = []
for _, row in df.iterrows():
    suffix = "  [LIVE]" if row['Status'] == 'Live' else "  [dormant]"
    labels.append(row['Product'] + suffix)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8.5, color=BROWN_DARK, rotation=35, ha="right")
for tick, (_, row) in zip(ax.get_xticklabels(), df.iterrows()):
    if row['Status'] == 'Live':
        tick.set_color(BROWN_DARK); tick.set_fontweight("bold")
    else:
        tick.set_color(BROWN_MUTED)
ax.set_title("Implied probability varies sharply by product, College Basketball runs at 3.3% while Mention sits at 54%",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Implied probability (%)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
legend_items = [
    Patch(facecolor=ORANGE, label='Average (Live)'),
    Patch(facecolor=BROWN_DARK, label='Median (Live)'),
    Patch(facecolor="#E8A472", alpha=0.65, label='Average (Dormant)'),
    Patch(facecolor="#9D8268", alpha=0.65, label='Median (Dormant)'),
]
ax.legend(handles=legend_items, loc="upper right", frameon=False, fontsize=9, labelcolor=BROWN_DARK)
ax.tick_params(axis="y", colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False); ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.set_ylim(0, max(df['Avg Price (%)'].max(), df['Median Price (%)'].max()) * 1.18)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "14_implied_prob_by_product.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("14 ✓")

print("\nAll 15 charts regenerated. No edge bars, overlap fixed.")
