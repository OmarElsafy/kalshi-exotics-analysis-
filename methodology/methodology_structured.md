# Kalshi Exotics, Structured Methodology
**Analysis period:** September 17, 2025 to June 1, 2026
**Author:** Omar El Safy
**Dashboard:** [dune.com/Ommiii/klashi-exotics](https://dune.com/Ommiii/klashi-exotics)

---

## 1. Data Sources

| Source | What it contains | How we used it |
|---|---|---|
| `kalshi.market_report` (Dune) | Daily aggregates per market ticker, notional volume, open interest, high/low price | Volume, OI, and listed-market counts |
| `kalshi.trade_report` (Dune) | One row per trade, ticker, contracts, price, timestamp | Handle, fee estimation, implied probability distribution, bet size distribution, ever-traded counts |
| Kalshi public API | Series metadata, market status, leg composition (`mve_selected_legs`) | Cross-Category composition sample, product taxonomy, launch dates |

**Grain audit:** `kalshi.trade_report` confirmed at one row per trade via direct inspection (Notebook 03). A 5-leg parlay is one trade on one ticker, leg count does not multiply rows.

**Time range:** September 17, 2025 (exotic launch date) to June 1, 2026. All queries filter on `date >= '2025-09-17' AND date <= '2026-06-01'` against the frozen June 1 snapshot.

---

## 2. Key Definitions

**Exotic / KXMVE**
Any market whose `report_ticker` starts with `KXMVE` (Kalshi's MultiVariate Event prefix). This is the deterministic source-aligned definition, verified against Kalshi's public API. We do not use `category = 'Exotics'` from Dune because Dune relabels 7 of 11 KXMVE families (e.g. NFL parlays appear as "Sports"). The `KXMVE%` prefix is the only reliable filter.

**Notional**
`SUM(contracts_traded)`, each contract has a $1 face value, so notional equals contract count expressed in dollars. This is the potential payout if every contract wins, not the cash exchanged. The $14.0B headline figure is notional.

**Handle**
`SUM(contracts_traded × price / 100)` per trade row, the actual cash that changed hands. Always less than notional. The $1.42B figure is handle. Notional-to-handle ratio is approximately 9.8x because the average exotic trades at ~10% implied probability.

**Implied Probability**
Price expressed as a percentage. A contract trading at 15 cents = 15% implied probability = roughly 6-to-1 odds. Price is probability in a binary prediction market.

**Price floor and tick size**
Kalshi prices combo contracts in tenth-of-a-cent (deci-cent) steps. The true minimum tradeable price is **0.1 cent**, not 1 cent. Trades occur across the full 0.1c to 99c range. Note that Dune's `kalshi.trade_report.price` column stores price as an integer number of cents and truncates, so all sub-1c trades are stored as `price = 0` (see Section 3, "Data-quality correction").

**Open Interest**
A stock (snapshot), not a flow. Plotted as a daily value. Never summed across days, that would double-count. Peak OI is `MAX(open_interest)` over the period.

**Taker Fee**
`0.07 × contracts × P × (1 - P)` where P = trade price in decimal. Kalshi's published formula. Maker fee is 0% on standard markets; 0.25% on major event days (treated as negligible in aggregate).

---

## 3. Analytical Methods

### Handle calculation
Applied per row in `kalshi.trade_report`: `contracts_traded × price / 100`. Summed across all KXMVE rows for the period. This gives real cash exchanged, not notional.

### Fee estimation
Applied Kalshi's taker fee formula (`0.07 × contracts × P × (1-P)`) per row across all 32.5 million KXMVE trades, then summed. 

The shortcut, applying the formula to the average price (~10%) and scaling by notional, overstates fees by approximately 40%. The reason is Jensen's inequality: the fee function `P × (1-P)` is concave, so applying it to the mean of P is always larger than the mean of `P × (1-P)`. At low implied probabilities (1% to 15%), this nonlinearity is significant. The correct approach is row-level calculation.

Result: **~$60M taker fees, ~4.5% effective rate on handle.** (Fee revenue is unaffected by the sub-1c correction: sub-cent trades carry a near-zero fee because `P x (1-P)` collapses as P approaches zero, but they were already counted in the fee query.)

### Cross-Category composition
Pulled 135,426 open `KXMVECROSSCATEGORY` parlays via the Kalshi public API (May 2026). For each parlay, inspected the `mve_selected_legs` field to identify the parent series category of each leg. 99.89% of open parlays have all-Sports legs. 0.11% mix Sports and Crypto. No Politics, Macro, or other-domain legs appear in current usage.

**Limitation of this sample:** open parlays only. Closed positions from resolved events (Oscars, Grammys, College Basketball Championship) are excluded because those markets have already settled and are not accessible via the default API endpoint. The all-time composition figure is likely 95% to 97% sports, but the directional story holds.

### Listed vs ever traded
Counted distinct `KXMVE%` tickers in `kalshi.market_report` (all-time listed = 37.1 million). Joined to `kalshi.trade_report` to identify which tickers appeared at least once (ever traded = 17.2 million, 47%). Tickers that never appeared in `trade_report` are classified as never traded (53%).

### Implied probability drift
Weekly average and median implied probability per KXMVE trade, plotted as a time series (query 7516976). The headline drift (roughly 20% to 10% over eight months) is **contract-weighted** (handle ÷ notional): each contract counts equally, so the figure is pulled down by the growing volume of cheap-longshot contracts. A trade-weighted version (each trade counts once, regardless of size) is much flatter, around 22% to 21%. The two measures answer different questions: contract-weighted shows where the volume sits; trade-weighted shows what the typical trade looks like. The "halving" is a volume-mix effect, not a change in the typical trade.

### Extreme-longshot share over time
Monthly share of trades priced below 1 cent (the sub-cent floor) and at 2 cents or below (extreme longshots), query 7598456. The sub-cent share roughly doubled from about 6% in October 2025 to 12% by May 2026, with a sharp dip in February. The dip is the only month where the absolute count of sub-cent trades fell (down 17%) while total trading still grew (up 16%): the Super Bowl ends the NFL season, the sports calendar narrows, and there are fewer concurrent games to stack into many-leg parlays, while casual money floods the single marquee game at normal odds. The share tracks how many games are running at once, because extreme longshots require many simultaneous events to build from. This is consistent with a mechanical (product-mix) driver, though leg counts are not directly observable in the trade data.

### Platform context
Kalshi-wide handle and notional since September 17, 2025 drawn from `kalshi.market_report` with no ticker filter. Exotic share = KXMVE handle / total handle. Broken out weekly as a stacked area chart (query 7600498).

### Data-quality correction: recovering sub-1c trades
**The catch.** The 1-cent price floor looked suspiciously clean, so we cross-validated Dune against Kalshi's own trades API (`yes_price_dollars`, full decimal precision). The check exposed a silent truncation: Dune's `kalshi.trade_report.price` is stored as an integer number of cents and rounds down, so every trade priced between 0.1c and 0.9c is stored as `price = 0`. Our standard `price > 0` filter had therefore been deleting them.

**Proof.** Pulling the same tickers from Kalshi's API returned real executed trades at 0.1c, 0.5c, 0.8c and so on, each stored as `0` in Dune. Confirmed both directions: a 1.8c trade is stored as `1` (truncated, not rounded). So the flooring affects every price, and a Dune bar labelled "Nc" actually spans Nc.0 to Nc.9.

**Scale.** Pinned to the snapshot window, the recovered sub-cent trades number **2,894,623** (8.9% of activity), carrying 5.0 billion contracts but only about **$18M of handle (1.3%)**. The true trade count is **32,457,465**, not the 29,562,842 the `price > 0` filter reported.

**Reconstruction.** Dune can supply exact counts and contracts for the sub-cent bucket but not the internal price split. A random sample of 700 sub-cent tickers, priced via the Kalshi API, gives the shape: mode at 0.2c, contract-weighted mean **0.367c**. For Dune-only handle estimates we use an effective-price proxy: `price = 0` → 0.367c; `price = N` → N + 0.45c (the midpoint of the floored range). Exact figures use the API.

**What it changed.** Trade-count, distribution, floor-share and trade-size charts were rebuilt to include the sub-cent trades (and the affected Dune queries corrected in place). Handle, notional and the implied-probability averages were essentially unaffected, because they already swept the sub-cent trades into their denominators as zeros.

---

## 4. Validation

**Fee cross-check, Sportico**
Sportico independently reported total parlay hold at 14.7% of handle and 10.2% ex-fees for KXMVE trades (January to April 2026). The implied fee component from their figures: **4.5%**. Our trade-by-trade calculation: **~4.5%**. This is the closest available external validation and gives confidence the fee magnitude is correct.

**Grain audit, trade_report**
Confirmed one row per trade in `kalshi.trade_report` by direct inspection of the table structure and spot-checking multi-leg parlay tickers (Notebook 03). A parlay's leg count does not multiply its trade count.

**Category audit, Sports filter completeness**
Ran `SELECT category, COUNT(DISTINCT report_ticker), SUM(daily_volume)` against all Kalshi markets since September 17, 2025. "Sports" is the single comprehensive category for all non-exotic sports markets, 1,699 unique tickers, $57.38B volume. There is no fragmented sports taxonomy. The filter `WHERE category = 'Sports' AND report_ticker NOT LIKE 'KXMVE%'` captures the full non-exotic sports book. One exception: the "Mentions" category contains both standalone mention markets and the `KXMVEMENTIONSSINGLE` series, the `NOT LIKE 'KXMVE%'` filter handles this correctly (query 7608163).

**Notional vs handle, Dune schema**
Confirmed that `kalshi.market_report.daily_volume` is notional (contract count × $1 face value) by inspecting the schema alongside `high`/`low` price columns. Handle is derived by applying price to the trade-level data in `kalshi.trade_report`.

### Per-price-point distribution (trade count and handle)
Two charts showing activity across every price tick, one for trade count and one for handle. Both include the sub-cent bucket (`price = 0`, the 0.1c to 0.9c trades). A separate bucketed view groups prices into ranges, with the bottom bucket defined as 0c to 2c "extreme longshots."

**Trade count by price tick** (query 7622547 → `Fig15b`)
`COUNT(*)` grouped by `price`, filtered `BETWEEN 0 AND 99`. Sub-cent contracts (`price = 0`) are 8.9% of all trades, the single largest bar, larger than any whole-cent tick (1c is 6.4%). More trades print below a single cent than on every price above 50 cents combined. Power-law decay above the floor. Caveat: the sub-cent bar aggregates nine deci-cent ticks (0.1c to 0.9c), so as a single tick the most-traded price is 1c; as a group, sub-cent is largest.

**Handle by price tick** (query 7622663 → `Fig15a`)
`SUM(contracts_traded * effective_price / 100.0)` grouped by `price`, where effective price reconstructs the floored value (see "Data-quality correction"). Handle is a broad plateau from the floor to about 35c, peaking at **26c ($24.3M)**. As a bucket *share* the 0c-2c extreme longshots are only 4.6% of handle (against 20.1% of trades), so the floor is a small share of cash. Per individual tick, however, the sub-cent and 1c ticks each carry roughly $18M to $23M, near the peak, because the contract volume there is enormous. The accurate framing is "the cheapest trades are a small share of handle," not "the floor barely registers."

**Why notional was not charted:** Notional = `SUM(contracts_traded)` per tick. Low-price contracts are cheap so bettors buy more per trade, inflates notional at the floor mechanically, not behaviourally. Adds noise, not a third distinct story. Trade count and handle cover the two meaningful dimensions.

**Column name note:** Timestamp column in `kalshi.trade_report` is `date` (varchar, YYYY-MM-DD). Filter: `WHERE date >= '2025-09-17'`. Not `block_time`.

---

## 5. Limitations

**No user ID column**
`kalshi.trade_report` does not contain a user identifier. All bettor-level analysis (bet size distribution, the $176K largest stake) describes *trade* profiles, not *trader* profiles. The $176K stake could be one person or ten acting simultaneously. We cannot deduce trader concentration, loyalty, or repeat behaviour from this dataset.

**Listed ≠ confirmed available to trade**
We assume every `KXMVE` ticker in `market_report` was presented to bettors with a live price. If markets are priced via RFQ and a market maker never quoted a specific combination, that ticker would appear in our "listed" count but was never actually tradeable. Some portion of the 53% dead-on-arrival rate may reflect "never quoted" rather than "available but unwanted." We cannot separate these two cases from the data we have.

**Trade data completeness**
We assume Dune's mirror of `kalshi.trade_report` is a complete historical record. The grain audit confirms structural integrity (one row per trade) but does not confirm that every historical trade is present. Gaps in Dune's ingestion would cause the "ever traded" count to be understated and the dead-on-arrival rate to be overstated.

**Cross-Category composition is a point-in-time sample**
The 99.89% all-sports finding is based on 135,426 open parlays in May 2026. Resolved parlays from event-specific products (Oscars, Grammys, March Madness) are excluded. The figure likely understates non-sports usage slightly; the directional conclusion (overwhelmingly sports) is robust.

**Small-N products**
CBB Championship shows 100% ever-traded rate. This is based on ~30K listed tickers, a much smaller combination surface than Sport Multi-Game's 22 million. Percentages across products are not operationally comparable; a 100% rate on 30K is trivially achievable where 48% on 22 million is a structural outcome.

**Fee estimate is taker-only**
The ~$60M figure covers taker fees only. Maker fees are 0% on standard markets and approximately 0.25% on major event days. The major-event maker fee component was treated as negligible in aggregate, but this introduces a small downward bias in the total fee estimate.

**No RFQ quote stream data**
We do not have access to historical RFQ quote logs. Market maker identity, concentration, and quoting behaviour cannot be derived from the public Dune tables. Any claim about who quotes the combo book or how many market makers are active is inferred, not measured.

---

*Underlying notes and working decisions: `methodology/methodology_notes.md`*
*Full query inventory: `dashboard/queries_inventory.md`*
