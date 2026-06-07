-- =====================================================================
-- SUB-1¢ CORRECTION — Corrected Dune queries (June 2026)
-- =====================================================================
-- WHY: Dune's kalshi.trade_report.price column stores price as an INTEGER
-- number of cents and TRUNCATES (floors). All trades priced 0.1¢–0.9¢
-- (Kalshi's deci-cent ticks) are stored as price = 0. The old queries
-- filtered `price > 0`, which silently DELETED ~2.9M real sub-1¢ trades.
--
-- FIX: treat `price = 0 AND contracts_traded > 0` as the "sub-1¢" bucket.
-- For price/handle precision, the true price is recovered from Kalshi's
-- API (yes_price_dollars); within Dune we use an effective-price proxy:
--   price = 0  -> 0.367¢  (contract-weighted mean from API sample)
--   price = N  -> N + 0.45¢ (midpoint of the floored deci-cent range)
--
-- WINDOW: all queries pinned to the report snapshot, Sep 17 2025 – Jun 1 2026.
-- True corrected trade count = 32,457,465 (was 29,562,842 with price>0).
-- =====================================================================


-- ---------------------------------------------------------------------
-- 7622547 (corrected) — Trade count by price tick, INCLUDING sub-1¢
-- Powers Fig 15b (implied probability distribution)
-- ---------------------------------------------------------------------
SELECT price,                       -- 0 = sub-1¢ bucket (0.1–0.9¢)
       COUNT(*) AS trades
FROM kalshi.trade_report
WHERE report_ticker LIKE 'KXMVE%'
  AND date >= '2025-09-17' AND date <= '2026-06-01'
  AND contracts_traded > 0
  AND price BETWEEN 0 AND 99
GROUP BY price
ORDER BY price;


-- ---------------------------------------------------------------------
-- 7622663 (corrected) — Handle by price tick, flooring-corrected
-- Powers Fig 15a (handle by price point)
-- ---------------------------------------------------------------------
SELECT price,
       SUM(contracts_traded
           * (CASE WHEN price = 0 THEN 0.367 ELSE price + 0.45 END) / 100.0) AS handle_usd
FROM kalshi.trade_report
WHERE report_ticker LIKE 'KXMVE%'
  AND date >= '2025-09-17' AND date <= '2026-06-01'
  AND contracts_traded > 0
  AND price BETWEEN 0 AND 99
GROUP BY price
ORDER BY price;


-- ---------------------------------------------------------------------
-- 7623140 (corrected) — Trades & handle by implied-probability bucket
-- Powers Fig 15 (paired trades vs handle). Bottom bucket = 0-2¢ extreme longshots.
-- ---------------------------------------------------------------------
WITH t AS (
  SELECT
    CASE
      WHEN price <= 2  THEN '1: 0-2c (extreme longshots)'
      WHEN price <= 5  THEN '2: 3-5c'
      WHEN price <= 15 THEN '3: 6-15c'
      WHEN price <= 30 THEN '4: 16-30c'
      WHEN price <= 50 THEN '5: 31-50c'
      ELSE                  '6: 51-99c'
    END AS bucket,
    MIN(price) OVER () AS dummy,
    contracts_traded,
    contracts_traded * (CASE WHEN price = 0 THEN 0.367 ELSE price + 0.45 END) / 100.0 AS handle
  FROM kalshi.trade_report
  WHERE report_ticker LIKE 'KXMVE%'
    AND date >= '2025-09-17' AND date <= '2026-06-01'
    AND contracts_traded > 0 AND price BETWEEN 0 AND 99
)
SELECT bucket,
       COUNT(*) AS trades,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_trades,
       ROUND(SUM(handle), 0) AS handle_usd,
       ROUND(100.0 * SUM(handle) / SUM(SUM(handle)) OVER (), 1) AS pct_handle
FROM t
GROUP BY bucket
ORDER BY bucket;


-- ---------------------------------------------------------------------
-- 7598456 (corrected) — Monthly longshot share (replaces "1¢ floor")
-- Powers Fig 16a (sub-1¢ share) and Fig 16b (0-2¢ share)
-- ---------------------------------------------------------------------
SELECT
    date_trunc('month', CAST(date AS date)) AS month,
    ROUND(100.0 * SUM(CASE WHEN price = 0  THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_sub1c,   -- Fig 16a
    ROUND(100.0 * SUM(CASE WHEN price <= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_0to2c     -- Fig 16b
FROM kalshi.trade_report
WHERE report_ticker LIKE 'KXMVE%'
  AND date >= '2025-09-17' AND date <= '2026-06-01'
  AND contracts_traded > 0
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------------------
-- 7557750 (corrected) — Trade-size buckets, INCLUDING sub-1¢ trades
-- Powers Fig 18 (trade size: % trades vs % cash)
-- ---------------------------------------------------------------------
WITH t AS (
  SELECT contracts_traded
         * (CASE WHEN price = 0 THEN 0.367 ELSE price + 0.45 END) / 100.0 AS cash
  FROM kalshi.trade_report
  WHERE report_ticker LIKE 'KXMVE%'
    AND date >= '2025-09-17' AND date <= '2026-06-01'
    AND contracts_traded > 0 AND price BETWEEN 0 AND 99
)
SELECT
  CASE
    WHEN cash < 2   THEN '1: Under $2'
    WHEN cash < 5   THEN '2: $2-5'
    WHEN cash < 10  THEN '3: $5-10'
    WHEN cash < 20  THEN '4: $10-20'
    WHEN cash < 50  THEN '5: $20-50'
    WHEN cash < 200 THEN '6: $50-200'
    ELSE                 '7: $200+'
  END AS bucket,
  COUNT(*) AS trades,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_trades,
  ROUND(100.0 * SUM(cash) / SUM(SUM(cash)) OVER (), 1) AS pct_cash
FROM t
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------------------
-- 7576002 (corrected) — Fee revenue by product, INCLUDING sub-1¢
-- Powers Fig 19. Taker fee = 0.07 * contracts * p * (1-p), p in [0,1].
-- Uses effective price so sub-1¢ trades contribute (was dropped before, ~+$1.8M).
-- ---------------------------------------------------------------------
WITH t AS (
  SELECT report_ticker,
         contracts_traded AS c,
         (CASE WHEN price = 0 THEN 0.367 ELSE price + 0.45 END) / 100.0 AS p   -- price as fraction
  FROM kalshi.trade_report
  WHERE report_ticker LIKE 'KXMVE%'
    AND date >= '2025-09-17' AND date <= '2026-06-01'
    AND contracts_traded > 0 AND price BETWEEN 0 AND 99
)
SELECT report_ticker,
       COUNT(*) AS trades,
       ROUND(SUM(c * p), 0) AS handle_usd,
       ROUND(SUM(0.07 * c * p * (1 - p)), 0) AS est_taker_fee_usd
FROM t
GROUP BY 1
ORDER BY est_taker_fee_usd DESC;
