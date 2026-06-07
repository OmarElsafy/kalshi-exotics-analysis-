"""
Regenerate all 10 article charts in the Predicted brand theme.
- Space Mono font everywhere
- Dark brown (#3B2314) titles
- Orange (#CC5A1A) accents
- Muted brown (#8B6F5E) secondary
- Cream background (#FAF6F0)
"""
import os
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from matplotlib.patches import Wedge
from pathlib import Path
import numpy as np

API_KEY = os.environ["DUNE_API_KEY"]  # set via: export DUNE_API_KEY=...
headers = {"X-Dune-API-Key": API_KEY}
CHARTS_DIR = Path("../charts")

# === PREDICTED THEME ===
BROWN_DARK = "#3B2314"
ORANGE = "#CC5A1A"
BROWN_MUTED = "#8B6F5E"
CREAM = "#FAF6F0"
TAN = "#D4B896"
SAGE = "#9CA88A"

PALETTE = [ORANGE, BROWN_DARK, BROWN_MUTED, TAN, SAGE, "#A65D2A", "#6B4E3D", "#C49968", "#8F9577", "#D9853B", "#5C4636"]

plt.rcParams.update({
    "font.family": "Space Mono",
    "font.weight": "normal",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "-",
    "grid.color": BROWN_MUTED,
    "figure.facecolor": CREAM,
    "axes.facecolor": CREAM,
    "axes.labelcolor": BROWN_DARK,
    "axes.titlecolor": BROWN_DARK,
    "xtick.color": BROWN_DARK,
    "ytick.color": BROWN_DARK,
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

def style_axes(ax, title):
    ax.set_title(title, fontsize=14, fontweight="bold", pad=18, loc="left", color=BROWN_DARK,
                 fontfamily="Space Mono")
    for spine in ax.spines.values():
        spine.set_visible(False)

def add_edge_bars(fig):
    """Add the orange edge bars top and bottom (Predicted brand)."""
    fig.patches.extend([
        plt.Rectangle((0, 0.98), 1, 0.02, transform=fig.transFigure, color=ORANGE, zorder=10),
        plt.Rectangle((0, 0), 1, 0.02, transform=fig.transFigure, color=ORANGE, zorder=10),
    ])


# ===== CHART 00: PLATFORM PERSPECTIVE =====
sql = """
SELECT
    SUM(daily_volume) AS total_kalshi,
    SUM(daily_volume) FILTER (WHERE report_ticker LIKE 'KXMVE%') AS exotic_vol,
    SUM(daily_volume) FILTER (WHERE category = 'Sports' AND report_ticker NOT LIKE 'KXMVE%') AS sports_non_exotic,
    SUM(daily_volume) FILTER (WHERE category != 'Sports' AND report_ticker NOT LIKE 'KXMVE%') AS everything_else
FROM kalshi.market_report
WHERE DATE(date) >= DATE '2025-09-17'
"""
r = requests.post('https://api.dune.com/api/v1/query', headers={**headers, 'Content-Type': 'application/json'},
                  json={'name': 'NB05 Platform Composition', 'query_sql': sql})
qid = r.json()['query_id']
r = requests.post(f'https://api.dune.com/api/v1/query/{qid}/execute', headers=headers)
eid = r.json()['execution_id']
while True:
    time.sleep(4)
    if requests.get(f'https://api.dune.com/api/v1/execution/{eid}/status', headers=headers).json()['state'] == 'QUERY_STATE_COMPLETED':
        break
data = requests.get(f'https://api.dune.com/api/v1/execution/{eid}/results', headers=headers).json()['result']['rows'][0]

total = data['total_kalshi']
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)

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
ax.set_xlim(0, total * 1.02)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1e9:.0f}B"))
ax.set_title("Where Exotic Parlays Fit on Kalshi — Total Platform Volume Since Sep 2025",
             fontsize=14, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_xlabel("USD Notional Volume", fontsize=10, color=BROWN_DARK)
ax.tick_params(axis="x", colors=BROWN_DARK, labelsize=10)
ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED)
ax.grid(axis="y", visible=False)

