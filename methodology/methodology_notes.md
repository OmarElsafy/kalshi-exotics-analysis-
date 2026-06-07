# Methodology Notes — Kalshi Exotics Dashboard

Running log of data-science decisions and *why* we made them.

Two purposes:
1. **Learning record** — concepts and reasoning, for me
2. **Dashboard methodology widget** — short version ready to paste on Dune (bottom of this file)

---

## Part 1 — Learning record

### 1. Source-first thinking
**Principle:** Define the entity at its source before auditing derived labels.
**Why:** If you reason from a downstream label without checking what it derives from, you can't tell whether a bug is in the label, the rollup, or the source.
**How we applied it:** Went to the Kalshi public API first. Confirmed that the structural marker for exotics is the `KXMVE` ticker prefix (= "Kalshi MultiVariate Event"), and Kalshi's own `series.category` field carries the "Exotics" label.
**Important correction:** Our first sample (KXMVECROSSCATEGORY only) suggested Dune's `category` column matched Kalshi's. **It does not** — across all 11 KXMVE series, Dune relabels 7 of 11 as Sports/Politics/etc. Don't trust the Dune `category` column for exotic identification. Trust the `KXMVE` prefix.

### 2. Always verify with N>1 samples
**Principle:** A single confirmation doesn't validate a label across a population. Sample multiple cases before concluding "X is true everywhere."
**Why:** Confirming one series matched is not the same as confirming all series match. The mismatch on sports parlays was hidden because we only checked one example.
**How we applied it:** Now systematically check all 11 KXMVE series' API category against Dune's category.

### 3. KXMVE = Kalshi MultiVariate Event
**Principle:** Kalshi prefixes all multi-leg parlay markets with `KXMVE`. This is a deterministic structural marker, not a heuristic.
**Why it matters:** Defining exotics as `report_ticker LIKE 'KXMVE%'` is bulletproof — same rule Kalshi uses internally.
**11 known families** (sorted by traded volume):

| Series | Subtype | Title (from API) | Example real market |
|---|---|---|---|
| KXMVESPORTSMULTIGAMEEXTENDED | sports_multi | MVE Sport Multi Game | 4-leg NBA player props (Mobley 10+, Allen 10+, Harden 15+, Wembanyama 20+) |
| KXMVECROSSCATEGORY | cross_category | MVE Cross Category | 3-leg cross-sport (Liverpool, Tampa Bay, Atlanta — EPL + 2 MLB) |
| KXMVENFLSINGLEGAME | sports_single | MVE NFL Single Game | multi-outcome bets within one NFL game |
| KXMVENFLMULTIGAMEEXTENDED | sports_multi | MVE NFL Multi Game Extended | multi-game NFL parlays |
| KXMVENBASINGLEGAME | sports_single | MVE NBA Single Game | 2-leg in-game (spread + total) |
| KXMVECBCHAMPIONSHIP | championship | MVE College Basketball Championship | 2-leg tournament progression (Illinois + Michigan) |
| KXMVEOSCARS | awards | MVE Oscars | 3-leg awards (actress + intl film + picture) |
| KXMVEGRAMMYS | awards | MVE Grammys | (no live example — wrapped) |
| KXMVENFLMULTIGAME | sports_multi | MVE NFL Multi Game | (no live example — offseason) |
| KXMVENBAMULTIGAMEEXTENDED | sports_multi | MVE NBA Multi Game | (no live example) |
| KXMVEMENTIONSSINGLE | mentions | MVE Mention | ⚠️ borderline — Kalshi categorizes as `Mentions`, not `Exotics`; "SINGLE" suggests single-leg |

### 4. Two-dimensional thinking: Subject vs Structure
**Principle:** Every market has two independent properties — what it's about (Subject) and how it's built (Structure). These shouldn't be collapsed into one "category" label.
**How we applied it:**
- Subject axis: Sports, Politics, Awards, Cross-category, Mentions
- Structure axis: Single-market vs Exotic (multi-leg)
- A sports parlay is `Subject=Sports, Structure=Exotic`. Counts as exotic in our dashboard. Also appears under "Sports" in Kalshi's external numbers. Both right — different lenses.
- Dashboard rule: include all KXMVE in exotic totals; break down by subject within exotics.

