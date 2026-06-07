# Dashboard Query Inventory — `dune.com/Ommiii/klashi-exotics`

Snapshot of the queries currently powering the Kalshi Exotics Dune dashboard.
Pulled via Dune REST API on 2026-05-15.

Effective source of truth across the board is `kalshi.market_report`, but **5 of 10 queries reach it via a fork** (`query_5910819`, owned by `datadashboards`) instead of going direct.
None of the queries touch `kalshi.trade_report` (the raw trade-level table).

---

## Inventory

| Query ID | Name | Source | What it returns |
|---|---|---|---|
| 7495941 | Total Volumes Of Exotics | `kalshi.market_report` ✅ | Headline totals (all-time) |
| 7413453 | Combo's Share of Exotics | `kalshi.market_report` ✅ | % of exotic *volume* classified as "combo" |
| 7413505 | Exotics Share Of Open Interest | `kalshi.market_report` ✅ | % of exotic *open interest* classified as "combo" |
| 7411455 | Segments of Exotics on Kalshi | `kalshi.market_report` ✅ | 2-bucket split (combo-like vs other) |
| 7412131 | Kalshi exotics by segment (Vol+OI) | `kalshi.market_report` ✅ | 4-bucket split by hardcoded report_ticker |
| 7396205 | Exotics Share of Weekly Volume | `query_5910819` 🔗 | Weekly exotics share since 2026-02-23 |
| 7409732 | All Time Kalshi Exotics Volume | `query_5910819` 🔗 | Same headline as 7495941, via fork |
| 7409748 | Exotics Share of Total Kalshi Volume (Monthly) | `query_5910819` 🔗 | Most-recent-month exotics share |
| 7409718 | Exotics + Kalshi Weekly Volumes | `query_5910819` 🔗 | Most-recent-week exotics share |
| 7493445 | Cumulative Exotics Volume Kalshi Since Launch | `query_5910819` 🔗 | Weekly + cumulative volume |
| **5910819** | *Weekly Kalshi Volume by Tag* (owned by `datadashboards`) | `kalshi.market_report` | Weekly rollup: `(week, category, sum(daily_volume))` |

Legend: ✅ direct read · 🔗 forks another user's query

---

## Trader Behavior section (added 2026-05-24)

| Query ID | Name | Source | What it returns |
|---|---|---|---|
| 7545755 | Parlay Odds Distribution — Implied Probability | `kalshi.trade_report` ✅ | p10/p25/median/mean/p75/p99/max of trade prices |
| 7550808 | Bet Size Distribution — Cash Per Trade | `kalshi.trade_report` ✅ | Percentile distribution of cash per trade |
| 7545751 | How People Bet by Series | `kalshi.trade_report` ✅ | Per-series trades, handle, notional, skew ratio |
| 7557750 | Bet Size Buckets — Cash Per Trade | `kalshi.trade_report` ✅ | Bucketed bet size distribution (% trades, % cash) |

---

## Fee Revenue section (added 2026-05-25)

| Query ID | Name | Source | What it returns |
|---|---|---|---|
| 7576002 | Fee Revenue by Product | `kalshi.trade_report` ✅ | Per-product trades, handle, notional, fee revenue, avg implied prob |
| 7576182 | Total Estimated Fee Revenue (Counter) | `kalshi.trade_report` ✅ | Single value: total estimated taker fees ($55M) |
| 7576183 | Effective Fee Rate (Counter) | `kalshi.trade_report` ✅ | Single value: fee % of handle (4.51%) |

---

## Article-specific charts (added 2026-05-28)

| Query ID | Name | Source | What it returns | Chart in article |
|---|---|---|---|---|
| 7598456 | Floor Trades (1¢) Monthly | `kalshi.trade_report` ✅ | % of trades at the 1¢ price floor per month | Chart 10 |
| 7598460 | OI Over Time — Exotic vs Total Kalshi | `kalshi.market_report` ✅ | Daily OI snapshots, exotic and platform-wide | Chart 11 |
| 7521948 | Kalshi Exotic Handle — Monthly | `kalshi.market_report` ✅ | Monthly handle, cumulative handle + notional, avg/median implied prob | Charts 01, 02, 12 |
| 7598462 | Parlay Odds Histogram | `kalshi.trade_report` ✅ | Trade count + % by price bucket (1¢ floor to 70¢+) | Chart 13 |

---

## Article chart → query map (full)

