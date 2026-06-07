"""
Implied probability histogram — variable-width bins, 1¢ floor isolated.
Data from Dune query 7623168.
"""
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

CHARTS_DIR = Path("../charts")
API_KEY = os.environ["DUNE_API_KEY"]  # set via: export DUNE_API_KEY=...

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

LABEL_MAP = {
    "1c floor": "1¢ floor",
    "2-5c":     "2–5¢",
    "5-15c":    "5–15¢",
    "15-30c":   "15–30¢",
    "30-50c":   "30–50¢",
    "50c+":     "50¢+",
}

QID = 7623168
rows = requests.get(
    f"https://api.dune.com/api/v1/query/{QID}/results",
    headers={"X-Dune-API-Key": API_KEY}
).json()["result"]["rows"]

df = pd.DataFrame(rows)
df["pct_of_trades"] = df["pct_of_trades"].astype(float)
df = df.sort_values("sort_order").reset_index(drop=True)
df["display_label"] = df["label"].map(LABEL_MAP).fillna(df["label"])

print(df[["display_label", "pct_of_trades"]].to_string())

# ── Chart ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.5))
fig.patch.set_facecolor(BG)

colors = [ORANGE if i == 0 else BROWN_DARK for i in range(len(df))]
bars = ax.bar(df["display_label"], df["pct_of_trades"],
              color=colors, width=0.55, zorder=3)

# Value labels above bars
for bar, val in zip(bars, df["pct_of_trades"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        f"{val:.1f}%",
        ha="center", va="bottom",
        fontsize=9.5, fontfamily="Space Mono",
        color=BROWN_DARK
    )

# 1¢ floor annotation
floor_pct = df["pct_of_trades"].iloc[0]
ax.annotate(
    "Structural floor:\nparlays below 1%\ntrade at exactly 1¢",
    xy=(0, floor_pct),
    xytext=(0.7, df["pct_of_trades"].max() * 0.82),
    fontsize=7.5, fontfamily="Space Mono", color=ORANGE,
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.1,
                    connectionstyle="arc3,rad=-0.25"),
    ha="left"
)

# Grid
for y in [5, 10, 15, 20, 25]:
    ax.axhline(y, color=BROWN_MUTED, linewidth=0.3, alpha=0.4, zorder=1)

ax.set_ylim(0, df["pct_of_trades"].max() * 1.3)
ax.set_ylabel("% of all trades", fontsize=9, color=BROWN_MUTED, labelpad=8)
ax.tick_params(axis="x", labelsize=9, length=0, colors=BROWN_DARK)
ax.tick_params(axis="y", labelsize=8, length=0, colors=BROWN_MUTED)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

ax.text(0.99, 0.97, "Bin widths vary — see methodology",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=7, color=BROWN_MUTED, style="italic")

ax.set_title(
    "Half of all exotic trades sit below 15¢ — the 1¢ floor is a structural outlier",
    fontsize=11, fontweight="bold", color=BROWN_DARK, pad=14, loc="left"
)

fig.text(0.01, 0.01,
         f"Source: Dune query {QID} · kalshi.trade_report · KXMVE% since Sep 17 2025",
         fontsize=7, color=BROWN_MUTED)

plt.tight_layout(rect=[0, 0.03, 1, 1])
out = CHARTS_DIR / "implied_prob_bins.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"\nSaved: {out}")
print(f"Dune query: https://dune.com/queries/{QID}")
