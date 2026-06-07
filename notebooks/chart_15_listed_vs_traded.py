"""
Chart 15 — % of Listed KXMVE Markets That Ever Received a Trade
Data from Dune query 7607014. Hardcoded from dashboard results.
Predicted theme: Space Mono, cream #FAF6F0, orange #CC5A1A, dark brown #3B2314.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from pathlib import Path

CHARTS_DIR = Path("../charts")

BROWN_DARK  = "#3B2314"
ORANGE      = "#CC5A1A"
BROWN_MUTED = "#8B6F5E"
CREAM       = "#FAF6F0"
TAN         = "#D4B896"

plt.rcParams.update({
    "font.family": "Space Mono",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.grid": False,
    "figure.facecolor": CREAM, "axes.facecolor": CREAM,
    "text.color": BROWN_DARK,
})

# Data — sorted descending by % ever traded
products = [
    "CBB\nChamp",
    "Cross\nCategory",
    "Sport\nMulti-Game",
    "NBA\nMulti Ext",
    "NBA\nSingle",
    "NFL\nMulti",
    "NFL\nMulti Ext",
    "NFL\nMention",
    "NBA\nMulti",
    "NFL\nSingle",
    "NFL\nMulti (v1)",
]
pcts = [100, 94, 48, 14, 13, 11, 11, 10, 8, 9, 5]

# Sort descending
paired = sorted(zip(pcts, products), reverse=True)
pcts_sorted  = [p for p, _ in paired]
labels_sorted = [l for _, l in paired]

# Colour: highlight top two and Sport Multi, mute the rest
def bar_color(p):
    if p >= 90:   return ORANGE
    if p >= 40:   return BROWN_DARK
    return BROWN_MUTED

colors = [bar_color(p) for p in pcts_sorted]

fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor(CREAM)

x = np.arange(len(labels_sorted))
bars = ax.bar(x, pcts_sorted, color=colors, width=0.6, zorder=3)

# Value labels above bars
for bar, val in zip(bars, pcts_sorted):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1.5,
        f"{val}%",
        ha="center", va="bottom",
        fontsize=10, fontweight="bold",
        color=BROWN_DARK,
    )

# 50% reference line
ax.axhline(50, color=ORANGE, linewidth=0.8, linestyle="--", alpha=0.5, zorder=2)
ax.text(len(labels_sorted) - 0.45, 51.5, "50%", fontsize=8, color=ORANGE, alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(labels_sorted, fontsize=9, color=BROWN_DARK)
ax.set_ylim(0, 115)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.tick_params(axis="y", labelsize=9, color=BROWN_MUTED, labelcolor=BROWN_MUTED)
ax.tick_params(axis="x", length=0)

# Horizontal grid lines only
for y in [25, 50, 75, 100]:
    ax.axhline(y, color=BROWN_MUTED, linewidth=0.4, linestyle="-", alpha=0.3, zorder=1)

ax.set_title(
    "% of Listed KXMVE Markets That Ever Received a Trade",
    fontsize=13, fontweight="bold", color=BROWN_DARK,
    pad=16, loc="left",
)
ax.set_ylabel("Ever traded (%)", fontsize=9, color=BROWN_MUTED, labelpad=8)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=ORANGE,      label="≥90%  — near-full absorption"),
    Patch(facecolor=BROWN_DARK,  label="40–90% — majority traded"),
    Patch(facecolor=BROWN_MUTED, label="<40%  — majority never traded"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=8,
          framealpha=0, labelcolor=BROWN_DARK)

# Source footnote
fig.text(0.01, 0.01, "Source: Dune query 7607014 · kalshi.market_report",
         fontsize=7, color=BROWN_MUTED, ha="left")

plt.tight_layout(rect=[0, 0.03, 1, 1])
out = CHARTS_DIR / "15_listed_vs_traded.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=CREAM)
plt.close()
print(f"Saved: {out}")