| Chart # | File | Query ID(s) | Section in article |
|---|---|---|---|
| 00 | `00_platform_perspective.png` | ad-hoc (uses `kalshi.market_report`) | Opening |
| 01 | `01_monthly_handle.png` | 7521948 | Growth Story |
| 02 | `02_cumulative_handle_notional.png` | 7521948 | Opening |
| 03 | `03_implied_probability_drift.png` | 7516976 | Average Bettor |
| 04 | `04_bet_size_distribution.png` | 7557750 | Median Bet |
| 05 | `05_fee_revenue_by_product.png` | 7576002 | Fee Methodology |
| 06 | `06_handle_by_product.png` | 7506442 | Eleven Products |
| 07 | `07_handle_by_type.png` | 7506442 | Eleven Products |
| 08 | `08_handle_by_category.png` | 7506442 | Eleven Products |
| 09 | `09_launch_timeline.png` | ad-hoc (uses `kalshi.market_report`) | Eleven Products |
| **10** | `10_floor_trades_monthly.png` | **7598456** | Implied Probability |
| **11** | `11_oi_over_time.png` | **7598460** | Super Bowl / OI |
| **12** | `12_post_nfl_durability.png` | 7521948 | Growth Story |
| **13** | `13_parlay_odds_histogram.png` | **7598462** | Implied Probability |


### About query 5910819 (the upstream fork)

```sql
SELECT DATE_TRUNC('week', DATE(date)) as week,
       category,
       SUM(daily_volume) as "Volume"
FROM kalshi.market_report
GROUP BY 1, 2
```

That's the entire query. It's a trivial weekly rollup of `kalshi.market_report` grouped by category. **Anything that query does, you can do directly in your own queries with the same 4 lines of SQL.**

---

## How the queries classify "exotic" and "combo"

### Filter: what counts as an exotic
All five queries use the same filter:

```sql
WHERE category = 'Exotics'
```

This is sourced from `kalshi.market_report.category`. Confirmed via Kalshi API (`series.category`) that this label is Kalshi's own — well-founded provenance.

### Sub-classification: combo vs other

Two different approaches are in use across the dashboard — they don't agree with each other:

**Approach A — string-pattern heuristic** (queries 7413453, 7413505, 7411455):

```sql
CASE
  WHEN lower(report_ticker) LIKE '%crosscategory%'
    OR lower(report_ticker) LIKE '%multi%'
    OR lower(ticker_name)   LIKE '%basket%'
    OR lower(ticker_name)   LIKE '%index%'
  THEN 'Combo' ELSE 'Other'
END
```

**Approach B — exact match on hardcoded tickers** (query 7412131):

```sql
CASE
  WHEN report_ticker = 'KXMVECROSSCATEGORY'   THEN 'Cross-category exotics'
  WHEN report_ticker = 'KXMVECBCHAMPIONSHIP'  THEN 'BC Championship exotics'
  WHEN report_ticker = 'KXMVEOSCARS'          THEN 'Oscars exotics'
  ELSE 'Other exotics'
END
```

---

## Issues I see

### 1. Two different classifiers running in parallel
Approaches A and B will not give the same answer to "what's combo volume?" The "combo share" tiles (Approach A) and the "segment breakdown" tile (Approach B) can show numbers that don't reconcile. Decide on one definition.

### 2. Both classifiers miss `KXMVESPORTSMULTIGAMEEXTENDED`
The API metadata (notebook 01) showed `KXMVESPORTSMULTIGAMEEXTENDED` is a major MVE family — it accounted for a meaningful share of the markets we sampled. It's not in Approach B's hardcoded list, and it only catches Approach A's net by accident (because "MULTIGAME" matches `%multi%`). Worth confirming, but likely undercounted in 7412131's "Cross-category" / "BC Championship" / "Oscars" buckets — it falls into "Other".

### 3. The heuristic is brittle
String matches like `%multi%` will catch anything with "multi" in the ticker — including non-MVE markets, in principle. False positives are possible.

