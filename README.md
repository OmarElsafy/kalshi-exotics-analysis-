# Kalshi Exotics Analysis

A data analysis and methodology study of Kalshi's exotic Combo (parlay markets) (KXMVE) — combining Dune Analytics, Kalshi's public API, and trade-level microstructure analysis.

**Live dashboard:** [dune.com/Ommiii/klashi-exotics](https://dune.com/Ommiii/klashi-exotics)

---

## Headline findings

*Snapshot: Sep 17 2025 - Jun 1 2026*

| | |
|---|---|
| Notional volume since launch | **$14.0B** |
| Cash exchanged (handle) | **$1.42B** |
| Total trades | **32,457,465** |
| Estimated Kalshi fee revenue | **~$60M** (taker fees, trade-by-trade) |
| Effective fee rate | **~4.5% of handle** |
| Median trade size | **$9.30** (mean $44, 4.7x skew) |
| Largest single stake | **$176,010** |
| Extreme longshots (priced 0-2c) | **20% of trades, 4.6% of handle** |
| Two products carry | **96% of handle** |

---

## What's in this repo

```
.
├── methodology/
│   └── methodology_notes.md      # 50 documented analytical decisions
├── notebooks/
│   ├── 01_kalshi_api_metadata.ipynb     # API exploration, KXMVE structure
│   ├── 03_trade_report_audit.ipynb      # Trade-level grain verification
│   └── 04_fee_revenue_estimation.ipynb  # Fee revenue estimation methodology
├── dashboard/
│   ├── intro_widget.md           # Dashboard intro text
│   ├── launch_timeline_widget.md # KXMVE launch timeline
│   ├── premium_widget.md         # Handle / notional explainer
│   └── queries_inventory.md      # All dashboard query IDs
└── queries/
    ├── base_kalshi_weekly_by_category.sql
    ├── sub1c_corrected_queries.sql   # corrected SQL after the sub-1c truncation catch
    └── dune_queries/             # JSON dumps of each query
```

The June 2026 data snapshot (`data_snapshot_2026-06-02.json`) and the supporting
correction data (`data_sub1c_*.json`, `data_implied_prob_buckets_corrected.json`,
etc.) are the frozen source of truth; every chart is rebuilt from them.

---

## Methodology highlights

This project documents 81 numbered methodology decisions in [`methodology/methodology_notes.md`](methodology/methodology_notes.md). A few of the most important:

- **Defining exotics structurally:** `report_ticker LIKE 'KXMVE%'` (Kalshi's deterministic prefix), not the derived `category` column.
- **Notional vs handle:** distinguishing potential payout from actual cash exchanged.
- **Cross-Category composition:** empirical sampling showed 99.89% of "Cross-Category" parlays are all-sports legs despite the name.
- **Trade grain verification:** confirmed `kalshi.trade_report` is 1 row per trade, not per leg.
- **Trade-by-trade fee computation:** applying Kalshi's parabolic fee formula `0.07 x contracts x P x (1-P)` to each trade individually rather than aggregate prices, a ~40% correction over the aggregate approach.
- **Sub-1c data-truncation catch (notes 73-81):** discovered that Dune's `trade_report.price` stores prices as integer cents and *truncates*, so all trades priced 0.1c-0.9c were stored as `0` and silently dropped by a `price > 0` filter. Cross-validated against Kalshi's API (`yes_price_dollars`) to recover ~2.9M missing trades. True trade count is **32.46M, not 29.56M**. The corrected SQL for every affected query is in [`queries/sub1c_corrected_queries.sql`](queries/sub1c_corrected_queries.sql).

---

## Reproducing the analysis

1. Get a [Dune Analytics](https://dune.com) API key
2. Replace `YOUR_DUNE_API_KEY` placeholders in the notebooks
3. Notebook 01 — explore Kalshi API and verify series metadata
4. Notebook 03 — verify trade_report row grain
5. Notebook 04 — estimate fee revenue trade-by-trade
6. All Dune queries referenced are in [`dashboard/queries_inventory.md`](dashboard/queries_inventory.md)

---

## Data sources

| Source | Used for |
|---|---|
| `kalshi.market_report` (Dune) | Daily volume, open interest, price ranges, settlement status |
| `kalshi.trade_report` (Dune) | Per-trade rows: `contracts_traded`, `price`, `report_ticker` |
| Kalshi public API | Series metadata, parlay leg structure (`mve_selected_legs`) |

---

## License

MIT
