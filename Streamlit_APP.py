import streamlit as st
import matplotlib.pyplot as plt
import mysql.connector
import pandas as pd
from datetime import date

from config import DB_CONFIG
from Backtest.BackTestingEngine import run_backtest, compare_strategies

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title = "Trading Backtester",
    page_icon  = "📈",
    layout     = "wide"
)

# ─────────────────────────────────────────
# HELPERS — fetch data from DB for dropdowns
# ─────────────────────────────────────────
@st.cache_data
def get_assets():
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id, symbol, name FROM assets")
    rows   = cursor.fetchall()
    conn.close()
    return rows

@st.cache_data
def get_users():
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    rows   = cursor.fetchall()
    conn.close()
    return rows

def get_backtest_history():
    conn = mysql.connector.connect(**DB_CONFIG)
    df   = pd.read_sql("""
        SELECT result_id, strategy_name, asset,
               date_from, date_to, return_pct,
               win_rate, max_drawdown, total_trades, ran_at
        FROM v_backtest_overview
        ORDER BY ran_at DESC
        LIMIT 20
    """, conn)
    conn.close()
    return df

# ─────────────────────────────────────────
# SIDEBAR — all user inputs
# ─────────────────────────────────────────
st.sidebar.title("⚙️ Backtest Settings")

# User selector
users       = get_users()
user_labels = {u[1]: u[0] for u in users}
username    = st.sidebar.selectbox("User", list(user_labels.keys()))
user_id     = user_labels[username]

# Asset selector
assets       = get_assets()
asset_labels = {f"{a[1]} — {a[2]}": a[1] for a in assets}
asset_choice = st.sidebar.selectbox("Asset", list(asset_labels.keys()))
asset_symbol = asset_labels[asset_choice]

# Strategy selector
strategy = st.sidebar.selectbox(
    "Strategy",
    ["ma_crossover", "rsi"]
)

# Date range
col1, col2 = st.sidebar.columns(2)
date_from  = col1.date_input("From", value=date(2020, 1, 1))
date_to    = col2.date_input("To",   value=date(2023, 12, 31))

# Capital and quantity
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)", min_value=100, value=10000, step=500
)
quantity = st.sidebar.number_input(
    "Quantity per Trade", min_value=1, value=1, step=1
)

# Strategy parameters
st.sidebar.markdown("---")
st.sidebar.subheader("Strategy Parameters")

strategy_params = {}
if strategy == "ma_crossover":
    strategy_params['fast_period'] = st.sidebar.slider(
        "Fast MA Period", min_value=5,  max_value=50,  value=10
    )
    strategy_params['slow_period'] = st.sidebar.slider(
        "Slow MA Period", min_value=20, max_value=200, value=50
    )
elif strategy == "rsi":
    strategy_params['period']      = st.sidebar.slider(
        "RSI Period",    min_value=5,  max_value=30,  value=14
    )
    strategy_params['oversold']    = st.sidebar.slider(
        "Oversold Level",  min_value=10, max_value=40,  value=30
    )
    strategy_params['overbought']  = st.sidebar.slider(
        "Overbought Level", min_value=60, max_value=90, value=70
    )

# Run button
run = st.sidebar.button("🚀 Run Backtest", use_container_width=True)

# ─────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────
st.title("📈 Trading Strategy Backtesting Engine")
st.caption("Test trading strategies against historical market data.")