### 4. Same logic duplicated across multiple queries
Three queries hardcode the same `LIKE` pattern. Any future change to the classifier has to be made in three places. This is a maintenance smell — a single source-of-truth list of subtypes (in a reference table or a CTE that's reused) would fix it.

### 5. Nothing in this dashboard answers the leg-counting question
None of these queries touch `kalshi.trade_report`. The 1-vs-N counting question is about *trade rows*, not market rollups. To audit it we need to query `trade_report` directly, which we haven't done yet.

### 6. External dependency on `datadashboards`' query 5910819
Five of your queries fork `query_5910819`, owned by another Dune user. If that user deletes, renames, or modifies it, **five of your dashboard tiles silently break (or silently change numbers)**. There's no way to be notified. The upstream is also opaque: today it's a 4-line rollup, but the owner can change it anytime without telling us. This is the kind of dependency you don't want in something you'd put on a portfolio.

### 7. Two queries are duplicates
7495941 (direct) and 7409732 (via fork) compute literally the same thing — all-time exotics / sports / total Kalshi volume. Both can exist if they're used in different dashboard tiles, but it should be intentional, not accidental. Pick one.

---

## Replacement plan (ties into ETL flow)

**Transform stage (T2):** Use the deterministic, API-derived classifier instead of the heuristic. Strip the second segment of any KXMVE ticker:

```
KXMVECROSSCATEGORY-...        → cross_category
KXMVESPORTSMULTIGAMEEXTENDED  → sports_multi
KXMVEOSCARS-...               → oscars
KXMVECBCHAMPIONSHIP-...       → championship
KXMVE...                      → other_mve
```

Build this once in `dim_market`, then every dashboard query joins to it.

**Audit stage (T4):** Run the leg-counting check against `kalshi.trade_report` to verify Dune's row grain — settles the 1-vs-N question once and for all.

---

## Standardization plan: one source of truth

**Goal:** every query on this dashboard reads from `kalshi.market_report` directly. No external forks.

**Recommended pattern.** Create one base query *that you own* — the canonical weekly rollup. All other queries reference it via Dune's `query_NNNNNN` syntax. This keeps things DRY (Don't Repeat Yourself) but the dependency is now on a query you control, not someone else's.

Suggested base query (`base_kalshi_weekly_by_category`):

```sql
-- Owned by Ommiii. Single source of truth for weekly Kalshi volume by category.
SELECT
  DATE_TRUNC('week', DATE(date)) AS week,
  category,
  SUM(daily_volume)              AS volume,
  SUM(open_interest)             AS open_interest
FROM kalshi.market_report
GROUP BY 1, 2
```

Then every downstream query becomes a `SELECT ... FROM query_<your_id>`. If you ever change the grain or filters, you change one place.

**Rewrite checklist:**

| Query ID | Action |
|---|---|
| 7495941 | Keep as-is — direct, simple, correct. ⭐ The "good" pattern. |
| 7413453 / 7413505 / 7411455 / 7412131 | Eventually re-point to use `dim_market` subtypes (from notebook 02) instead of heuristic LIKE patterns |
| 7396205 / 7409732 / 7409748 / 7409718 / 7493445 | Re-point from `query_5910819` (`datadashboards`) → your new `base_kalshi_weekly_by_category` |
| 7409732 | Consider retiring (duplicate of 7495941) |

This work is independent of notebook 02/03 and can be done in parallel or after. It's a 30-minute cleanup once the new base query exists.

---

## ⚠️ SUB-1¢ CORRECTION (June 2026)

**Discovery:** `kalshi.trade_report.price` is stored as an **integer cent** and **truncates (floors)**. All trades priced 0.1¢–0.9¢ are stored as `price = 0`. Queries filtering `price > 0` silently dropped **~2.9M real sub-1¢ trades**. True trade count is **32,457,465** (not 29,562,842). Verified against Kalshi's API (`yes_price_dollars`).

Corrected SQL for all affected queries: [`queries/sub1c_corrected_queries.sql`](../queries/sub1c_corrected_queries.sql).

| Query ID | Powers | Correction |
|---|---|---|
| 7622547 | Fig 15b (per-tick trade count) | include `price = 0` |
| 7622663 | Fig 15a (handle per tick) | include `price = 0` + flooring proxy |
| 7623140 | Fig 15 (paired trades vs handle) | rebucket; bottom = 0-2¢ extreme longshots |
| 7598456 | Fig 16a/16b (monthly) | reframe "1¢ floor" → sub-1¢ (`price=0`) and 0-2¢ (`price<=2`) |
| 7557750 | Fig 18 (trade-size buckets) | include `price = 0` (was summing to 29.56M) |
| 7576002 | Fig 19 (fee by product) | include sub-1¢ (~+$1.8M; fee≈0 at p≈0) |

**Effective-price proxy (Dune only):** `price = 0 → 0.367¢` (API sample mean); `price = N → N + 0.45¢` (midpoint of floored deci-cent range). For exact price/handle, use Kalshi API `yes_price_dollars`.

**Unaffected:** all `market_report` queries (notional, handle, OI, composition) and the implied-probability queries (7545755, 7521948, 7576002 mean/median) — these were contract-weighted and already included `price=0` as zeros, so they move <0.5pp.

*Status: corrected SQL saved to repo. Live Dune queries NOT yet overwritten — pending owner review (overwriting changes the published dashboard).*
