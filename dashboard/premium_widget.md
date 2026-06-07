## Premium — the cash actually exchanged

**Premium** is the real money that flowed through Kalshi's exotic markets — different from notional volume.

Every Kalshi contract has a **$1 face value (notional)**, but traders don't pay $1 to buy one — they pay the contract's **price**, which reflects the market's view of how likely the bet is to win. If a 4-leg parlay trades at $0.10, you pay 10¢ per contract to acquire it. If all 4 legs hit, you receive $1 (a 10× payout). If any leg misses, you lose the $0.10.

So:
- **Premium** = `SUM(contracts × price paid)` — *what traders actually spent*
- **Notional** = `SUM(contracts × $1 face value)` — *what traders would receive if every parlay hit*

For Kalshi exotics, premium currently runs at roughly **10% of notional** — meaning the typical parlay trades at ~10¢, implying ~1-in-10 odds of winning.

### Sports-betting vocabulary

| Kalshi term | Sports-betting equivalent |
|---|---|
| Premium | Stake / wager — the cash you put down |
| Notional | Total payout if you win |
| Price (¢) | Implied probability — equivalent to 1 / decimal odds |

### What's in this section

- **Total Premium** — lifetime cash exchanged across all exotic markets since launch
- **Monthly Premium** — period-by-period cash flow; each bar is one month's activity
- **Cumulative Premium** — running total; the shape of the curve shows whether growth is accelerating or plateauing
