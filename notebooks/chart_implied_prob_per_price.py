"""
Implied probability histogram at every price point (1¢–99¢).
One bar per integer price tick — shows floor spike and full distribution shape.
"""
import os
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from pathlib import Path

CHARTS_DIR = Path("../charts")
API_KEY = os.environ["DUNE_API_KEY"]  # set via: export DUNE_API_KEY=...
headers = {"X-Dune-API-Key": API_KEY, "Content-Type": "application/json"}

BG          = "#FAF6F0"
ORANGE      = "#CC5A1A"
BROWN_DARK  = "#3B2314"
BROWN_MUTED = "#8B6F5E"
CREAM       = "#FAF6F0"
HIGHLIGHT   = "#CC5A1A"   # 1¢ floor spike

plt.rcParams.update({
    "font.family": "Space Mono",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "figure.facecolor": BG, "axes.facecolor": BG,
    "text.color": BROWN_DARK,
})

# ── Fetch per-price-point trade counts ─────────────────────────────────────
SQL = """
SELECT
    price AS price_tick,
    COUNT(*) AS trade_count
FROM kalshi.trade_report
WHERE report_ticker LIKE 'KXMVE%'
  AND date >= '2025-09-17'
  AND price BETWEEN 1 AND 99
GROUP BY price
ORDER BY price
"""

print("Creating query...")
r = requests.post(
    "https://api.dune.com/api/v1/query",
    headers=headers,
    json={"name": "KXMVE implied prob per price point", "query_sql": SQL}
)
qid = r.json().get("query_id")
print(f"Query ID: {qid}")

r = requests.post(f"https://api.dune.com/api/v1/query/{qid}/execute", headers=headers)
eid = r.json()["execution_id"]
print(f"Execution ID: {eid}")

print("Waiting for results...")
while True:
    time.sleep(5)
    s = requests.get(
        f"https://api.dune.com/api/v1/execution/{eid}/status", headers=headers
    ).json()["state"]
    print(f"  {s}")
    if s == "QUERY_STATE_COMPLETED":
        break
    if s in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
        raise RuntimeError(f"Query failed: {s}")

rows = requests.get(
    f"https://api.dune.com/api/v1/execution/{eid}/results", headers=headers
).json()["result"]["rows"]

df = pd.DataFrame(rows)
df["price_tick"] = df["price_tick"].astype(int)
df["trade_count"] = df["trade_count"].astype(float)
df = df.set_index("price_tick").reindex(range(1, 100), fill_value=0).reset_index()
df.columns = ["price_tick", "trade_count"]
total = df["trade_count"].sum()
df["pct_of_trades"] = df["trade_count"] / total * 100

print(f"Rows returned: {len(df)}")
print(df[df["pct_of_trades"] > 1].to_string())

# ── Build chart ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
fig.patch.set_facecolor(BG)

colors = [ORANGE if p == 1 else BROWN_MUTED for p in df["price_tick"]]

ax.bar(df["price_tick"], df["pct_of_trades"], width=0.8,
       color=colors, alpha=0.85, zorder=3)

# Annotate the 1¢ spike
floor_pct = df.loc[df["price_tick"] == 1, "pct_of_trades"].values[0]
ax.annotate(
    f"1¢ floor\n{floor_pct:.1f}% of all trades",
    xy=(1, floor_pct),
    xytext=(8, floor_pct * 0.85),
    fontsize=8, fontfamily="Space Mono", color=ORANGE,
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2),
    ha="left"
)

# Annotate 50¢ (coin flip)
p50 = df.loc[df["price_tick"] == 50, "pct_of_trades"].values[0]
if p50 > 0:
    ax.annotate(
        f"50¢ — coin flip\n{p50:.1f}%",
        xy=(50, p50),
        xytext=(55, p50 + 0.4),
        fontsize=7.5, fontfamily="Space Mono", color=BROWN_MUTED,
        arrowprops=dict(arrowstyle="->", color=BROWN_MUTED, lw=0.9),
    )

# Grid lines
for y in [1, 2, 3, 4, 5]:
    ax.axhline(y, color=BROWN_MUTED, linewidth=0.3, alpha=0.4, zorder=1)

ax.set_xlim(0, 100)
ax.set_ylim(0, max(df["pct_of_trades"]) * 1.18)
ax.set_xlabel("Implied probability (price per contract, ¢)", fontsize=9,
              color=BROWN_MUTED, labelpad=8)
ax.set_ylabel("% of all trades", fontsize=9, color=BROWN_MUTED, labelpad=8)
ax.tick_params(axis="both", labelsize=8, colors=BROWN_MUTED, length=0)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x)}¢"))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))

ax.set_title(
    "Most trades cluster at low implied probabilities — the 1¢ floor alone accounts for 7% of all trades",
    fontsize=11, fontweight="bold", color=BROWN_DARK, pad=14, loc="left"
)

fig.text(0.01, 0.01, "Source: Dune · kalshi.trade_report · KXMVE% since Sep 17 2025",
         fontsize=7, color=BROWN_MUTED)

plt.tight_layout(rect=[0, 0.03, 1, 1])
out = CHARTS_DIR / "implied_prob_per_price.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"\nSaved: {out}")
