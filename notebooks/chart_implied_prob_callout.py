"""
Implied probability summary stats callout chart.
1200 x 300px, Predicted theme variant.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

CHARTS_DIR = Path("../charts")

BG       = "#F5F0E8"
PRIMARY  = "#8B3A0F"   # dark rust — headline boxes
DARK     = "#2C1810"   # very dark brown — text
MUTED    = "#A07860"   # muted rust — secondary labels
BOX_MUTED = "#E8E0D4"  # soft box for percentile cards

fig, ax = plt.subplots(figsize=(12, 3))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 12)
ax.set_ylim(0, 3)
ax.axis("off")

# ── Title ──────────────────────────────────────────────────────────────────
ax.text(
    0.1, 2.72,
    "Implied probability distribution — all trades since launch",
    fontsize=11, fontfamily="monospace", fontweight="bold",
    color=DARK, va="top"
)

# ── Helper: draw a stat card ───────────────────────────────────────────────
def stat_card(x, y, w, h, value, label, sublabel=None,
              headline=False, bg=BOX_MUTED):
    # box
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04",
        linewidth=0,
        facecolor=PRIMARY if headline else bg,
        zorder=2
    )
    ax.add_patch(rect)

    text_color = BG if headline else DARK
    label_color = "#F0C090" if headline else MUTED

    # value
    ax.text(
        x + w / 2, y + h * 0.62,
        value,
        ha="center", va="center",
        fontsize=18 if headline else 14,
        fontfamily="monospace",
        fontweight="bold",
        color=text_color,
        zorder=3
    )
    # main label
    ax.text(
        x + w / 2, y + h * 0.25,
        label,
        ha="center", va="center",
        fontsize=8,
        fontfamily="monospace",
        color=label_color,
        zorder=3
    )
    # sublabel (descriptive context)
    if sublabel:
        ax.text(
            x + w / 2, y + h * 0.10,
            sublabel,
            ha="center", va="center",
            fontsize=6.5,
            fontfamily="monospace",
            color=label_color,
            zorder=3,
            style="italic"
        )

# ── Layout ─────────────────────────────────────────────────────────────────
card_h = 1.9
card_y = 0.4

# Headline stats — Mode + Median (orange boxes, left)
stat_card(0.10, card_y, 1.70, card_h, "1%",    "Mode",   "most common price",  headline=True)
stat_card(1.95, card_y, 1.70, card_h, "15.3%", "Median", "midpoint of all trades", headline=True)

# Divider
ax.plot([3.85, 3.85], [card_y + 0.2, card_y + card_h - 0.2],
        color=MUTED, linewidth=0.8, alpha=0.5, zorder=2)

# Mean
stat_card(4.00, card_y, 1.50, card_h, "20.3%", "Mean", "pulled up by large bets")

# Percentile cards — right side
stat_card(5.65, card_y, 1.50, card_h, "2.1%",  "P10",  "bottom 10% of trades")
stat_card(7.25, card_y, 1.50, card_h, "5.6%",  "P25",  "bottom 25% of trades")
stat_card(8.85, card_y, 1.50, card_h, "30.6%", "P75",  "top 25% of trades")
stat_card(10.45, card_y, 1.50, card_h, "81.5%", "P99", "top 1% of trades")

plt.tight_layout(pad=0)
out = CHARTS_DIR / "implied_prob_callout.png"
plt.savefig(out, dpi=100, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"Saved: {out}")
