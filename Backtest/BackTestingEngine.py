import pandas as pd
import mysql.connector
from config import DB_CONFIG
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()

from Strategy.MovingAverageCrossOver import ma_crossover
from Strategy.RSI                    import rsi_strategy
from Strategy.Save_Trades            import save_trades
from Metrics.PerformanceMetrics      import (pair_trades, calculate_metrics,
                                             save_backtest_result, save_metrics)
from Analytics.Charts                import plot_dashboard


# ─────────────────────────────────────────
# AVAILABLE STRATEGIES
# Add new strategies here as you build them
# ─────────────────────────────────────────
STRATEGIES = {
    'ma_crossover': ma_crossover,
    'rsi':          rsi_strategy,
}


# ─────────────────────────────────────────
# 1. LOAD HISTORICAL PRICES FROM DB
#    Pulls OHLCV rows for a given asset
#    and date range into a Pandas DataFrame
# ─────────────────────────────────────────

def get_engine():
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host     = os.getenv("DB_HOST")
    db       = os.getenv("DB_NAME")
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{db}")
def load_prices(asset_symbol, date_from, date_to, conn):
    query = """
        SELECT
            hp.timestamp,
            hp.open,
            hp.high,
            hp.low,
            hp.close,
            hp.volume
        FROM historical_prices hp
        JOIN assets a ON hp.asset_id = a.asset_id
        WHERE a.symbol    = %s
          AND hp.timestamp BETWEEN %s AND %s
        ORDER BY hp.timestamp ASC
    """
    engine = get_engine()
    df = pd.read_sql(query, engine, params=(asset_symbol, date_from, date_to))

    if df.empty:
        raise ValueError(
            f"No price data found for '{asset_symbol}' "
            f"between {date_from} and {date_to}."
        )

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"[+] Loaded {len(df)} rows for {asset_symbol}.")
    return df


# ─────────────────────────────────────────
# 2. GET IDs FROM DB
#    Looks up asset_id and strategy_id
#    by their human-readable names
# ─────────────────────────────────────────
def get_asset_id(symbol, cursor):
    cursor.execute(
        "SELECT asset_id FROM assets WHERE symbol = %s", (symbol,)
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Asset '{symbol}' not found in database.")
    return row[0]


def get_strategy_id(name, cursor):
    cursor.execute(
        "SELECT strategy_id FROM strategies WHERE name = %s", (name,)
    )
    row = cursor.fetchone()
    if not row:
        # Auto-insert strategy if it doesn't exist yet
        cursor.execute(
            "INSERT INTO strategies (name) VALUES (%s)", (name,)
        )
        return cursor.lastrowid
    return row[0]


# ─────────────────────────────────────────
# 3. MAIN BACKTEST RUNNER
#    Full pipeline in one function call
# ─────────────────────────────────────────
def run_backtest(user_id, asset_symbol, strategy_name,
                 date_from, date_to, initial_capital,
                 quantity=1, **strategy_params):
    print(f"\n{'='*50}")
    print(f"  Backtest: {strategy_name} on {asset_symbol}")
    print(f"  Period:   {date_from} → {date_to}")
    print(f"  Capital:  ${initial_capital:,.2f}")
    print(f"{'='*50}")

    # Validate strategy exists
    if strategy_name not in STRATEGIES:
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available: {list(STRATEGIES.keys())}"
        )

    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # ── Step 1: Resolve IDs ──────────────────
        asset_id    = get_asset_id(asset_symbol, cursor)
        strategy_id = get_strategy_id(strategy_name, cursor)
        conn.commit()  # commit auto-insert if strategy was new

        # ── Step 2: Load price data from DB ──────
        df = load_prices(asset_symbol, date_from, date_to, conn)

        # ── Step 3: Run strategy → get signals ───
        strategy_fn = STRATEGIES[strategy_name]
        signals     = strategy_fn(df, **strategy_params)

        if not signals:
            print("[!] No signals generated. Try a wider date range.")
            return None

        print(f"[+] {len(signals)} signals generated.")

        # ── Step 4: Save signals as trades to DB ─
        save_trades(signals, user_id, asset_id, strategy_id, quantity, conn)

        # ── Step 5: Pair trades → calculate metrics
        paired  = pair_trades(signals)

        if not paired:
            print("[!] No completed trade pairs found.")
            return None

        metrics = calculate_metrics(paired)
        final_capital = initial_capital + metrics['total_pnl']

        # ── Step 6: Save backtest result + metrics
        result_id = save_backtest_result(
            user_id, strategy_id, asset_id,
            date_from, date_to,
            initial_capital, final_capital, conn
        )
        save_metrics(result_id, metrics, conn)

        # ── Step 7: Print summary ─────────────────
        print(f"\n  Results:")
        print(f"  Total Trades  : {metrics['total_trades']}")
        print(f"  Win Rate      : {metrics['win_rate']}%")
        print(f"  Total P&L     : {metrics['total_pnl']:.4f}")
        print(f"  Max Drawdown  : {metrics['max_drawdown']:.4f}")
        print(f"  Profit Factor : {metrics['profit_factor']:.4f}")
        print(f"  Risk/Reward   : {metrics['risk_reward']:.4f}")
        print(f"  Final Capital : ${final_capital:,.2f}")
        print(f"  result_id     : {result_id}")

        # ── Step 8: Plot dashboard ────────────────
        plot_dashboard(paired, metrics, strategy_name=strategy_name)

        return {
            'result_id':    result_id,
            'metrics':      metrics,
            'signals':      signals,
            'paired':       paired,
            'final_capital': final_capital
        }

    except ValueError as ve:
        print(f"[!] Error: {ve}")
        return None

    except Exception as e:
        conn.rollback()
        print(f"[!] Unexpected error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────
# 4. COMPARE MULTIPLE STRATEGIES
#    Runs several strategies on the same
#    asset and date range, then compares
# ─────────────────────────────────────────
def compare_strategies(user_id, asset_symbol,
                        date_from, date_to, initial_capital,
                        strategies: list):
    """
    strategies = [
        {'name': 'ma_crossover', 'params': {'fast_period': 10, 'slow_period': 50}},
        {'name': 'rsi',          'params': {'period': 14}},
    ]
    """
    from Analytics.Charts import plot_strategy_comparison

    results = {}
    for s in strategies:
        print(f"\nRunning: {s['name']} ...")
        result = run_backtest(
            user_id, asset_symbol,
            s['name'], date_from, date_to,
            initial_capital,
            **s.get('params', {})
        )
        if result:
            results[s['name']] = result['metrics']

    if results:
        plot_strategy_comparison(results)

    return results


# ─────────────────────────────────────────
# 5. ENTRY POINT — run directly to test
# ─────────────────────────────────────────
if __name__ == "__main__":

    # Single strategy backtest
    run_backtest(
        user_id        = 1,
        asset_symbol   = 'AAPL',
        strategy_name  = 'ma_crossover',
        date_from      = '2023-01-01',
        date_to        = '2023-12-31',
        initial_capital= 10000,
        quantity       = 1,
        fast_period    = 10,
        slow_period    = 50
    )

    # Compare two strategies on same data
    compare_strategies(
        user_id        = 1,
        asset_symbol   = 'AAPL',
        date_from      = '2023-01-01',
        date_to        = '2023-12-31',
        initial_capital= 10000,
        strategies     = [
            {'name': 'ma_crossover', 'params': {'fast_period': 10, 'slow_period': 50}},
            {'name': 'rsi',          'params': {'period': 14}},
        ]
    )