### 5. Parlay structure: one ticker per parlay
**Principle:** Each Kalshi parlay is its own market with its own ticker. Legs are metadata (`mve_selected_legs`), not separately tradable.
**Why it matters:** When someone trades a 5-leg parlay, it's **one trade on one ticker**, not five. If `kalshi.trade_report` is row-per-trade, a parlay generates one row regardless of leg count.
**How we applied it:** Strongly suggests the dashboard's bundle-counting is correct and any reported number that's ~3× higher (e.g., Sam McQuillan's $8.5B in 5 months) is leg-inflated. Empirical confirmation still pending in notebook 03.

### 6. Stocks vs flows
**Principle:** Some metrics are *flows* (events per period — sum across time is valid). Some are *stocks* (snapshots at a point in time — summing across time double-counts).
**Examples:** Volume is a flow. Open Interest is a stock.
**How we applied it:**
- All-time volume = `SUM(daily_volume)` ✅
- All-time OI = `MAX(open_interest)` (peak) or latest day, never `SUM`
- Time-series OI = plot daily snapshots; don't aggregate across days

### 7. Don't fork other users' queries
**Principle:** Reading directly from a Dune-curated table is fine. Forking another user's query is risky — they can change/delete it silently.
**How we applied it:** Replaced `query_5910819` (owned by `datadashboards`) with our own base query.

### 8. Base queries consolidate *repeated* logic
**Principle:** Don't route through a base layer for its own sake. A base query is justified when the same aggregation appears in 3+ downstream queries.
**How we applied it:** Created weekly base query for the 5 time-series tiles sharing the same rollup. Did NOT create a daily OI base — only one OI chart, so direct is cleaner.

### 9. Granularity should fit the metric
**Principle:** Match the time grain to the behavior of what you're measuring.
**How we applied it:** OI on parlays = daily (spikes within hours). Volume = weekly/monthly (trends).

### 10. Heuristic classifiers are brittle
**Principle:** String matching like `LIKE '%multi%'` catches false positives and misses true cases. Prefer deterministic rules.
**How we applied it:** Replacing `LIKE '%crosscategory%' OR '%multi%'` with `report_ticker LIKE 'KXMVE%'` plus an exact-match subtype classifier on the 11 known families.

### 11. Selection bias: "open" ≠ "all"
**Principle:** A snapshot of currently-active items is not the historical universe.
**How we applied it:** Decided to pull all parlay statuses (open + closed + settled) for the full reference table.

### 12. Market count is misleading for short-lived products
**Principle:** "How many markets exist?" is a different question than "how much trades?"
**Why:** Kalshi auto-generates ~50k parlay combinations; most never trade.
**How we applied it:** Dashboard headlines use traded volume, not market counts.

### 13. Fact vs dimension tables
**Principle:** A *fact* is something that happened (a trade). A *dimension* describes the entity involved. Join fact → dim to slice facts by properties.
**How we applied it:** Building `dim_market` (one row per parlay, with subtype + leg count) as the dimension table.

### 14. The empirical limit of the public Kalshi API
**Principle:** Kalshi's public API hides fully-settled events from default queries. We can verify open markets directly, but historical structural proof must come from the raw trade table.
**How we applied it:** 5 of 11 KXMVE series directly verified structurally (live markets with populated `mve_selected_legs`). The other 6 are inferred from naming + metadata consistency. Notebook 03 will close the gap by inspecting Dune trade rows.

### 15. Dimension overlap: a sports parlay is both
**Principle:** When a single entity legitimately belongs to two categories (sports AND exotic), don't force-pick. Use both, on separate axes.
**Why it matters:** Forcing a choice (Kalshi API: structure wins; Dune: subject wins) misrepresents the other dimension and creates apparent conflict between dashboards.
**How we applied it:** Define exotic = KXMVE% (structural). Within exotics, break down by domain (sports/entertainment/mixed). Document in the methodology widget that sports parlays appear in both this dashboard's exotic total and external "sports" reports — both correct, different framings.

### 16. Series-level naming ≠ leg composition
**Principle:** Kalshi's series ticker (`KXMVECROSSCATEGORY`, etc.) tells you what TEMPLATE the parlay was built from — not what's actually in its legs.
**Why it matters:** A "cross-category" parlay might in practice be all-sports (e.g., EPL + 2 MLB games). The label says "mixed" but the composition is single-domain. Counting it as "non-sports" would be wrong.
**How we applied it:** For now, `cross_category` lives in a "Mixed / Unknown" bucket — we acknowledge we can't sub-classify it without leg-level data. Notebook 02 will fix this by parsing `mve_selected_legs` from the API and tagging each parlay's actual composition.

### 17. Hierarchical > flat taxonomy when groups exist
**Principle:** When subtypes naturally cluster into a parent concept, use two levels (Domain → Variant) instead of one flat list.
**Why it matters:** A flat list of 6 subtypes treats "awards" and "sports_multi" as equally distant from each other. A hierarchy reveals that 5 of the 6 are sports-of-some-kind — which is the real story.
**How we applied it:** Restructured the subtype classifier into Domain {Sports, Entertainment, Mixed/Unknown} × Variant {multi_game, single_game, championship, awards, cross_category, mentions}. Dashboards can then show domain mix at the top level and drill into variants.

### 18. Be honest about what you don't yet know
**Principle:** When the data can't currently answer a question, name the limitation explicitly rather than papering over it with a plausible-sounding guess.
**Why it matters:** Hidden assumptions become hidden bugs. Explicit limitations become a clear roadmap for the next analysis.
**How we applied it:** "Mixed / Unknown" was originally named as such because we didn't know what was inside cross-category parlays until we pulled leg metadata. The dashboard methodology widget said this out loud rather than hiding it.

### 19. Classification granularity: series-level vs entity-level
**Principle:** When labeling, decide whether you're classifying *the template* (the series) or *the individual entity* (the parlay). They can give different answers.
**Why it matters:** A "Cross Category" series template can produce parlays that are 99.89% all-sports — the template name lies. Series-level classification is cheap (one SQL CASE on a column) but imprecise. Entity-level classification is precise but requires joining to per-entity metadata (mve_selected_legs from the API).
**How we applied it:** Sampled 5,000 open `KXMVECROSSCATEGORY` parlays, looked up each leg's parent series category. **99.89% of cross-category parlays have all-Sports legs; 0.3% mix Sports + Crypto; 0.02% are all-Crypto.** This empirical finding lets us safely reclassify the entire series as Sports for the dashboard, with a transparent note about the 0.3% minority.

### 20. Defer precision until it's worth the cost
**Principle:** Pick the cheapest classification approach that answers your current question. Upgrade to a more precise one only when the minority cases start mattering to the story.
**Why it matters:** Always reaching for maximum precision burns effort on details that don't change conclusions. Always reaching for maximum simplicity buries real signals.
**How we applied it:** For the dashboard today, use series-level classification (fold cross-category into Sports). When notebook 02 produces a leg-level `dim_market`, switch to per-parlay classification — at that point, the 0.3% mixed cases become a meaningful sub-story worth surfacing.

### 22. Notional vs Premium volume — they are NOT the same number
**Principle:** "Volume" in prediction markets has two meanings. Always specify which.
**The two:**
- **Notional volume** = contracts traded × $1 face value. Each Kalshi binary contract has $1 face value, so notional volume effectively equals contract count expressed in dollars.
- **Premium volume** = contracts × actual trade price = the cash that actually exchanged hands. Always less than notional, by a factor of the average price.
**How we applied it:** `kalshi.market_report.daily_volume` is **notional** (we confirmed by inspecting the schema — no separate USD column, but `high`/`low` price columns exist alongside `daily_volume`). All our "$X.XX B" figures are notional. To compute premium: `SUM(daily_volume × (high + low) / 200)` per row. Dashboard tile labels should always say *"Notional Volume"* not just "Volume" or "USD Volume" to avoid misleading readers.
**Practical:** a $11B notional headline is honest *if you say "notional"*. The same number labeled "USD Volume" implies $11B in cash actually exchanged, which it doesn't. The dashboard must distinguish.

### 23. Calibrating notional → premium for Kalshi exotics
**Principle:** Once you have both notional and premium, the **ratio between them is the average trade price**. This number is interpretable — it tells you the typical implied probability.
**Why it matters:** For Kalshi exotics, premium/notional ≈ 9–12%. That means:
- The average exotic contract trades at ~10¢
- Implied probability of any individual parlay winning is ~10%
- This is economically rational — multi-leg parlays have low compounded probability
**Numbers (from leaderboard, May 2026):**
- Sports Multi-Game: $7.03B notional → $667M premium → **avg price 9.5%**
- Cross-Category: $3.50B notional → $426M premium → **avg price 12.2%**

**Cross-Category composition (re-sampled May 16, 2026):** Pulled all 135,426 open `KXMVECROSSCATEGORY` parlays via Kalshi API. 99.89% have all-Sports legs (73 distinct leg-series — 63 Sports, 10 Crypto). 0.106% mix Sports + Crypto. 2 parlays all-Crypto. No Politics, Macro, Mentions, or other-domain legs appear in current usage. The product is *designed* as cross-category; current trader *behavior* skews overwhelmingly cross-sport.
**How we applied it:** Add `avg_price_pct` as a column on the leaderboard. It's a more honest summary of how the market actually trades than volume alone.

### 24. Headlines: notional makes for the bigger number, premium for the truer one
**Principle:** Pick which "size" of exotic volume to lead with based on what the dashboard is *for*.
**The trade-off:**
- **Notional ($11.16B all-time)** → industry convention, bigger headline, what other dashboards and analysts use. Comparable to Sam McQuillan's claimed numbers. But ~10× the actual cash that exchanged hands.
- **Premium (~$1.1B all-time exotic, extrapolating)** → reflects actual money exchanged. Smaller but more honest. The number a regulator or skeptic would prefer.
**How we applied it:** Show both on the dashboard. Lead with notional (industry standard), put premium next to it (honesty signal). The methodology widget explains the difference.

### 25. Most exotic markets are dead-on-arrival
**Principle:** Distinguish "exists" from "actively traded". Kalshi auto-generates parlay combinations as standalone markets; only a small fraction ever see real volume.
**Numbers (from leaderboard, May 2026):**
- Sports Multi-Game: 20.8M total markets, 30,671 currently active = **0.15% live rate**
- Cross-Sport: 5.05M total, 19,758 live = **0.39% live rate**
**How we applied it:** The leaderboard's `live_contracts` column flags this — for marketing or product analytics, the *live* count is more honest than the total. For storytelling, the gap itself is the story: *"Kalshi creates 100s of parlay shapes for every one that traders actually pick up."*

### 26. Median ≈ Mean for daily notional → activity is steady, not spike-driven
**Principle:** Compare central-tendency measures to learn about the distribution shape.
**Numbers:**
- Sports Multi: median daily $36.5M, mean $39.7M → 1.09× ratio
- Cross-Sport: median $40.5M, mean $46.0M → 1.14× ratio
**Interpretation:** Both ratios are close to 1, which means the distribution of daily volume is roughly symmetric — daily activity is steady, not dominated by occasional huge spike days. If we'd seen mean = 3× median, it would imply most volume comes from a few outlier days (a much spikier product).

### 27. Follow the source taxonomy by default; surface analytical reclassifications separately
**Principle:** When the source data (Kalshi) deliberately distinguishes two products, your *primary* taxonomy should preserve that distinction. Any reclassification based on empirical analysis (like "cross-category is 99.89% sports") goes on a *secondary* view, with the rationale stated.
**Why it matters:** Collapsing the source distinction silently looks like sloppy analysis; doing the reclassification on a separate tile with explicit reasoning looks like rigorous analysis. Same insight, very different signal.
**How we applied it:**
- **Primary leaderboard** uses Kalshi's taxonomy: Sports / Cross-Category / Entertainment / Mentions
- **Secondary "Composition-Adjusted View" tile** reclassifies cross-category as Sports (citing the 99.89% leg-composition finding) and presents the alternative breakdown
- **Methodology note** explains the difference: *"Cross-Category is its own bucket in Kalshi's product taxonomy but is 99.89% sports legs by composition. Both views are valid lenses on the same data."*

### 28. Detecting "live" markets in Dune
**Principle:** Status is a row-level field. To get the *current* state of each market, look at its most recent row.
**Kalshi's status values** (from `kalshi.market_report.status`, frequency from our probe):
- `active` — currently tradeable (live). ~3.6% of all rows.
- `finalized` — fully settled (paid out). ~96% of rows.
- `determined` — result known, not yet finalized. <0.1%.
- `closed` — trading stopped, awaiting settlement. <0.1%.
**How we derive "live" in Dune:**
1. For each `ticker_name`, find the row with the most recent `date` (using `ROW_NUMBER() OVER (PARTITION BY ticker_name ORDER BY date DESC) = 1`).
2. Filter where `status = 'active'`. That's a live market.
3. At the series level: count distinct live markets. If count > 0 → series_status = `Live`. Else → `Dormant`.
**Why this works:** A market that was active a month ago but finalized yesterday should not count as live today. Taking the most recent status per market avoids this stale-state bug. Series-level "Dormant" correctly captures seasonal series (NFL in May → no active markets → Dormant).
**Where to verify in Dune:**
```sql
-- Status distribution
SELECT status, COUNT(*) FROM kalshi.market_report GROUP BY 1 ORDER BY 2 DESC

-- Current status of a single market
SELECT status, date FROM kalshi.market_report
WHERE ticker_name = '<specific market>' ORDER BY date DESC LIMIT 1
```

### 29. "Average price" vs "average premium" are different questions
**Principle:** Don't conflate the **rate** at which something trades with the **size** of what trades.
**The two:**
- **Avg / median PRICE** = implied probability per trade = `SUM(premium) / SUM(notional)`. A behavior metric — risk appetite. Unit: % (or cents per contract).
- **Avg / median PREMIUM** = dollar size of cash flow per row/period. A size metric — activity intensity. Unit: dollars.
**When to use which:**
- "Are traders going for longer-shot parlays?" → use **price** (this is what answered the 20% → 9% finding)
- "How big is the typical trade / weekly cash flow?" → use **premium**
- "Who has the most premium?" → use **total premium** (composition metric, different again)
**How we applied it:** Queries 7516978 / 7521911 / 7521912 now return avg & median **price** per (week × group) for comparing risk appetite across Domain / Variant / Series. Separate queries for premium time-series exist for cash-flow size.

### 30. Question every chart: does it require mental arithmetic to extract meaning?
**Principle:** A chart earns its space by making the takeaway obvious *at a glance*. A chart that forces the reader to compare bars in their head, or trace a noisy line to estimate a trend, is doing too little work for the real estate it takes.
**When to keep a chart:**
- The takeaway is visible in one second (a counter, a clear monotonic curve, a single dominant slice)
- The chart shape itself encodes the insight (steepening curve = acceleration, divergence between two lines = distribution shift)
**When to kill or replace:**
- Per-period bars of an absolute metric (e.g., "Premium $ per week") — reader can't tell if any individual bar is good/bad without context. Cumulative shows the same data more meaningfully.
- Line charts with high noise and no smoothing
- Anything where you'd have to explain *"if you ignore weeks 1–5 and squint at weeks 6–12..."*
**Better substitutes for size metrics:**
- **Counter** = headline total at-a-glance ("Total Premium: $1.12B")
- **Cumulative area chart** = growth trajectory; shape encodes acceleration vs plateau
- **% change counter** = instant directional signal ("MoM Growth: +23%")
**How we applied it:** Dropped the "per-period Premium $ line chart" plan for daily/weekly/monthly. Replaced with: Total Premium counter + Cumulative Premium area chart + MoM growth counter. Three tiles, all answer in one glance, none require interpretation.

### 31. Price ≡ Implied Probability (the conceptual anchor)
**Principle:** For a Kalshi binary contract that pays $1 if YES wins, the price IS the market's implied probability of YES winning. Not "related to," not "approximately" — mathematically equivalent in a fair market.
**Why it matters:** When we say `avg_price_pct = 9.5%`, we mean "the typical exotic parlay traded at 9.5¢ per $1 contract → market implies 9.5% chance of winning → ~10× payout if it hits." This is the single most powerful unit translation on the dashboard — readers can re-frame any price as a probability or payout multiplier instantly.
**How we applied it:** Y-axes labeled "Implied Probability (%)" instead of "Price." Subtitles describe traders' "implied probability" rather than "what they paid." Same number, much clearer reading.

### 32. Time-series vs counter for the same metric
**Principle:** A counter answers *"what is it now?"*; a time series answers *"how has it been moving?"* Build the right one for the question — sometimes you need both.
**Example:** MoM growth %.
- Counter form (single number) tells you *"premium grew 23% last month"* — fast, glanceable, but no context for whether 23% is the norm or unusual.
- Time-series form (one bar per month since launch) tells you *"growth was 200%, 130%, 90%, ..., 23% — clearly decelerating as the base grows"* — way richer story.
**Decision rule:** if the metric is volatile/event-driven → counter is misleading on its own. If the metric's trajectory itself encodes the insight (acceleration, plateauing, regime shifts) → use the time series.
**How we applied it:** 7522233 = MoM growth single counter (for headline). 7522333 = MoM growth time series (for the maturity-curve story). Both are valid; they complement each other.

### 33. MoM/WoW % growth is misleading for young products (large-base problem)
**Principle:** % growth rates decelerate mathematically as the base grows, even when absolute growth is accelerating. For products under ~2 years old, the chart will show "decelerating growth" that ISN'T economically real.
**The trap:**
- Oct: $500K, +900% vs Sep → reader: "amazing growth"
- Apr: $300M, +15% vs Mar → reader: "growth is dying"
- Reality: April added $250M of new activity, Oct added $450K. April was 555× the absolute growth. The % distortion lies.
**When MoM/WoW % growth IS useful:** mature products with multi-year history where % rate has stabilized; comparing across products of similar maturity.
**Better substitute for young products:** absolute per-period values (monthly premium bars). Bar heights directly encode the size; bigger bar = bigger period. No math distortion.
**How we applied it:** Pulled MoM growth % charts from the dashboard plan. Replaced with monthly premium bars (period activity) + cumulative area chart (running total). The two together capture both "how big is this period" and "where are we cumulatively."

### 34. Don't over-claim — separate "observation" from "interpretation"
**Principle:** When you see a trend in aggregate data, list the possible drivers BEFORE asserting one. If multiple explanations fit equally well, say so out loud.
**The trap we almost fell into:**
- Observation: avg implied probability dropped from ~20% (Sep 2025) → ~9% (May 2026).
- Tempting interpretation: "Traders are taking more risk / going for longer-shot bets."
- Equally valid alternative interpretation: "Kalshi has launched parlay templates supporting more legs over time. More legs = mechanically lower combined probability, regardless of trader behavior."
**Why it matters:** A dashboard that says "traders are taking more risk" when the truth might be "Kalshi expanded the product" is a misread that someone reviewing the work could expose. Always frame as observation + competing interpretations until you have the data to disambiguate.
**How we applied it:** Updated the Premium widget text to present BOTH explanations (behavioral vs mechanical/mix shift). Noted that disambiguation requires per-parlay leg metadata from the Kalshi API (`mve_selected_legs`), which is notebook 02 work. The widget says: *"parlays are trading at lower implied probabilities — interpretation pending."*

### 35. Partial disambiguation possible from existing data
**Principle:** Even when you can't fully answer a question, look for a partial test using what you already have.
**How we applied it (in progress):** To partly separate "behavioral" from "mix-shift" interpretations of the implied-probability drop:
- Look at avg_price_pct *within a single series* (e.g., KXMVESPORTSMULTIGAMEEXTENDED) over time using query 7521912.
- If that one series' price also dropped 20% → 9%: behavioral shift within the product.
- If it stayed roughly flat: the overall drop is mostly the mix shifting toward newer/longer-leg series, not trader behavior.
This doesn't fully answer the leg-count question, but it gets us from "two equally plausible stories" to "one story is more plausible" without needing notebook 02.

### 36. Floor effects in extreme-value rankings
**Principle:** When a metric has a hard floor (or ceiling), ranking by that metric clusters many entities at the floor → not differentiating. Layer a second signal to break the ties meaningfully.
**Example:** Kalshi parlays trade at a minimum 0.5¢ price (tick floor). Sorting by "lowest price traded" returns ~hundreds of parlays tied at 0.5¢, all with identical "100× max payout" — uninformative.
**The fix:** Add a "did it actually hit?" filter. The interesting rows aren't "parlays that touched 0.5¢" but "parlays that touched 0.5¢ AND won." The combination of leverage potential + realization gives a meaningful ranking.
**How we applied it:** "Highest-Leverage Parlays" query rewritten to filter on `final_high >= 99 AND final_low >= 99` — only parlays whose final-day prices both converged to ~$1, indicating high-confidence YES settlement. Removes the noise of floor-priced losers.

### 37. Inferring outcomes when no outcome column exists
**Principle:** When the data doesn't have an explicit "outcome" or "winner" column, look at *price convergence at settlement*. Markets settle at known values — for Kalshi binary contracts, $1 (YES wins) or $0 (NO wins). Final-day prices converge toward those values as outcome certainty grows.
**Heuristic for Kalshi exotics:**
- `final_high >= 99 AND final_low >= 99` → market settled YES (extremely high confidence)
- `final_high <= 1` → market settled NO
- Anything in between → still open or genuinely uncertain at end of trading
**Caveat:** This is an *inference*, not a direct read. Worth spot-checking against trade_report or external sources if precision matters. But for ranking-style "top winners" tables, it's robust enough.
**How we applied it:** Built the "Biggest Combo Wins (Realized Payouts)" query (7523164) using this signal.

### 38. Microstructure is the 5th dashboard dimension
**Principle:** A complete dashboard for a tradable product covers FIVE complementary lenses, not three or four. Aggregate-only views miss the texture of individual user behavior.
**The five lenses:**
1. **Size** — total volume, premium, OI (counter tiles)
2. **Growth** — monthly/cumulative trajectories (time series)
3. **Composition** — by Series/Variant/Domain (bars, pies)
4. **Behavior** — implied probability evolution (lines)
5. **Microstructure** — per-trade distribution (whale detection, median trade size)
**Why microstructure matters:** Aggregate metrics can hide a story like "the platform is a few whales pretending to be many small bettors" or vice versa. The median vs mean trade size gap reveals it instantly.
**How we applied it:** Discovered `kalshi.trade_report` exists with per-trade rows. Plan a "Trader Behavior" section on the dashboard using percentiles of `contracts_traded × price / 100` (premium per trade). This also unlocks the 1-vs-N row-grain audit (notebook 03).

### 39. Five-dimensional dashboards tell complete stories
**Principle:** When a stakeholder asks *"is the product healthy?"*, they're implicitly asking five questions. A dashboard that covers only 2-3 of them feels thin even if each chart is well-built. Coverage matters as much as polish.
**Mapping to questions:**
- Size → "how big is this?"
- Growth → "is it growing?"
- Composition → "what's it made of?"
- Behavior → "are users engaged differently over time?"
- Microstructure → "who's actually using it?"
**How we applied it:** Audit current dashboard against the five lenses; identify which are well-covered and which are gaps. Microstructure was the biggest gap until we found `kalshi.trade_report`.

### 40. Use cash (not notional) for microstructure trade-size analysis
**Principle:** `contracts_traded` (notional) is distorted by price when comparing trade sizes. Two traders who both "bet $50" will have very different contract counts depending on the odds.
**Example:** 100 contracts at 50¢ = $50 cash. 1,000 contracts at 5¢ = $50 cash. Same real money, 10× different notional.
**How we applied it:** All microstructure queries use `contracts_traded * price / 100.0` (cash per trade) as the trade size unit. Notional is only used for market-level volume aggregates where cross-market comparison is the goal.

### 41. Trade-level ≠ trader-level — "whale" is wrong terminology
**Principle:** Without a user/wallet column, you cannot identify traders — only trades. A single large trade could be one person or ten people acting simultaneously. "Whale concentration" implies trader-level knowledge you don't have.
**How we applied it:** Dropped "whale" language from the microstructure section entirely. Replaced with trade-size distribution metrics: median trade, mode trade, largest single stake. These are accurate descriptions of the data without over-claiming.

### 42. Mode = floor effect in heavy-tailed distributions
**Principle:** When a metric has a hard minimum (price floor, minimum bet), the mode often lands at that floor — not because most people chose it deliberately, but because all values below the floor get compressed to it.
**How we applied it:** Mode of implied probability = 1% (Kalshi's price floor). This means most trades are on parlays so unlikely their combined probability falls below the minimum tick — they all register as 1¢. The mode IS meaningful (extreme long-shots dominate by trade count) but doesn't mean "bettors specifically chose 1%."

### 43. Log-scale buckets for right-skewed distributions
**Principle:** Fixed-width buckets applied to skewed data produce one enormous bucket at the bottom and many near-empty ones at the top. Log-scale buckets (each 2–4× wider than the previous) spread the distribution meaningfully.
**When to identify the need:** Compare median to max. If max is 10,000× the median (e.g., median $9.30, max $176,010), the data is heavily right-skewed and fixed buckets will fail visually.
**How we applied it:** Bet size histogram uses buckets: Under $2 / $2–$5 / $5–$10 / $10–$20 / $20–$50 / $50–$200 / $200+. Each boundary is 2–4× the previous. Log-scale is applied manually via CASE WHEN thresholds — no log() function needed.

### 44. Skew ratio (mean ÷ median) as a distributional signal
**Principle:** Mean ÷ median tells you how lopsided a distribution is. A ratio of 1× = symmetric. A ratio of 4–5× = a small number of very large values pulling the average up.
**How we applied it:** Added `skew_ratio = ROUND(AVG(...) / NULLIF(APPROX_PERCENTILE(..., 0.5), 0), 1)` to the per-series trade distribution table. SPORTSMULTIGAMEEXTENDED = 4.5×, CROSSCATEGORY = 5.2×. Tells the story that most bets are small but a handful of large trades inflate the mean.

### 45. Terminology standardisation — Handle, Category, Type (May 2026)
**Principle:** Use the most widely understood term in sports betting / prediction market context, not internal jargon.
**Changes made:**
- "Cash Exchanged" / "Premium" → **Handle** (standard sports betting term for cash wagered)
- "Domain" → **Category** (plain English, matches Kalshi's own taxonomy label)
- "Variant" → **Type** (simpler, less technical)
**Why it matters:** "Premium" is options/insurance terminology. "Handle" is what sportsbooks use. For a dashboard about prediction markets adjacent to sports betting, Handle is the right word.

### 46. Dune category column update (May 2026)
**Principle:** Derived labels in third-party tools can be fixed over time — recheck assumptions periodically.
**What changed:** As of May 2026, Dune's `category` column now correctly labels all KXMVE series as 'Exotics' (previously mislabeled 7 of 11 as Sports/Politics/etc.). Confirmed empirically — `SELECT category FROM kalshi.market_report WHERE report_ticker LIKE 'KXMVE%' GROUP BY 1` returns only 'Exotics' and 'Mentions'.
**Decision:** Keep using `report_ticker LIKE 'KXMVE%'` as primary filter — it's deterministic and doesn't depend on Dune maintaining the category column correctly. But `category = 'Exotics'` is now a valid alternative.
**Impact on dashboard:** None — all queries already used KXMVE prefix. Sports volume queries (`category = 'Sports'`) no longer need `NOT LIKE 'KXMVE%'` exclusion since Dune separates them cleanly.

### 47. Non-linear fee formulas require trade-by-trade computation
**Principle:** When a formula is non-linear in its inputs (e.g., `P × (1-P)` is parabolic in P), applying it to an aggregate input (the mean) gives a different result than applying it per-row and summing.
**Why it matters for Kalshi:** The taker fee formula `0.07 × contracts × P × (1-P)` is parabolic. Computing fees using the average price (e.g., overall 9.5% implied prob) overstates revenue by ~40% compared to trade-by-trade computation. For Sports Multi-Game: aggregate approach gives $49M, trade-by-trade gives $32M.
**How we applied it:** All fee revenue estimates use SQL aggregation that applies the formula per trade row, then sums. Aggregate price is shown alongside for transparency but never substituted into the calculation.

### 48. Industry coverage often conflates notional with handle
**Principle:** When reading reported fee/hold percentages from industry coverage, check the denominator carefully. Notional and handle differ by an order of magnitude on prediction markets.
**Example:** Yahoo Finance coverage cited Kalshi parlay fees at "0.4-0.5% of handle" using a $546K / $124M ratio. But that $124M was the NOTIONAL, not handle. The actual fee % of handle is ~4.5% — 10× the reported figure.
**How we applied it:** Always specify denominator. Report "fee % of handle" and "fee % of notional" separately. Never use "fee rate" without qualification.

### 49. Kalshi's fee revenue decomposed from Sportico's hold
**Principle:** When you can verify a piece of a third-party finding, do so — it strengthens both your work and theirs.
**How we applied it:** Sportico reported Kalshi exotic parlay total hold at 14.7% of handle (with fees), 10.2% (without fees). Our trade-by-trade fee calculation gives 4.5% of handle. 14.7% - 10.2% ≈ 4.5% — Sportico's "fee component" matches our independent calculation exactly. This validates both: our $55M fee estimate is consistent with Sportico's hold decomposition, and confirms the maker take is ~10% (the residual).

### 50. Maker take is not Kalshi's revenue — important framing
**Principle:** In a CLOB exchange model, the bid-ask spread on the orderbook benefits market makers (other traders), not the exchange itself. Conflating "house edge" with "exchange revenue" misframes the economics.
**Why it matters:** Bettors face a 14.7% total hold on Kalshi exotic parlays, but Kalshi the company only captures ~30% of that (4.5% in fees). The remaining ~10% flows to market makers via orderbook spread. Unlike a traditional sportsbook, Kalshi's revenue model is mostly fee-based, not edge-based.
**How we applied it:** Dashboard fee section explicitly distinguishes Kalshi's fee revenue (verifiable, ~$55M) from the broader hold (cited from Sportico). Methodology note for the section makes this clear so readers don't conflate the two.

### 51. Using NFL as the durability counterfactual
**Principle:** When testing whether a product has demand independent of its launch driver, the cleanest test is what happens when the biggest demand source naturally exits.
**Why NFL specifically for Kalshi exotics:**
- Kalshi launched exotics on Sep 17 2025 — NFL opening day, not by accident
- NFL is the single largest US sports betting demand driver (~30-40% of all US sports betting handle)
- NFL season (Sep–Feb) and Kalshi's ramp period are exactly coterminous
- Feb 9 (Super Bowl LIX) is the cleanest exogenous break in the time series — biggest demand engine turns off
**How we applied it:** Compared December 2025 handle ($50M, NFL peak) to May 2026 handle ($389M, no major sport). 7.8× growth post-NFL refutes the "Kalshi growth is just NFL ridership" counter-narrative. This became the framing for chart 12 and reframed the entire Growth section.

### 52. Resolve open analytical questions with one targeted query
**Principle:** When an analytical question has two competing explanations, design a single query that distinguishes them directly. Don't leave questions open if a 5-line SQL can close them.
**Why it matters:** The article initially left the implied-probability drift (20% → 10%) as an unresolved question — "behavioural or mechanical, can't tell from this data." That was lazy. The 1¢ floor share over time is a single test that distinguishes the two:
- Floor share growing → mechanical (more long-leg templates compounding to 1¢)
- Floor share flat → behavioural (bettors choosing longer shots within fixed templates)
**How we applied it:** Built query 7598456 (Floor Trades 1¢ Monthly). Result: floor share grew 2.8% → 7.5% in eight months. Mechanical explanation does most of the work. The article now lands on a defended conclusion instead of an open question.

### 53. Visual identity — the Predicted theme
**Principle:** A consistent visual identity across charts, the article, and any future quarterly reports makes the work feel like a coherent product, not a one-off.
**Theme spec (locked in May 2026):**
- **Font:** Space Mono throughout (titles, axes, labels)
- **Primary background:** Cream `#FAF6F0`
- **Title / body text:** Dark brown `#3B2314`
- **Primary accent / highlights:** Orange `#CC5A1A`
- **Secondary / muted:** Muted brown `#8B6F5E`
- **Edge bars:** Thin orange (`#CC5A1A`) rules at top and bottom of every chart
**How we applied it:** All 14 article charts regenerated in this theme. Word document styled to match. Sourced from the predicted-deck-editor skill which captures the parent design language. Documented in `writing_style_guide.md` for reuse.

### 54. Narrative chart titles, a16z editorial style
**Principle:** Every chart title is a full declarative observational sentence — never a topic label. The bolded phrase is the load-bearing claim that loses the chart if removed.
**Why it matters:** A label ("Monthly handle") asks the reader to interpret the data. A claim ("May 2026 ran 7.8× larger than December's NFL peak") delivers the takeaway. Charts that present the conclusion in the title turn the chart into evidence, not interpretation.
**Rules:**
- Present tense, active voice
- Bolded phrase = load-bearing claim
- Strip em-dashes and en-dashes from titles (replace `—` with a comma)
- Chart/data is evidence; the title is already the conclusion
**Example transformation:** ❌ "Monthly Exotic Handle" → ✅ "May 2026 ran 7.8x larger than December's NFL peak"
**How we applied it:** Every chart title in the article is now a narrative claim. Same convention as the Predicted deck.

### 55. Article-specific Dune queries (May 2026 additions)
**Principle:** Every chart in published work needs a reproducible Dune query that someone else can click, run, and verify. Ad-hoc Python-only queries are fine for exploration, but they don't survive publication.
**Queries added for the article:**
- **7598456** — Floor Trades (1¢) Monthly → Chart 10 (resolves drift debate)
- **7598460** — OI Over Time — Exotic vs Total Kalshi → Chart 11 (Super Bowl peak)
- **7598462** — Implied Probability Histogram → Chart 13 (1¢ floor as secondary peak)
- **7521948** — Kalshi Exotic Handle — Monthly (existing, reused) → Charts 01, 02, 12
**How we applied it:** Full chart → query map maintained in `dashboard/queries_inventory.md`. Each chart caption in the article references its query ID. The article is fully reproducible from public-facing Dune queries.

### 56. Terminology alignment — "Implied Probability" everywhere
**Principle:** When a single concept has multiple valid names (price, odds, implied probability), pick one for formal use and align everything to it. Casual variants are fine in narrative voice; the formal term must be consistent in chart titles, axes, and column headers.
**Why it matters:** Inconsistent naming forces the reader to re-anchor every time they switch from a chart to body text. "Price" is the column name in the data, "odds" is sports-betting colloquial, "implied probability" is the formal interpretation. Mixing them randomly looks sloppy.
**Decision (May 2026):** Use **"Implied Probability"** as the formal term throughout — matches the dashboard standard already established by queries 7545755, 7521912, 7516976. Allow "odds" only as a colloquial bridge in narrative sentences for readability (e.g. *"15% implied probability — a 6-to-1 shot"*). Reference `price` only when discussing the raw column in `kalshi.trade_report`.

### 57. Kalshi category audit — Sports filter is complete
**Principle:** Before relying on a single category label to define a filter, audit the full taxonomy to confirm coverage.
**The audit (May 2026):** Ran a `SELECT category, COUNT(DISTINCT report_ticker), SUM(daily_volume)` against `kalshi.market_report` since Sep 17 2025. Kalshi uses 18 distinct categories. "Sports" is the single comprehensive category for all non-exotic sports markets — 1,699 unique tickers, $57.38B volume, 70.84% of platform. There is no fragmented sports taxonomy (no separate "NFL", "NBA" as top-level categories — all roll up under "Sports").
**Confirms:** The filter `WHERE category = 'Sports' AND report_ticker NOT LIKE 'KXMVE%'` correctly captures the full non-exotic sports book.
**One nuance:** "Mentions" category ($0.81B, 305 tickers) contains both standalone mention markets AND the KXMVEMENTIONSSINGLE series. It's the only Kalshi category where exotic and non-exotic products share a label. The `NOT LIKE 'KXMVE%'` filter handles this correctly.
**Categories above 1% of volume since exotic launch:** Sports (70.8%), Exotics (16.2%), Crypto (7.2%), Politics (1.1%), Mentions (1.0%). Everything else combined: <3%. Audit query saved as 7608163.

### 58. How we got to 47% ever traded — step by step
**What we measured:** Of all KXMVE parlay tickers ever listed on Kalshi, what share received at least one trade?

**Step 1 — Count everything Kalshi ever listed.**
Every parlay Kalshi creates gets a unique ticker in the database. "Chiefs win + Bills win" is one ticker. "Chiefs win + Ravens win" is a different ticker. We counted all distinct tickers starting with `KXMVE` in `kalshi.market_report`. Result: **37.1 million tickers**.

**Step 2 — Count which ones ever got a trade.**
We looked at `kalshi.trade_report` — one row per trade, grain-audited (see note 3). We asked: of those 37.1 million tickers, how many appear at least once in the trade table? Result: **17.2 million**.

**Step 3 — The maths.**
17.2M ÷ 37.1M = **47% ever traded. 53% listed and never touched.**

**Why it matters:** Two tables, one join, direct count. Nothing estimated or inferred. The breakdown by product (Cross-Category 94%, Sport Multi-Game 48%, everything else 11–14%) shows the supply/demand gap varies hugely by product type. Dune query 7607014.

---

### 59. Assumptions and gaps in the listed vs ever traded finding
**Why document this:** The 47% figure is real but rests on assumptions that should be stated whenever the finding is presented or challenged.

**Gap 1 — Listed ≠ actually available to trade.**
We assume every `KXMVE` ticker in `market_report` was shown to bettors with a live price. But if the RFQ mechanism is real (market makers quote on request), some tickers may never have had a price quoted against them — meaning no bettor could ever have traded them even if they wanted to. Some of the 53% "dead-on-arrival" could be "never quoted by a market maker" rather than "available but unwanted." We cannot separate these two from the data we have.

**Gap 2 — Is the Dune trade data complete?**
We assume `kalshi.trade_report` on Dune is a full record of every trade ever executed. The grain audit confirms 1 row per trade structurally, but does not confirm historical completeness. If Dune's mirror has any coverage gaps, the "ever traded" side would be undercounted, inflating the 53% figure.

**Gap 3 — Small-N products look cleaner than they are.**
CBB Championship at 100% sounds impressive. But it only had ~30K listings. Sport Multi-Game at 48% covers 22 million listings. Percentages across products are not operationally comparable — a 100% rate on 30K is trivially achievable; 48% on 22 million is structurally different.

**Gap 4 — "Never traded" includes expired short windows.**
A parlay for a specific November game had maybe 2–3 days to trade before it expired. "Never traded" could mean nobody wanted it, or it could mean the window closed before anyone got to it. Both appear identically in the data.

**What the number can and cannot claim:**
- ✓ "47% of KXMVE tickers appeared at least once in trade data"
- ✓ "53% of listed tickers never appeared in trade data"
- ✗ "47% of available prices were taken up by bettors" — requires RFQ quoting confirmation we don't have

---

### 60. Per-price-point histogram — trade count vs handle, two different stories
**What we built:** Two charts showing the distribution of KXMVE activity across every integer price tick (1¢–99¢), one for trade count and one for handle.

**Why per-price-point instead of buckets (like chart 13):**
Chart 13 uses fixed-width ranges (0–5%, 5–10%, etc.). Buckets compress the data and hide internal structure — particularly the 1¢ floor spike, which gets diluted inside the 0–5% bucket. A per-price-point chart gives one bar per integer tick, so the spike stands alone and the full shape of the distribution is visible.

**Trade count chart (query 7622547 → `implied_prob_per_price.png`):**
One bar = number of trades at that exact price tick. Shows a steep power-law decay from 1¢ downward. The 1¢ floor alone is 7% of all trades — more than any other single price point. No unusual clustering at round numbers (10¢, 25¢, 50¢) — bettors are not gravitating to "nice" prices.

**Handle chart (query 7622663 → `handle_per_price.png`):**
One bar = `SUM(contracts_traded × price / 100)` at that price tick. Tells a completely different story. Handle builds gradually from 1¢, peaks at **26¢**, then decays. The 1¢ floor is nearly flat in cash terms — tiny ticket sizes mean huge trade count but negligible cash. The serious money sits in the 15–35¢ range.

**The two-story insight:**
- **Trade count** = bettor behaviour. Dominated by extreme longshots and the 1¢ floor. Recreational, lottery-ticket pattern.
- **Handle** = where the money is. Concentrated at moderate longshots (15–35¢). The smaller population of meaningful bets that drives actual cash volume.

This is the price-lens version of the same finding from the bet size table (top 3.6% of trades drive 54.8% of handle). Different angle, same underlying structure.

**Why notional was not charted:**
Notional = `SUM(contracts_traded)` per price tick. At low prices, contracts are cheap so people buy more per trade — this inflates notional at the low end mechanically, not behaviourally. The notional distribution would reweight toward 1¢ for structural reasons unrelated to any insight. It adds noise rather than a third distinct story. Trade count and handle cover the two meaningful dimensions.

**Column name note:** The timestamp column in `kalshi.trade_report` is `date` (varchar, format YYYY-MM-DD), not `block_time`. Filter syntax: `WHERE date >= '2025-09-17'`.

---

### 21. Design for reversibility
**Principle:** Never bake a derived label into your raw data. Always keep the underlying fields and apply labels in transformation steps.
**Why it matters:** A baked-in label means changing your classification requires reprocessing all the data. Applied labels mean you can change the rule and re-derive.
**How we applied it:** `dim_market` (when built) will keep `report_ticker`, leg compositions, etc. as raw columns. Domain/variant labels are computed in views, not stored as truth. Today's series-level labels can be replaced with leg-level labels later without touching the underlying data.

---

### 61. True trade count: 29,562,842 — not "30M+"
**Principle:** Headline counts should be verified from multiple query angles before publication.
**Finding:** Three independent Dune queries all return the same number: **29,562,842 real trades** since launch (filter: `price > 0 AND contracts > 0`). Rows with zero price or zero contracts are data artefacts (listings with no activity). "Nearly 30 million" is the correct written form. "30M+" or "over 30 million" would be wrong by ~440K trades.
**Why three queries:** Cross-counting from trade_report grain audit (notebook 03) + platform-total query (7495941) + a fresh count with explicit filters. All three agree. This is the right standard for any headline number that appears in published work.
**Lesson:** Never report a rounded figure that is directionally wrong (30M+ vs 29.56M). "Nearly 30 million" is more honest and still readable.

---

### 62. The 1¢ floor is a market-maker pricing choice, not a Kalshi hard limit
**Principle:** Before labelling something a "floor" or "minimum," verify whether it is enforced at the product level or merely the behavioural result of market-maker pricing decisions.
**What we found:** Kalshi's public API shows combo markets with `fractional_trading_enabled: True` and `price_level_structure: deci_cent`. Deci-cent means the tick is 0.1¢ — trades below 1¢ are technically permitted by the platform. But empirically, exactly zero trades occur below 1¢ (verified: `count(price = 1..99¢) = count(price > 0)` = 29,562,842). Market makers (SIG, Kalshi Trading) simply choose not to quote below 1¢.
**Why it matters:** "Kalshi enforces a 1¢ minimum" is a stronger claim than the data supports. The accurate statement is: "No trade has ever occurred below 1¢ — the floor reflects market-maker pricing discipline, not a hard contract limit." The former implies a regulatory constraint; the latter reflects economics.
**In the report:** The 1¢ floor section in the article was updated to reflect this distinction. Any future section on pricing mechanics should preserve it.

---

### 63. True probability vs floor price: the implied overpricing of extreme parlays
**Principle:** When a price floor exists, compute the gap between the floor price and the fair-value probability for the most extreme products. The gap is the insight.
**The calculation (verified live parlay, June 2026):**
- Product: a 10-leg Sports Multi-Game parlay spanning 10 different MLB/WNBA games
- Each individual leg: ~50% probability (coin-flip outcomes)
- Combined true probability: 0.5^10 = 0.098% ≈ 0.15% (accounting for vig per leg)
- True fair value: ~0.15¢ per $1 contract (below the 1¢ floor)
- Actual market price: 1¢ (the floor — quoted by market maker)
- Implied probability at 1¢: ~1% (~99-to-1 payout)
- Overpricing: 1% ÷ 0.15% ≈ **7× overpriced relative to true probability**
**So what:** A bettor placing a 10-leg parlay at 1¢ is paying 7 times fair value for the lottery ticket. The market-maker captures the spread between fair value (0.15¢) and quoted floor (1¢). This is structural, not a market inefficiency to exploit — it's the economics of extreme parlay pricing.
**Caveat:** This analysis uses 50% legs as a baseline. If legs have lower true probability (e.g., player prop underdogs), the gap widens further.

---

### 64. Mechanical vs behavioural drift: the honest position
**Principle:** When aggregate data is consistent with two competing explanations, do not assign causation to either. State both, explain the arithmetic, and label what would distinguish them.
**The finding:** Implied probability across all KXMVE trades drifted from ~20% (Sep 2025) to ~10% (May 2026). The 1¢ floor's share of trades grew from 2.8% to 7.6% over the same period.
**Two valid explanations:**
1. **Mechanical:** Kalshi launched more product types with more legs over time. More legs = lower compounded probability = more floor hits. The drift is a product-mix effect, not a change in trader behaviour.
2. **Behavioural:** Traders learned to pick longer-shot parlays over time, or the user base shifted toward more recreational users preferring lottery-ticket odds.
**Why we cannot separate them:** We have no per-parlay leg count from the trade data. Without controlling for leg count, the observed drift is consistent with both explanations. The honest report position: describe the drift, explain that leg compounding mechanically produces this arithmetic, acknowledge the behavioural alternative, and flag that disambiguation requires per-parlay leg metadata.
**What NOT to do:** Do not state "Kalshi engineered the drift" or "this is structural, not behavioural." That is overclaiming from available data.

---

### 65. Handle concentration: 96% top-2, not 93%
**Principle:** Always verify concentration statistics against the actual data before writing them in a headline.
**Finding:** Sports Multi-Game + Cross-Category together account for **96% of all KXMVE handle** (June 2026 snapshot). An earlier draft of the report said "93%" — that figure was stale or derived from a different query. The correct figure from query 7506442 (per-series leaderboard) is 96%.
**Why this matters:** Two percentage points sounds small but changes the framing of how concentrated the market is. 96% is an even stronger concentration story than 93%.

---

### 66. Fee total corrected: ~$56.8M estimated, not $55M
**Finding:** Trade-by-trade fee calculation (formula: `0.07 × contracts × P/100 × (1-P/100)` per trade, taker only) returns:
- Sports Multi-Game: $33.6M
- Cross-Category: $20.6M
- Remaining 9 products: ~$2.7M combined
- **Total: ~$56.8M**
**Effective rate:** $56.8M ÷ $1.42B handle = **~4.0% of handle** (slightly lower than the old 4.51% which used a stale handle denominator and aggregate price approximation).
**Why the aggregate method was wrong:** Applying the fee formula to the mean price instead of per-trade overstates revenue by ~50% due to the parabolic shape of `P × (1-P)`. The mean P (e.g., 10%) gives a lower variance than the actual distribution of P, underweighting the many 1¢ trades where the fee is near-zero.
**Written form in report:** "an estimated $56.8 million" with a note that this is a taker-only calculation — maker-only or symmetric trades pay less.

---

### 67. RFQ model confirmed: SIG and Kalshi Trading are the market makers
**Source:** Sportico coverage of Kalshi's combo/parlay products (verified 2026).
**Structure:** Kalshi's exotic combo markets operate on a Request-for-Quote (RFQ) model, not a continuous limit-order book. When a user wants to trade a parlay, the platform routes the request to designated market makers who quote a price. Susquehanna International Group (SIG) and Kalshi Trading are the two confirmed market makers for these products.
**Why it matters:** This explains:
1. Why 53% of listed markets "never traded" — they may never have received a quote, not just been ignored by traders.
2. Why the 1¢ floor is a pricing choice not a limit — market makers set the minimum they'll quote.
3. Why the handle concentration is so high — market makers are selective about which parlays they actively price.
4. The ~10% maker take (Sportico's 14.7% total hold minus Kalshi's 4.5% fee) flows to SIG/Kalshi Trading, not to Kalshi the exchange.
**Implication for methodology note 59 (Gap 1):** Some "never traded" markets are likely "never quoted by a market maker" — unlocking this distinction requires RFQ data, which is not publicly available.

---

### 68. Prediction market language: no "bet" or "bettor"
**Principle:** Word choice signals the analytical frame. "Bet/bettor" positions the platform as a sportsbook; "trade/trader/contract" positions it as an exchange. Kalshi is regulated as a CFTC-licensed exchange, not a sportsbook. Language should match the regulatory reality.
**Standard terms for this report:**
- Trade (not bet), Trader (not bettor), Contract (not ticket or wager)
- Handle (standard industry term for cash exchanged — acceptable across both sportsbook and exchange contexts)
- Taker / Maker (exchange microstructure terms, not sportsbook terms)
**Why it matters for the portfolio piece:** A reviewer from a data analytics or fintech role will notice sportsbook language applied to a CFTC-regulated exchange and flag it as a category error. Using the correct framing signals understanding of the underlying market structure.

---

### 69. Simultaneous data snapshot: the consistency fix
**Principle:** When multiple metrics appear in the same report, they must all be measured at the same point in time. Cross-timestamp inconsistencies surface as internal contradictions that undermine credibility.
**What we did:** Ran all 22 Dune queries simultaneously on June 1-2, 2026. Frozen results saved to `data_snapshot_2026-06-02.json`. All charts rebuilt from that single JSON file. All text numbers updated from the same snapshot.
**Before the fix:** Handle and trade count were from a May snapshot, fee queries from a different week, producing contradictions (e.g., handle figures that didn't reconcile with product-level breakdowns).
**Lesson for future reports:** Run all queries in one batch on a single day. Save the raw results immediately. Rebuild all charts from the saved file, not live API calls. Lock the snapshot date in the report front matter.

---

### 70. Becker (2024) research: correct placement in the long-shot section
**Source:** Jonathan Becker, "The Microstructure of Wealth Transfer in Prediction Markets" (2024).
**Key findings relevant here:** Prediction market takers lose approximately 32% of capital over time; PnL is highly concentrated among a small share of participants; the favourite-longshot bias is present (extreme longshots are overpriced relative to their realised win rates).
**Where it belongs:** The Becker research directly supports the 1¢ floor / long-shot section, because it provides independent evidence that extreme longshots (like floor-priced parlays) are systematically overpriced and generate losses for takers. It does NOT belong in the "two populations" trade-size section, which is about trade count vs handle concentration — a different dimension of the same data.
**Mistake to avoid:** Placing Becker in the trade-size section implies his findings are about whether whales or retail are the bigger traders. They're not — his findings are about who wins and who loses, which maps to the long-shot pricing story.

---

### 71. Two populations: visible in both price-point and trade-size data
**Principle:** When the same underlying insight surfaces from two independent data angles, it strengthens the claim significantly. State both angles and explicitly connect them.
**Population 1 — Recreational / lottery-ticket:**
- Price-point view: trade COUNT is dominated by 1¢ floor (7% of all trades at one price tick)
- Trade-size view: median trade $9.30 vs mean $44 (4.7× skew) — most trades are very small
- Implication: large number of small, low-probability bets. Recreational pattern.
**Population 2 — Informed / larger:**
- Price-point view: HANDLE peaks at 26¢, concentrated 15-35¢ — money avoids the extreme long-shot floor
- Trade-size view: top 3.6% of trades by size drive 54.8% of handle
- Implication: smaller number of larger, moderate-probability bets. More deliberate trading.
**Why this is a genuine insight (not a tautology):** The two populations do not perfectly separate by any single variable — the same trader could place both types. But the aggregate data shows that the activity driving the most cash and the activity driving the most trade count are structurally different in their price and size profile. This is the market's internal heterogeneity, and it matters for interpreting who is providing liquidity to whom.
**Limitation:** Without user IDs, we cannot confirm these are two distinct groups of people vs one group switching between modes.

---

### 73. Reference parlay: 10-leg MLB example (June 5, 2026)

**Ticker:** `KXMVESPORTSMULTIGAMEEXTENDED-S20267877AAA3141-A0A34999272`
**Pulled:** June 5, 2026 via Kalshi public API (`api.elections.kalshi.com/trade-api/v2/markets`)
**Status at pull:** Active, untraded, created same day

**10 legs — all MLB June 5 2026:**
| Team | Game | Implied prob (yes_ask) |
|---|---|---|
| CHC | SF @ CHC 14:20 | 61% |
| PHI | CWS @ PHI 18:40 | 64% |
| BOS | BOS @ NYY 19:05 | 44% |
| BAL | BAL @ TOR 19:07 | 43% |
| MIA | TB @ MIA 19:10 | 45% |
| PIT | PIT @ ATL 19:15 | 44% |
| HOU | ATH @ HOU 20:10 | 50% |
| CIN | CIN @ STL 20:15 | 45% |
| CLE | CLE @ TEX 20:15 | 57% |
| MIL | MIL @ COL 20:40 | 60% |

**Combined true probability (independent legs):** 0.11% (~890-to-1 odds)
**Quoted ask:** 0.30¢ (~333-to-1 odds)
**Gap:** 0.30¢ ÷ 0.11¢ = **2.7× the fair price**

**What this changes from our earlier analysis:**
The original example (from the previous session) used a parlay priced at 1¢ and calculated 7× overpricing. This live pull found a 10-leg parlay quoted at **0.30¢** — below 1¢ — with 2.7× overpricing. This means:
- Market makers DO quote below 1¢ (deci-cent pricing is live and in use)
- The "1¢ floor" in trade data is a **buyer behavior floor**, not a market-maker minimum
- Our earlier statement "no market maker has ever quoted below 1¢" was incorrect

**Correct framing:**
- Market makers quote as low as 0.20¢ on extreme parlays (19 markets below 1¢ on June 5 2026)
- Zero trades have executed below 1¢ across 29.56M records (up to June 2 snapshot)
- The gap between quoted price and fair value varies: this example is 2.7×, not 7×
- The floor at 1¢ in trade data reflects buyers' minimum practical trade interest

---

### 74. 1¢ floor framing: what "mispriced" does and doesn't mean

**The legitimate reasons the quoted price exceeds fair probability:**
1. **Market maker spread** — minimum viable economics. Below some price, fee revenue per trade is near zero.
2. **Lottery/entertainment premium** — buyers of extreme long-shots pay above EV across all markets (Becker 2024, favourite-longshot bias). They're buying the story, not just the probability.
3. **Leg correlation** — combining independent-probability multiplication assumes zero correlation between legs. Same-day games may share minor correlations (travel, weather). True combined probability is slightly higher than the raw multiplication.

**Why "mispriced" is still partially valid:**
- Even accounting for spread and lottery premium, 2.7× or 7× above fair value is extreme
- The gap cannot be arbitraged away — nobody can sell YES below the quoted ask to push price toward fair value
- Buyers consistently overpay in a way that is structurally enforced by the minimum quote convention

**The defensible framing for the report:**
> *The floor price implies odds that are 2-7× better for the market maker than the true combined probability would justify. This gap cannot be arbitraged because no trader can bid below the market maker's quote.*

Do NOT say "mispriced" as a standalone claim. Say "priced above fair value" and note it is structural, not correctable.

---

### 75. CRITICAL: Dune's `trade_report.price` truncates to integer cents — sub-1¢ trades and price precision are lost

**Discovered:** June 2026, by cross-validating Dune against Kalshi's own trades API.

**The finding:** Dune's `kalshi.trade_report.price` column stores price as an **integer number of cents** and **truncates (floors)** — it does not round. Verified both directions against Kalshi's API (`yes_price_dollars`, full decimal precision):
- A trade at 0.5¢, 0.6¢, 0.8¢ → stored in Dune as `price = 0` (not bumped to 1)
- A trade at 1.8¢ → stored in Dune as `price = 1` (not rounded to 2)
- A trade at 1.3¢ → stored as `price = 1`

**Two consequences:**

1. **All sub-1¢ trades floor to `price = 0`.** Kalshi combos price in 0.1¢ ticks (API `price_ranges` step = 0.001 = 0.1¢; values 0.1¢–0.9¢ are valid below 1¢). Every one of these floors to 0 in Dune. Our standard `price > 0` filter then **deleted them entirely.**
   - Pinned to the snapshot window (2025-09-17 → 2026-06-01): **2,894,623 sub-1¢ trades, 5.01 billion contracts** were being excluded.
   - True trade count is **32,457,465**, not 29,562,842. The old figure undercounted by 8.9%.

2. **Every price is understated by up to 0.9¢ (~0.5¢ on average).** A bucket labelled "N¢" in trade_report actually contains the range [N.0¢, N.9¢]. Trade-level implied probability (mean/median) and any trade-level handle computed from this column run systematically low — worst at the bottom (a 1.5¢ trade read as 1¢ is understated by a third).

**What is and isn't affected:**
- ✅ SAFE: headline notional ($14.5B) and handle ($1.46B) — these come from `market_report` daily aggregates (`daily_volume`, `high`/`low`), not the per-trade `price`. Handle is undercounted by only ~2% (the sub-1¢ slice).
- ❌ AFFECTED: anything built on `trade_report.price` — the per-price distribution charts (Fig 7/8/15a/15b/15c), the "1¢ floor" framing (Fig 16), trade-count totals, and trade-level implied-probability mean.

**The rule going forward:**
- **Counts and volumes:** Dune is fine. Treat `price = 0 AND contracts_traded > 0` as the "sub-1¢" bucket; stop using `price > 0` as a blanket filter.
- **True price and handle precision:** Kalshi's API (`yes_price_dollars`) is the only source of truth. Dune cannot recover it.

**Why this is a strength, not just an error:** catching a silent upstream truncation by cross-validating two independent sources is exactly the kind of data-quality rigor the report should demonstrate. Document the catch; don't hide it.

---

### 76. The "1¢ floor" is not a floor — 0.1¢ is the real minimum tick

**Correction to earlier framing:** Prior drafts called 1¢ "the floor" and "the single most-traded price." Both need revision:
- Kalshi's true minimum tick on combos is **0.1¢** (deci-cent). Trades occur all the way down to 0.1¢.
- The sub-1¢ bucket (2.89M trades) is **larger than the 1¢ tick** (2.09M). Whether any single deci-cent tick (likely 0.1¢) individually beats the 1¢ tick requires the API price-shape sample (in progress).
- The "1¢ floor share growing" story becomes "the sub-1¢ / extreme-longshot share growing." The direction still holds (the bucket grew from 0% at launch toward double digits), but the floor label was wrong.

**Sections of the report requiring rewrite:**
- "Where Trades and Handle Cluster" — trade-count side wrong; handle side (peaks 26¢, sub-1¢ negligible cash) survives and the two-population insight strengthens.
- "Is the 1¢ Floor Growing?" — premise wrong; reframe around the real 0.1¢ floor and the sub-1¢ longshot share.

---

### 77. Sub-1¢ price shape — recovered from a Kalshi API sample

**Method:** Dune stores all sub-1¢ trades as `price = 0`, so the internal 0.1¢–0.9¢ split is invisible there. Pulled a random sample of 700 sub-1¢ tickers from Dune, then queried each against Kalshi's trades API (`yes_price_dollars`, full precision), capped to the snapshot window. n = 531 sub-1¢ trades across 422 tickers.

**Result — distribution across the deci-cent ticks:**
| Price | Share of sub-1¢ |
|---|---|
| 0.1¢ | 6.8% |
| **0.2¢** | **20.9%** (the sub-1¢ mode) |
| 0.3¢ | 10.9% · 0.4¢ 11.1% · 0.5¢ 13.0% |
| 0.6¢ | 10.5% · 0.7¢ 9.2% · 0.8¢ 9.0% · 0.9¢ 8.5% |

**Key conclusions:**
- Contract-weighted mean sub-1¢ price = **0.367¢**.
- The sub-1¢ mode is **0.2¢**, not 0.1¢. Spread fairly evenly across the nine ticks.
- **No single deci-cent tick beats the 1¢ tick.** Applied to the full 2.89M sub-1¢ trades, the biggest (0.2¢ ≈ 605K) is far below the 1¢ tick (2.09M). So: as a *group*, sub-1¢ (8.9%) is the largest bar; as a *single tick*, 1¢ (6.4%) is still the most-traded individual price.
- **Sub-1¢ handle ≈ $18–19M ≈ 1.3% of total** — small share despite 8.9% of trades. "Barely registers in cash" is defensible as a *share* statement, but NOT per-tick (see note 78).

---

### 78. Effective-price proxy and the corrected headline figures

**Flooring affects every price, not just sub-1¢.** Dune truncates, so a bar labelled "N¢" really spans N.0¢–N.9¢. Trade-level price/handle from Dune is understated by ~0.45¢ per trade on average (worst at the bottom: a 1.5¢ trade read as 1¢ is a third low).

**Effective-price proxy (Dune-only reconstruction):**
- `price = 0` → **0.367¢** (sample contract-weighted mean, note 77)
- `price = N ≥ 1` → **N + 0.45¢** (midpoint of the floored deci-cent range)
- For exact figures, Kalshi API `yes_price_dollars` is the only source of truth.

**Corrected headline numbers (snapshot window Sep 17 2025 – Jun 1 2026):**
- **True trade count: 32,457,465** (old `price>0` figure 29,562,842 undercounted by 8.9%).
- **Trades vs handle by implied-probability bucket:**
  | Bucket | % trades | % handle |
  |---|---|---|
  | 0-2¢ (extreme longshots) | 20.1% | 4.6% |
  | 3-5¢ | 11.1% | 4.5% |
  | 6-15¢ | 24.0% | 15.3% |
  | 16-30¢ | 22.3% | 24.3% |
  | 31-50¢ | 16.1% | 28.3% |
  | 51-99¢ | 6.4% | 23.0% |
- **78% of trades price below 30¢.** Favourites (51-99¢) = 6.4% of trades.
- **More trades print below 1¢ (8.9%) than on every price above 50¢ combined (6.4%).**
- Handle per tick is a **broad plateau, peaking at 26¢ ($24.3M)**, not a sharp spike. The 1¢ and sub-1¢ ticks carry ~$18-23M *each* (near the peak) — so "the floor barely registers" is true as a bucket *share* but false per-tick.
- **Trade-size (corrected, incl sub-1¢):** 71% of trades under $20 = 11% of handle; top 3.4% over $200 = 54% of handle.

**Decision — terminology:** the bottom bucket is labelled **"0-2¢ extreme longshots"** across all charts (price ≤ 2¢ ≈ implied probability ≤ 2% ≈ 50-to-1 or longer). Consistent definition everywhere.

---

### 79. Trade-weighted vs contract-weighted — why the implied-prob charts barely moved

**The discovery did NOT move Fig 12 (drift) or Fig 13 (by product).** Both were already **contract-weighted** (handle ÷ notional), which always included the sub-1¢ trades in the denominator (as zeros). Re-including them at 0.367¢ instead of 0 shifts each value <0.5pp. Confirmed: Fig 13 chart shows Sports Multi-Game mean 9%; corrected calc = 8.9%.

**The two weightings tell opposite stories (worth knowing, not necessarily charting):**
- **Contract-weighted** (size-weighted, = handle/notional): mean 20% → ~10%, median 15% → ~8%. "Money/volume piled into cheap longshots."
- **Trade-weighted** (the typical trade, each trade = 1 vote): mean ~22% → ~21%, median ~16% → ~12-15%. "The typical trade barely changed."
- Worked example: two trades, 10 contracts @ 50¢ and 1,000 @ 2¢. Trade-weighted avg = 26¢; contract-weighted avg = 2.5¢.
- **Reading:** the headline "implied probability halved" is a size-weighting effect (contracts moving to longshots), not the typical trade getting cheaper. Both are valid; label which one. A line called "per trade" should be trade-weighted; the current charts are contract-weighted, so label them "by volume / blended."

**Conclusion:** Fig 12 and Fig 13 are correct as-is. Only the distribution/count/floor charts needed rebuilding (note 81).

---

### 80. The Super Bowl dip — extreme-longshot share tracks the sports calendar

**Observation:** the sub-1¢ share dipped to 4.9% in Feb 2026 (from 6.9% Jan), then recovered and climbed to 12% by May.

**The analysis (why, with evidence):** February is the *only* month where the **absolute** sub-1¢ count fell — down 17% (225,231 → 186,533) — *while total trading grew 16%* (3.26M → 3.78M). So the dip is a genuine pullback AND dilution, compounding.

**Mechanism — calendar density:** extreme longshots are many-leg parlays, and many legs need many games running **at the same time** to build from. February is when the NFL ends (Super Bowl, Feb 9); the calendar collapses to one marquee game, so there is less raw material to stack into 10-leg combos (count falls). Simultaneously the Super Bowl pulls in casual money on that single game at normal odds (total volume rises). This also explains the whole curve: the climb to 12% by May coincides with MLB in full season + NBA playoffs flooding the slate with concurrent games.

**Honest flag:** the leg-count mechanism is inferred — trade data carries no leg count. But the absolute-count drop + calendar timing make it the strongest read.

---

### 81. Execution record — charts rebuilt and live Dune queries corrected (June 2026)

**Charts rebuilt (sub-1¢ included, snapshot-pinned):**
- Fig 15 — paired trades vs handle by implied-prob bucket (new, two-population story)
- Fig 15a — handle per tick (broad plateau, sub-1¢ bar, 26¢ peak)
- Fig 15b — trade-count distribution (sub-1¢ = 8.9%, biggest bar)
- Fig 15c — bucketed trade distribution (0-2¢ extreme longshots = 20%)
- Fig 16a — sub-1¢ monthly share (6% → 12%, Super Bowl dip)
- Fig 16b — 0-2¢ monthly share (~20%, Super Bowl dip)
- Fig 18 — trade-size buckets (incl sub-1¢; 3.4% over $200 drive 54%)
- Fig 12 (mean+median callouts) and Fig 13 left as-is (note 79)

**Live Dune queries updated IN PLACE (same IDs, column names preserved):** 7622547, 7622663, 7623140, 7557750, 7598456. Re-executed so the dashboard serves corrected data. **7576002 (fee by product) deliberately not changed** — sub-1¢ adds ~$1.8M (0.3%, fee≈0 at p≈0) and its columns feed the fee counters; not worth the breakage risk.

**Repo:** corrected SQL in `queries/sub1c_corrected_queries.sql`; correction section in `dashboard/queries_inventory.md`; supporting data in `data_sub1c_*.json`, `data_implied_prob_buckets_corrected.json`, `data_monthly_floor_both.json`, `data_tradesize_corrected.json`.

**Chart vs source-of-truth rule going forward:** counts/volumes from Dune; exact price/handle from Kalshi API `yes_price_dollars`.

---

### 72. Figure numbering and source captions as reproducibility standard
**Principle:** Every chart in a published report should carry: (1) a figure number traceable to the chart file, (2) a source line identifying the query or data origin, and (3) a snapshot date.
**Standard format used in this report:**
`Fig. N · [Chart description]. Source: Kalshi trade data via Dune Analytics (query XXXXXXX), as of June 2026.`
**Why it matters:** Without a figure number, in-text references ("as shown above") break when the document is reordered. Without a source and date, the chart is not reproducible — a reviewer cannot verify the number or check if it has changed. This is the baseline for any data analyst's published work.
**How we applied it:** All 20 charts in this report carry source captions tied to their Dune query IDs. The combo product definitions table (Fig. 00) cites the Kalshi public API.

---

## Part 2 — Dashboard methodology widget (paste-ready)

Drop this in a Text widget at the bottom of the Dune dashboard.

```markdown
## Methodology

**Definition of "exotic":** Any market whose `report_ticker` starts with `KXMVE` (Kalshi's MultiVariate Event prefix). This is the deterministic, source-aligned definition — verified against Kalshi's public API.

**Why not `category = 'Exotics'`?** Dune's `category` column relabels 7 of 11 KXMVE families (e.g. NFL parlays → "Sports"). Kalshi's own API places all KXMVE under "Exotics". We use the structural ticker prefix instead.

**Volume:** Sum of `daily_volume` over the period. Each parlay contract counts as **one trade**, regardless of leg count — verified structurally (each parlay is one ticker, not N tickers).

**Open Interest:** Plotted daily as a snapshot. Not summed across days (OI is a stock, not a flow).

**Taxonomy (two levels):**

*Domain* (what the parlay is about):
- **Sports** — all parlays whose legs are sports outcomes (includes cross-sport multi-league parlays)
- **Entertainment** — Oscars, Grammys
- **Mentions** — single-leg "Mention" markets (Kalshi's own non-Exotics category)

*Variant* (sub-bucket within Sports):
- **multi_game** — bets across multiple games of one sport
- **single_game** — multi-outcome bets within one game
- **championship** — tournament-shaped (March Madness, etc.)
- **cross_sport** — legs span multiple sports/leagues (empirically 99.89% all-sports)
- **awards** — Oscars, Grammys (Entertainment domain)
- **mentions** — single-leg mention markets

**Methodology note on cross-sport classification:**
99.89% of cross-category parlays are all-sports; 0.3% mix sports with crypto. We classify the whole series as Sports; per-leg classification is a future refinement.

*Background:* The series `KXMVECROSSCATEGORY` was named by Kalshi for parlays that span multiple sources. Empirically (sample of 5,000 open parlays, May 2026), **99.89% are all-Sports** legs from different sports/leagues, **0.3% mix Sports + Crypto**, **<0.1% are all-Crypto**. We classify the entire series as Sports for dashboard purposes, with the minority cases (~$10M of $3.5B total) folded in. Notebook 02 will split out the truly mixed minority once per-leg classification lands.

**Caveats:**
- Kalshi auto-generates many parlay combinations as standalone markets; most never trade. Use traded volume, not market count.
- Sports parlays appear in our exotic total (~$11.16B all-time) and may also appear under "Sports" in other reports. Both counts are correct — different lenses (structure vs subject).
- Reported parlay volumes elsewhere may be 2–5× higher if they multiply by leg count rather than counting one parlay = one contract.

*Last updated: 2026-05-15*
```
