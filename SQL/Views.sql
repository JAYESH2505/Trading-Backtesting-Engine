-- ─────────────────────────────────────────
-- Views.sql
-- Run this after Schema.sql
-- ─────────────────────────────────────────

USE Backtesting_Engine;


-- ─────────────────────────────────────────
-- 1. TRADE SUMMARY VIEW
--    Every trade with readable names instead of raw IDs
-- ─────────────────────────────────────────
CREATE VIEW v_trade_summary AS
SELECT
    t.trade_id,
    u.username,
    a.symbol,
    s.name           AS strategy_name,
    t.trade_type,
    t.quantity,
    t.entry_price,
    t.entry_time,
    t.exit_price,
    t.exit_time,
    t.profit_loss,
    t.status
FROM trades t
JOIN users      u ON t.user_id     = u.user_id
JOIN assets     a ON t.asset_id    = a.asset_id
JOIN strategies s ON t.strategy_id = s.strategy_id;


-- ─────────────────────────────────────────
-- 2. STRATEGY PERFORMANCE VIEW
--    Aggregated metrics per strategy
-- ─────────────────────────────────────────
CREATE VIEW v_strategy_performance AS
SELECT
    s.name                                      AS strategy_name,
    COUNT(t.trade_id)                           AS total_trades,
    SUM(CASE WHEN t.profit_loss > 0 THEN 1 ELSE 0 END) AS winning_trades,
    SUM(CASE WHEN t.profit_loss < 0 THEN 1 ELSE 0 END) AS losing_trades,
    ROUND(SUM(t.profit_loss), 8)                AS total_pnl,
    ROUND(AVG(t.profit_loss), 8)                AS avg_pnl_per_trade,
    ROUND(
        SUM(CASE WHEN t.profit_loss > 0 THEN 1 ELSE 0 END)
        / COUNT(t.trade_id) * 100
    , 2)                                        AS win_rate_pct
FROM trades t
JOIN strategies s ON t.strategy_id = s.strategy_id
WHERE t.status = 'CLOSED'
GROUP BY s.strategy_id, s.name;


-- ─────────────────────────────────────────
-- 3. ASSET PERFORMANCE VIEW
--    Which assets are most profitable
-- ─────────────────────────────────────────
CREATE VIEW v_asset_performance AS
SELECT
    a.symbol,
    a.asset_type,
    COUNT(t.trade_id)            AS total_trades,
    ROUND(SUM(t.profit_loss), 8) AS total_pnl,
    ROUND(AVG(t.profit_loss), 8) AS avg_pnl_per_trade,
    ROUND(
        SUM(CASE WHEN t.profit_loss > 0 THEN 1 ELSE 0 END)
        / COUNT(t.trade_id) * 100
    , 2)                         AS win_rate_pct
FROM trades t
JOIN assets a ON t.asset_id = a.asset_id
WHERE t.status = 'CLOSED'
GROUP BY a.asset_id, a.symbol, a.asset_type;


-- ─────────────────────────────────────────
-- 4. BACKTEST OVERVIEW VIEW
--    Every backtest with strategy and asset names
--    and its performance metrics joined in
-- ─────────────────────────────────────────
CREATE VIEW v_backtest_overview AS
SELECT
    br.result_id,
    u.username,
    s.name           AS strategy_name,
    a.symbol         AS asset,
    br.date_from,
    br.date_to,
    br.initial_capital,
    br.final_capital,
    ROUND(br.final_capital - br.initial_capital, 2) AS net_profit,
    ROUND(
        (br.final_capital - br.initial_capital)
        / br.initial_capital * 100
    , 2)             AS return_pct,
    pm.win_rate,
    pm.total_trades,
    pm.max_drawdown,
    pm.profit_factor,
    pm.risk_reward_ratio,
    br.ran_at
FROM backtest_results br
JOIN users             u  ON br.user_id     = u.user_id
JOIN strategies        s  ON br.strategy_id = s.strategy_id
JOIN assets            a  ON br.asset_id    = a.asset_id
LEFT JOIN performance_metrics pm ON br.result_id = pm.result_id;


-- ─────────────────────────────────────────
-- 5. MONTHLY PNL VIEW
--    P&L grouped by month — useful for charts
-- ─────────────────────────────────────────
CREATE VIEW v_monthly_pnl AS
SELECT
    a.symbol,
    s.name                          AS strategy_name,
    DATE_FORMAT(t.exit_time, '%Y-%m') AS month,
    ROUND(SUM(t.profit_loss), 8)    AS monthly_pnl,
    COUNT(t.trade_id)               AS trades_that_month
FROM trades t
JOIN assets     a ON t.asset_id    = a.asset_id
JOIN strategies s ON t.strategy_id = s.strategy_id
WHERE t.status = 'CLOSED'
  AND t.exit_time IS NOT NULL
GROUP BY a.asset_id, s.strategy_id, month
ORDER BY month;