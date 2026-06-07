"""
Handle distribution by price point (1¢–99¢).
Handle = contracts_traded × price / 100 per trade, summed by price tick.
"""
import os
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

CHARTS_DIR = Path("../charts")
API_KEY = os.environ["DUNE_API_KEY"]  # set via: export DUNE_API_KEY=...
headers = {"X-Dune-API-Key": API_KEY, "Content-Type": "application/json"}

BG          = "#FAF6F0"
ORANGE      = "#CC5A1A"
BROWN_DARK  = "#3B2314"
BROWN_MUTED = "#8B6F5E"

plt.rcParams.update({
    "font.family": "Space Mono",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "figure.facecolor": BG, "axes.facecolor": BG,
    "text.color": BROWN_DARK,
})

SQL = """
SELECT
    price AS price_tick,
    SUM(contracts_traded * price / 100.0) AS handle_usd
FROM kalshi.trade_report
WHERE report_ticker LIKE 'KXMVE%'
  AND date >= '2025-09-17'
  AND price BETWEEN 1 AND 99
GROUP BY price
ORDER BY price
"""

print("Fetching cached results from query 7622663...")
qid = 7622663
rows = requests.get(
    f"https://api.dune.com/api/v1/query/{qid}/results",
    headers={"X-Dune-API-Key": API_KEY}
).json()["result"]["rows"]

df = pd.DataFrame(rows)
df["price_tick"] = df["price_tick"].astype(int)
df["handle_usd"] = df["handle_usd"].astype(float)
df = df.set_index("price_tick").reindex(range(1, 100), fill_value=0).reset_index()
df.columns = ["price_tick", "handle_usd"]
df["handle_m"] = df["handle_usd"] / 1e6

print(f"\nTop 10 price points by handle:")
print(df.nlargest(10, "handle_m")[["price_tick", "handle_m"]].to_string())

# ── Chart ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
fig.patch.set_facecolor(BG)

# Find peak for colour logic — highlight the peak bar
peak_price = df.loc[df["handle_m"].idxmax(), "price_tick"]
colors = [ORANGE if p == peak_price else BROWN_MUTED for p in df["price_tick"]]

ax.bar(df["price_tick"], df["handle_m"], width=0.8,
       color=colors, alpha=0.85, zorder=3)

# Annotate peak
peak_h = df.loc[df["price_tick"] == peak_price, "handle_m"].values[0]
ax.annotate(
    f"{peak_price}¢ peak\n${peak_h:.1f}M",
    xy=(peak_price, peak_h),
    xytext=(peak_price + 6, peak_h * 0.9),
    fontsize=8, fontfamily="Space Mono", color=ORANGE,
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2),
)

# Grid
for y in ax.get_yticks():
    ax.axhline(y, color=BROWN_MUTED, linewidth=0.3, alpha=0.4, zorder=1)

ax.set_xlim(0, 100)
ax.set_ylim(0, df["handle_m"].max() * 1.2)
ax.set_xlabel("Implied probability (price per contract, ¢)", fontsize=9,
              color=BROWN_MUTED, labelpad=8)
ax.set_ylabel("Handle ($M)", fontsize=9, color=BROWN_MUTED, labelpad=8)
ax.tick_params(axis="both", labelsize=8, colors=BROWN_MUTED, length=0)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x)}¢"))
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.0f}M" if x > 0 else "$0"))

ax.set_title(
    "Handle concentrates at low-to-mid implied probabilities — the 1¢ floor barely registers in cash terms",
    fontsize=11, fontweight="bold", color=BROWN_DARK, pad=14, loc="left"
)

fig.text(0.01, 0.01, "Source: Dune · kalshi.trade_report · KXMVE% since Sep 17 2025",
         fontsize=7, color=BROWN_MUTED)

plt.tight_layout(rect=[0, 0.03, 1, 1])
out = CHARTS_DIR / "handle_per_price.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"\nSaved: {out}")
print(f"Dune query: https://dune.com/queries/{qid}")
