-- =============================================================================
-- Base query: Weekly Kalshi Volume & Open Interest by Category
-- Owner: Ommiii (you)
-- Purpose: Single source of truth for weekly Kalshi market data, grouped by
--          category. Replaces query_5910819 (owned by `datadashboards`) so the
--          dashboard no longer depends on an external user's query.
--
-- Grain: one row per (week, category)
-- Source: kalshi.market_report (daily, market-level)
--
-- Downstream consumers: any query that needs weekly Kalshi volume by category
--   (currently: 7396205, 7409732, 7409748, 7409718, 7493445 — these should be
--    repointed from `query_5910819` to `query_<this query's new id>`)
-- =============================================================================

SELECT
    DATE_TRUNC('week', DATE(date))  AS week,
    category,
    SUM(daily_volume)               AS volume,
    SUM(open_interest)              AS open_interest
FROM kalshi.market_report
GROUP BY 1, 2