# ─────────────────────────────────────────
# RUN BACKTEST ON BUTTON CLICK
# ─────────────────────────────────────────
if run:
    with st.spinner("Running backtest..."):
        result = run_backtest(
            user_id         = user_id,
            asset_symbol    = asset_symbol,
            strategy_name   = strategy,
            date_from       = str(date_from),
            date_to         = str(date_to),
            initial_capital = initial_capital,
            quantity        = quantity,
            **strategy_params
        )

    if result is None:
        st.error("Backtest failed. Check your date range or asset data.")

    else:
        metrics       = result['metrics']
        paired        = result['paired']
        final_capital = result['final_capital']

        # ── Metrics row ──────────────────────────
        st.subheader("📊 Performance Summary")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total Trades",   metrics['total_trades'])
        c2.metric("Win Rate",       f"{metrics['win_rate']}%")
        c3.metric("Total P&L",      f"${metrics['total_pnl']:.2f}")
        c4.metric("Max Drawdown",   f"${metrics['max_drawdown']:.2f}")
        c5.metric("Profit Factor",  f"{metrics['profit_factor']:.2f}")
        c6.metric("Final Capital",  f"${final_capital:,.2f}")

        st.markdown("---")

        # ── Charts row ───────────────────────────
        st.subheader("📉 Analytics Charts")

        times      = [t['exit_time'] for t in paired]
        pnls       = [t['pnl']       for t in paired]
        cumulative, drawdowns = [], []
        total, peak = 0, 0
        for p in pnls:
            total += p
            cumulative.append(total)
            if total > peak:
                peak = total
            drawdowns.append(total - peak)

        left, right = st.columns(2)

        # Equity curve
        with left:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(times, cumulative, color='steelblue', linewidth=2)
            ax.fill_between(times, cumulative, 0,
                            where=[c >= 0 for c in cumulative],
                            color='green', alpha=0.15)
            ax.fill_between(times, cumulative, 0,
                            where=[c < 0 for c in cumulative],
                            color='red', alpha=0.15)
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
            ax.set_title('Equity Curve')
            ax.set_xlabel('Date')
            ax.set_ylabel('Cumulative P&L')
            st.pyplot(fig)
            plt.close(fig)

        # Drawdown
        with right:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.fill_between(times, drawdowns, 0, color='red', alpha=0.4)
            ax.plot(times, drawdowns, color='darkred', linewidth=1)
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
            ax.set_title('Drawdown')
            ax.set_xlabel('Date')
            ax.set_ylabel('Drawdown')
            st.pyplot(fig)
            plt.close(fig)

        left2, right2 = st.columns(2)

        # Metrics bar
        with left2:
            fig, ax = plt.subplots(figsize=(7, 4))
            labels = ['Win Rate (%)', 'Profit Factor', 'Risk/Reward']
            values = [
                metrics['win_rate'],
                min(metrics['profit_factor'], 10),
                min(metrics['risk_reward'],   10),
            ]
            bars = ax.bar(labels, values,
                          color=['steelblue', 'seagreen', 'darkorange'],
                          width=0.5)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f'{val:.2f}', ha='center', fontsize=10)
            ax.set_title('Performance Metrics')
            st.pyplot(fig)
            plt.close(fig)

        # Pie chart
        with right2:
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(
                [metrics['winning_trades'], metrics['losing_trades']],
                labels  = ['Winning', 'Losing'],
                colors  = ['seagreen', 'crimson'],
                autopct = '%1.1f%%',
                explode = (0.05, 0),
                startangle = 140
            )
            ax.set_title('Trade Distribution')
            st.pyplot(fig)
            plt.close(fig)

        # ── Trade history table ───────────────────
        st.markdown("---")
        st.subheader("📋 Trade History")
        trade_df = pd.DataFrame(paired)
        trade_df['pnl'] = trade_df['pnl'].round(4)
        trade_df['result'] = trade_df['pnl'].apply(
            lambda x: '✅ Win' if x > 0 else '❌ Loss'
        )
        st.dataframe(trade_df, use_container_width=True)

# ─────────────────────────────────────────
# BACKTEST HISTORY TABLE
# ─────────────────────────────────────────
st.markdown("---")
st.subheader("🕓 Recent Backtest History")
try:
    history = get_backtest_history()
    if history.empty:
        st.info("No backtests run yet.")
    else:
        st.dataframe(history, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load history: {e}")