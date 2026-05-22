import mysql.connector
from config import DB_CONFIG


# ─────────────────────────────────────────
# 1. PAIR TRADES
# ─────────────────────────────────────────
def pair_trades(signals):
    paired = []
    open_trade = None

    for signal in signals:
        if signal['signal'] == 'BUY' and open_trade is None:
            open_trade = signal

        elif signal['signal'] == 'SELL' and open_trade is not None:
            paired.append({
                'entry_price': open_trade['price'],
                'exit_price':  signal['price'],
                'entry_time':  open_trade['timestamp'],
                'exit_time':   signal['timestamp'],
                'pnl':         signal['price'] - open_trade['price']
            })
            open_trade = None

    return paired


# ─────────────────────────────────────────
# 2. MAX DRAWDOWN
# ─────────────────────────────────────────
def max_drawdown(paired):
    peak       = 0
    max_dd     = 0
    cumulative = 0

    for trade in paired:
        cumulative += trade['pnl']
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_dd:
            max_dd = drawdown

    return max_dd


# ─────────────────────────────────────────
# 3. CALCULATE ALL METRICS
# ─────────────────────────────────────────
def calculate_metrics(paired):
    total_trades   = len(paired)
    winning_trades = sum(1 for t in paired if t['pnl'] > 0)
    losing_trades  = sum(1 for t in paired if t['pnl'] < 0)

    win_rate     = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl    = sum(t['pnl'] for t in paired)

    gross_profit  = sum(t['pnl'] for t in paired if t['pnl'] > 0)
    gross_loss    = sum(t['pnl'] for t in paired if t['pnl'] < 0) * -1
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0

    # Risk-reward: average win / average loss
    avg_win  = (gross_profit / winning_trades) if winning_trades > 0 else 0
    avg_loss = (gross_loss  / losing_trades)   if losing_trades  > 0 else 0
    risk_reward = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    return {
        'total_trades':    total_trades,
        'winning_trades':  winning_trades,
        'losing_trades':   losing_trades,
        'win_rate':        round(win_rate,    2),
        'total_pnl':       round(total_pnl,   8),
        'profit_factor':   round(profit_factor, 4),
        'risk_reward':     round(risk_reward,   4),
        'max_drawdown':    round(max_drawdown(paired), 8),
    }


# ─────────────────────────────────────────
# 4. SAVE BACKTEST RESULT TO DB
# ─────────────────────────────────────────
def save_backtest_result(user_id, strategy_id, asset_id,
                         date_from, date_to,
                         initial_capital, final_capital, conn):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO backtest_results
            (user_id, strategy_id, asset_id, date_from, date_to,
             initial_capital, final_capital)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, strategy_id, asset_id, date_from, date_to,
          initial_capital, final_capital))

    result_id = cursor.lastrowid  # grab the new PK before committing
    conn.commit()
    cursor.close()
    return result_id


# ─────────────────────────────────────────
# 5. SAVE PERFORMANCE METRICS TO DB
# ─────────────────────────────────────────
def save_metrics(result_id, metrics, conn):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO performance_metrics
            (result_id, win_rate, total_pnl, max_drawdown,
             risk_reward_ratio, profit_factor,
             total_trades, winning_trades, losing_trades)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        result_id,
        metrics['win_rate'],
        metrics['total_pnl'],
        metrics['max_drawdown'],
        metrics['risk_reward'],
        metrics['profit_factor'],
        metrics['total_trades'],
        metrics['winning_trades'],
        metrics['losing_trades'],
    ))
    conn.commit()
    cursor.close()


# ─────────────────────────────────────────
# 6. MAIN — RUN FULL METRICS PIPELINE
# ─────────────────────────────────────────
def run_metrics_pipeline(signals, user_id, strategy_id, asset_id,
                         date_from, date_to, initial_capital):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)

        # Step 1 — pair signals into completed trades
        paired = pair_trades(signals)
        if not paired:
            print("[!] No completed trades to evaluate.")
            return

        # Step 2 — calculate all metrics
        metrics = calculate_metrics(paired)

        # Step 3 — calculate final capital
        final_capital = initial_capital + metrics['total_pnl']

        # Step 4 — save backtest result row
        result_id = save_backtest_result(
            user_id, strategy_id, asset_id,
            date_from, date_to,
            initial_capital, final_capital, conn
        )

        # Step 5 — save metrics row linked to result
        save_metrics(result_id, metrics, conn)

        print(f"[+] Backtest saved. result_id = {result_id}")
        print(f"    Win Rate:      {metrics['win_rate']}%")
        print(f"    Total P&L:     {metrics['total_pnl']}")
        print(f"    Max Drawdown:  {metrics['max_drawdown']}")
        print(f"    Profit Factor: {metrics['profit_factor']}")
        print(f"    Risk/Reward:   {metrics['risk_reward']}")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        conn.close()