from matplotlib.patches import Patch
legend_items = [Patch(facecolor=c, label=f"{l} — {fmt_money(v)} ({v/total*100:.1f}%)")
                for l, c, v in zip(labels, colors, values)]
ax.legend(handles=legend_items, loc="lower center", bbox_to_anchor=(0.5, -0.4),
          ncol=3, frameon=False, fontsize=10, labelcolor=BROWN_DARK)

ax.text(total * 1.005, 0, f"  Total: {fmt_money(total)}", va="center", ha="left",
        fontsize=11, fontweight="bold", color=BROWN_DARK, fontfamily="Space Mono")

ax.set_ylim(-0.5, 0.4)
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "00_platform_perspective.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("00 ✓")


# ===== CHART 01: MONTHLY HANDLE =====
df = fetch("7521948")
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")
df["handle_m"] = df["handle"] / 1e6

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
bars = ax.bar(df["month"].dt.strftime("%b %Y"), df["handle_m"], color=ORANGE, edgecolor=CREAM, linewidth=2)
for bar, val in zip(bars, df["handle_m"]):
    if val >= 1:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(df["handle_m"])*0.015,
                f"${val:,.0f}M", ha="center", va="bottom", fontsize=10, color=BROWN_DARK, fontweight="bold",
                fontfamily="Space Mono")

ax.set_title("Monthly Exotic Handle scaled to ${:,.0f}M in May 2026".format(df.iloc[-1]['handle_m']),
             fontsize=14, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Handle (USD millions)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}M"))
ax.tick_params(axis="x", rotation=30, colors=BROWN_DARK, labelsize=9)
ax.tick_params(axis="y", colors=BROWN_DARK, labelsize=9)
ax.grid(axis="x", visible=False)
ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "01_monthly_handle.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("01 ✓")


# ===== CHART 02: CUMULATIVE HANDLE vs NOTIONAL =====
df = fetch("7521948")
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")
df["cum_notional_b"] = df["cumulative_notional"] / 1e9
df["cum_handle_b"] = df["cumulative_handle"] / 1e9

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
ax.fill_between(df["month"], df["cum_notional_b"], color=BROWN_DARK, alpha=0.15)
ax.plot(df["month"], df["cum_notional_b"], color=BROWN_DARK, linewidth=3, label="Notional")
ax.plot(df["month"], df["cum_handle_b"], color=ORANGE, linewidth=3, label="Handle (cash)")
ax.fill_between(df["month"], df["cum_handle_b"], color=ORANGE, alpha=0.2)
last = df.iloc[-1]
ax.annotate(f"${last['cum_notional_b']:.1f}B", xy=(last["month"], last["cum_notional_b"]),
            xytext=(8, 0), textcoords="offset points", fontsize=12, fontweight="bold", color=BROWN_DARK,
            fontfamily="Space Mono")
