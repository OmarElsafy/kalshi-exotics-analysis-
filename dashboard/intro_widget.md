# Kalshi Exotics (incl Combos) — Dashboard Overview

**Kalshi launched Exotic markets on September 17, 2025**, with the first
product being NFL multi-game parlays (`KXMVENFLMULTIGAME`). New KXMVE
families rolled out over the following months tied to major sporting and
cultural events — NBA in November, Grammys in late January, Cross-Category and
Oscars in February 2026, March Madness in mid-March. The cross-category product
(`KXMVECROSSCATEGORY`) launched on February 27, 2026.

An Exotic is a multi-leg prediction-market contract where **all legs must
resolve correctly** for the position to pay out. Payouts compound across legs —
higher return at higher risk, conceptually similar to a sports betting parlay.
Kalshi brands these as "Combos" on its platform.

### What we count as an exotic
We use a **structural definition**: any market whose ticker begins with `KXMVE`
(Kalshi MultiVariate Event) — Kalshi's deterministic prefix for every multi-leg
parlay. This definition was derived by pulling each KXMVE series' metadata
directly from Kalshi's public API and cross-referencing it against the Dune
table.

### The 11 KXMVE product families

- **`KXMVESPORTSMULTIGAMEEXTENDED` — MVE Sport Multi Game**
  - Multi-game parlays across any combination of sports (NBA, MLB, NHL, soccer, UFC, tennis, etc.). Each leg is a player prop, game outcome, or game stat.
  - *Real example:* "yes Mobley 10+ pts, yes Allen 10+ pts, yes Harden 15+ pts, yes Wembanyama 20+ pts" — 4-leg NBA player-prop stack across two games.

- **`KXMVECROSSCATEGORY` — MVE Cross Category**
  - Designed to span any market categories (sports, politics, crypto, macro, etc.). In practice today, used predominantly cross-sport — combining legs from different leagues/sports.
  - *Real example:* "yes Liverpool, yes Tampa Bay, yes Atlanta" — 3-leg parlay mixing EPL soccer + two MLB baseball games.

- **`KXMVENFLSINGLEGAME` — MVE NFL Single Game**
  - Multi-outcome bets *within a single NFL game* — combine spreads, totals, and player props for the same matchup.
  - *Typical structure:* "Mahomes throws TD AND Chiefs win AND Over 47.5 points" — 3-leg in-game parlay.

- **`KXMVENFLMULTIGAMEEXTENDED` — MVE NFL Multi Game Extended**
  - Parlays *across multiple NFL games*, typically a single week's slate. Each leg is a game outcome, spread, total, or player prop.
  - *Typical structure:* "yes Chiefs win, yes Bills win, yes 49ers cover, yes Over 51.5 in Cowboys game".

- **`KXMVENBASINGLEGAME` — MVE NBA Single Game**
  - Multi-outcome bets within a single NBA game (spreads, totals, player props all on the same game).
  - *Real example:* "no Cleveland wins by 9.5+, yes Over 201.5 pts scored" — 2-leg in-game (spread + total).

- **`KXMVECBCHAMPIONSHIP` — MVE College Basketball Championship**
  - Tournament-shaped parlays predicting multiple teams advancing through March Madness rounds.
  - *Real example:* "yes Illinois, yes Michigan" — 2-leg progression bet (different tournament rounds).

- **`KXMVEOSCARS` — MVE Oscars**
  - Parlays combining outcomes from multiple Oscar categories.
  - *Real example:* "yes Renate Reinsve (Best Actress), yes The Voice of Hind Rajab (Best Intl Film), yes One Battle After Another (Best Picture)" — 3-leg awards parlay.

- **`KXMVEGRAMMYS` — MVE Grammys**
  - Same structure as Oscars but for Grammy categories (Album of the Year, Song of the Year, Best New Artist, etc.).

- **`KXMVENFLMULTIGAME` — MVE NFL Multi Game**
  - A parallel/older variant of `MULTIGAMEEXTENDED` for NFL multi-game parlays. Same idea, less common.

- **`KXMVEMENTIONSSINGLE` — MVE Mention**
  - Markets tied to a person/topic being *mentioned* during a televised event or speech. The only KXMVE that Kalshi files under `Mentions` rather than `Exotics`. Treated as borderline in our taxonomy.

- **`KXMVENBAMULTIGAMEEXTENDED` — MVE NBA Multi Game**
  - Same concept as NFL multi-game but for the NBA slate — parlays across multiple NBA games on a single night/week.

### Note on Cross-Category
Kalshi designed `KXMVECROSSCATEGORY` as a product that can span *any* market
categories — Sports, Politics, Crypto, etc. To see how it's actually used, we
sampled **all 135,426 currently-open CROSSCATEGORY parlays** via the Kalshi
API and inspected each parlay's leg composition: **99.89% used all-Sports
legs**, 0.11% mixed Sports + Crypto, and only 2 parlays were all-Crypto. No
Politics, Macro, or other-domain legs appeared. The product is genuinely
cross-category in design; current trader behavior skews overwhelmingly to
cross-sport multi-game.

### Note on Mentions
`KXMVEMENTIONSSINGLE` is the only KXMVE that Kalshi's API categorizes as
`Mentions` rather than `Exotics`. Tiny activity. Treated as borderline in our
taxonomy.

### What this dashboard tracks
- Total exotic activity since launch and its share of total Kalshi volume
- Weekly and monthly growth trends
- Breakdown by **Domain** (subject), **Variant** (structure), and **Series**
  (Kalshi product) — three zoom levels of the same data
- **Notional** vs **Premium** views: notional = contracts × $1 face value
  (industry headline); premium = actual cash exchanged (~10% of notional)
- Live vs dormant market counts per series

> **Data sources:** `kalshi.market_report` on Dune Analytics for volume and open
> interest; **Kalshi's public API** (`api.elections.kalshi.com/trade-api/v2`)
> for series metadata, categorization, and leg composition. Cross-referencing
> the two sources surfaced the methodology decisions that drive this dashboard
> (see the full methodology widget at the bottom).
