from Backtest.BackTestingEngine import run_backtest, compare_strategies

# ── Single strategy ──────────────────────
run_backtest(
    user_id         = 1,
    asset_symbol    = "AAPL",
    strategy_name   = "ma_crossover",
    date_from = "2020-01-01",
    date_to   = "2023-12-31",
    initial_capital = 10000,
    quantity        = 1,
    fast_period     = 10,
    slow_period     = 50
)

# ── Compare two strategies ───────────────
compare_strategies(
    user_id         = 1,
    asset_symbol    = "AAPL",
    date_from       = "2020-01-01",
    date_to         = "2023-12-31",
    initial_capital = 10000,
    strategies      = [
        {"name": "ma_crossover", "params": {"fast_period": 10, "slow_period": 50}},
        {"name": "rsi",          "params": {"period": 14}},
    ]
)