ax.annotate(f"${last['cum_handle_b']:.2f}B", xy=(last["month"], last["cum_handle_b"]),
            xytext=(8, 0), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono")
ax.set_title("Cumulative handle reached ${:.2f}B against ${:.1f}B notional since launch".format(
    last['cum_handle_b'], last['cum_notional_b']),
    fontsize=13, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("USD billions", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}B"))
ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False)
ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "02_cumulative_handle_notional.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("02 ✓")


# ===== CHART 03: IMPLIED PROBABILITY DRIFT =====
df = fetch("7516976")
df["week"] = pd.to_datetime(df["week"])
df = df.sort_values("week")

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
ax.plot(df["week"], df["avg_price_pct"], color=ORANGE, linewidth=3, label="Average")
ax.plot(df["week"], df["median_price_pct"], color=BROWN_DARK, linewidth=2.5, linestyle="--", label="Median")
first, last = df.iloc[0], df.iloc[-1]
ax.annotate(f"{first['avg_price_pct']:.1f}%", xy=(first["week"], first["avg_price_pct"]),
            xytext=(5, 10), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono")
ax.annotate(f"{last['avg_price_pct']:.1f}%", xy=(last["week"], last["avg_price_pct"]),
            xytext=(5, 10), textcoords="offset points", fontsize=12, fontweight="bold", color=ORANGE,
            fontfamily="Space Mono")
ax.set_title("Average implied probability per trade has drifted from 20% to 10% in eight months",
             fontsize=13, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Implied probability (%)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.legend(loc="upper right", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False)
ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.set_ylim(0, max(df["avg_price_pct"].max(), df["median_price_pct"].max())*1.2)
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "03_implied_probability_drift.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("03 ✓")


# ===== CHART 04: BET SIZE DISTRIBUTION =====
sql = """
SELECT
    CASE
        WHEN contracts_traded * price / 100.0 < 2    THEN '1: Under $2'
        WHEN contracts_traded * price / 100.0 < 5    THEN '2: $2-$5'
        WHEN contracts_traded * price / 100.0 < 10   THEN '3: $5-$10'
        WHEN contracts_traded * price / 100.0 < 20   THEN '4: $10-$20'
        WHEN contracts_traded * price / 100.0 < 50   THEN '5: $20-$50'
        WHEN contracts_traded * price / 100.0 < 200  THEN '6: $50-$200'
        ELSE                                              '7: $200+'
    END AS bucket,
    COUNT(*) AS num_trades,
    ROUND(SUM(contracts_traded * price / 100.0), 0) AS total_cash
FROM kalshi.trade_report
WHERE starts_with(report_ticker, 'KXMVE') AND contracts_traded > 0 AND price > 0
GROUP BY 1 ORDER BY 1
"""
r = requests.post('https://api.dune.com/api/v1/query', headers={**headers, 'Content-Type': 'application/json'},
                  json={'name': 'NB05 Bet Size Buckets', 'query_sql': sql})
qid = r.json()['query_id']
r = requests.post(f'https://api.dune.com/api/v1/query/{qid}/execute', headers=headers)
eid = r.json()['execution_id']
while True:
    time.sleep(4)
    if requests.get(f'https://api.dune.com/api/v1/execution/{eid}/status', headers=headers).json()['state'] == 'QUERY_STATE_COMPLETED':
        break
rows = requests.get(f'https://api.dune.com/api/v1/execution/{eid}/results', headers=headers).json()['result']['rows']
df = pd.DataFrame(rows).sort_values("bucket")
df["label"] = df["bucket"].str.split(": ", expand=True)[1]
df["pct_trades"] = df["num_trades"]/df["num_trades"].sum()*100
df["pct_cash"] = df["total_cash"]/df["total_cash"].sum()*100

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
x = range(len(df))
ax.bar([i-0.2 for i in x], df["pct_trades"], width=0.4, color=ORANGE, label="% of trades", edgecolor=CREAM, linewidth=2)
ax.bar([i+0.2 for i in x], df["pct_cash"], width=0.4, color=BROWN_DARK, label="% of total cash", edgecolor=CREAM, linewidth=2)
ax.set_xticks(list(x))
ax.set_xticklabels(df["label"], color=BROWN_DARK)
ax.set_title("Small bets dominate trade count, large bets dominate handle",
             fontsize=14, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_ylabel("Share (%)", fontsize=10, color=BROWN_DARK)
ax.set_xlabel("Bet size (USD)", fontsize=10, color=BROWN_DARK)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.legend(loc="upper right", frameon=False, fontsize=11, labelcolor=BROWN_DARK)
ax.grid(axis="x", visible=False)
ax.grid(axis="y", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "04_bet_size_distribution.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("04 ✓")


# ===== CHART 05: FEE REVENUE BY PRODUCT =====
df = fetch("7576002").sort_values("Est. Kalshi Fee Revenue ($)", ascending=True)
df["fee_m"] = df["Est. Kalshi Fee Revenue ($)"] / 1e6
top = df[df["fee_m"] >= 1].copy()
other_total = df[df["fee_m"] < 1]["fee_m"].sum()
if other_total > 0:
    top = pd.concat([pd.DataFrame([{"Product": "Other (8 products)", "fee_m": other_total}]), top], ignore_index=True)

fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
bars = ax.barh(top["Product"], top["fee_m"], color=ORANGE, edgecolor=CREAM, linewidth=2)
for bar, val in zip(bars, top["fee_m"]):
    ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height()/2,
            f"${val:,.1f}M", va="center", fontsize=11, color=BROWN_DARK, fontweight="bold",
            fontfamily="Space Mono")

total_fees = df["fee_m"].sum()
ax.set_title(f"Sports Multi-Game alone produced ${df[df['Product']=='Sports Multi-Game']['fee_m'].iloc[0]:.1f}M of an estimated ${total_fees:.0f}M in Kalshi fees",
             fontsize=12, fontweight="bold", pad=18, loc="left", color=BROWN_DARK)
ax.set_xlabel("Estimated fees (USD millions)", fontsize=10, color=BROWN_DARK)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.0f}M"))
ax.grid(axis="y", visible=False)
ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED)
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.text(0.98, 0.05, f"Total: ${total_fees:,.1f}M", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=13, fontweight="bold", color=CREAM,
        fontfamily="Space Mono",
        bbox=dict(boxstyle="round,pad=0.6", facecolor=BROWN_DARK, edgecolor="none"))
add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "05_fee_revenue_by_product.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("05 ✓")


# ===== DONUT HELPER =====
def make_predicted_donut(values, labels, title, save_path, inner_label_threshold=4.0):
    total = sum(values)
    pcts = [v/total*100 for v in values]
    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.set_aspect('equal')
    ax.set_xlim(-1.6, 4.8)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')

    cumulative = 90
    # Shadow
    for v in values:
        angle = v/total * 360
        shadow = Wedge((0.04, -0.06), 1.0, cumulative - angle, cumulative,
                       width=0.42, facecolor="#000", alpha=0.15, edgecolor="none", zorder=1)
        ax.add_patch(shadow)
        cumulative -= angle

    cumulative = 90
    wedges = []
    for v, c, pct in zip(values, PALETTE[:len(values)], pcts):
        angle = v/total * 360
        wedge = Wedge((0, 0), 1.0, cumulative - angle, cumulative,
                      width=0.42, facecolor=c, edgecolor=CREAM, linewidth=3, zorder=3)
        ax.add_patch(wedge)
        wedges.append(wedge)
        if pct >= inner_label_threshold:
            mid = np.radians(cumulative - angle/2)
            r = 0.78
            x, y = r*np.cos(mid), r*np.sin(mid)
            ax.text(x, y, f"{pct:.1f}%", ha="center", va="center",
                    fontsize=15, fontweight="bold", color=CREAM, zorder=5,
                    fontfamily="Space Mono",
                    path_effects=[path_effects.withStroke(linewidth=3, foreground=BROWN_DARK)])
        cumulative -= angle

    ax.text(0, 0.10, fmt_money(total), ha="center", va="center", fontsize=24, fontweight="bold",
            color=BROWN_DARK, fontfamily="Space Mono")
    ax.text(0, -0.12, "Total Handle", ha="center", va="center", fontsize=10, color=BROWN_MUTED,
            fontfamily="Space Mono")

    ax.text(-1.6, 1.15, title, fontsize=15, fontweight="bold", color=BROWN_DARK, ha="left", va="top",
            fontfamily="Space Mono")

    legend_x = 1.6
    for i, (label, pct, v, c) in enumerate(zip(labels, pcts, values, PALETTE[:len(values)])):
        y = 0.9 - i * 0.16
        ax.add_patch(patches.Rectangle((legend_x, y - 0.04), 0.12, 0.08, facecolor=c, edgecolor="none"))
        ax.text(legend_x + 0.18, y, label, fontsize=11, color=BROWN_DARK, va="center", ha="left",
                fontfamily="Space Mono")
        ax.text(legend_x + 2.1, y, f"{pct:.2f}%", fontsize=11, color=BROWN_MUTED, va="center", ha="right",
                fontweight="bold", fontfamily="Space Mono")
        ax.text(legend_x + 3.05, y, fmt_money(v), fontsize=11, color=ORANGE, va="center", ha="right",
                fontweight="bold", fontfamily="Space Mono")

    add_edge_bars(fig)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight", facecolor=CREAM)
    plt.close()


df = fetch("7506442")
df["Handle ($)"] = pd.to_numeric(df["Handle ($)"])

# 06 — Product
d = df.sort_values("Handle ($)", ascending=False)
make_predicted_donut(d["Handle ($)"].tolist(), d["Series"].tolist(),
    "Sport Multi-Game and Cross Category account for 95% of exotic handle",
    CHARTS_DIR / "06_handle_by_product.png", 8.0)
print("06 ✓")

# 07 — Type
d = df.groupby("Type")["Handle ($)"].sum().sort_values(ascending=False).reset_index()
make_predicted_donut(d["Handle ($)"].tolist(), d["Type"].tolist(),
    "Multi-game parlays alone account for 59% of total exotic handle",
    CHARTS_DIR / "07_handle_by_type.png", 4.0)
print("07 ✓")

# 08 — Category
d = df.groupby("Category")["Handle ($)"].sum().sort_values(ascending=False).reset_index()
make_predicted_donut(d["Handle ($)"].tolist(), d["Category"].tolist(),
    "63% of handle is Sports, with effectively zero outside sports + cross-category",
    CHARTS_DIR / "08_handle_by_category.png", 2.0)
print("08 ✓")


# ===== CHART 09: LAUNCH TIMELINE =====
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
r = requests.post('https://api.dune.com/api/v1/query', headers={**headers, 'Content-Type': 'application/json'},
                  json={'name': 'NB05 Launch Timeline', 'query_sql': sql})
qid = r.json()['query_id']
r = requests.post(f'https://api.dune.com/api/v1/query/{qid}/execute', headers=headers)
eid = r.json()['execution_id']
while True:
    time.sleep(4)
    if requests.get(f'https://api.dune.com/api/v1/execution/{eid}/status', headers=headers).json()['state'] == 'QUERY_STATE_COMPLETED':
        break
rows = requests.get(f'https://api.dune.com/api/v1/execution/{eid}/results', headers=headers).json()['result']['rows']
df = pd.DataFrame(rows)
df["launch_date"] = pd.to_datetime(df["launch_date"])
df["last_date"] = pd.to_datetime(df["last_date"])
today = pd.to_datetime("2026-05-25")
df["is_active"] = (today - df["last_date"]).dt.days < 21
df = df.sort_values("handle", ascending=True)

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)
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
        ax.text(row["last_date"] + pd.Timedelta(days=3), i, label, ha="left", va="center",
                fontsize=10, color=BROWN_DARK, fontweight="bold", fontfamily="Space Mono")

events = [
    ("Exotics Launch", "2025-09-17"),
    ("Grammys", "2026-02-02"),
    ("Super Bowl LIX", "2026-02-08"),
    ("Oscars", "2026-03-15"),
    ("March Madness", "2026-03-16"),
]
for name, date in events:
    d = pd.to_datetime(date)
    ax.axvline(d, color=BROWN_DARK, linestyle=":", alpha=0.4, linewidth=1)
    ax.text(d, len(df) - 0.3, name, ha="center", va="bottom", fontsize=8, color=BROWN_DARK,
            fontweight="bold", fontfamily="Space Mono")

ax.axvline(today, color=BROWN_DARK, linewidth=1.5, alpha=0.8)
ax.text(today, -0.9, "TODAY", ha="center", va="top", fontsize=9, color=BROWN_DARK, fontweight="bold",
        fontfamily="Space Mono")

ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["product"].values, fontsize=10, color=BROWN_DARK, fontfamily="Space Mono")
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.tick_params(colors=BROWN_DARK, labelsize=9)
ax.set_xlim(pd.to_datetime("2025-08-25"), pd.to_datetime("2026-06-20"))
ax.set_ylim(-1.4, len(df) + 0.2)
ax.set_title("Eleven combo products launched in phases, two still carry the platform",
             fontsize=13, fontweight="bold", pad=20, loc="left", color=BROWN_DARK)
ax.grid(axis="y", visible=False)
ax.grid(axis="x", alpha=0.2, color=BROWN_MUTED)

from matplotlib.patches import Patch
legend_items = [
    Patch(facecolor=ORANGE, label="Active"),
    Patch(facecolor=BROWN_MUTED, label="Dormant"),
]
ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=10, labelcolor=BROWN_DARK)

add_edge_bars(fig)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "09_launch_timeline.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
plt.close()
print("09 ✓")

print("\nAll 10 charts regenerated in Predicted theme.")
