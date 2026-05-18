import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd


# ─────────────────────────────────────────
# 1. EQUITY CURVE
#    Cumulative P&L plotted over time
# ─────────────────────────────────────────
def plot_equity_curve(paired, strategy_name="Strategy"):
    times  = [t['exit_time'] for t in paired]
    pnls   = [t['pnl']       for t in paired]

    cumulative = []
    total = 0
    for p in pnls:
        total += p
        cumulative.append(total)

    plt.figure(figsize=(12, 5))
    plt.plot(times, cumulative, color='steelblue', linewidth=2)

    # Fill green above 0, red below 0
    plt.fill_between(times, cumulative, 0,
                     where=[c >= 0 for c in cumulative],
                     color='green', alpha=0.15, label='Profit zone')
    plt.fill_between(times, cumulative, 0,
                     where=[c < 0 for c in cumulative],
                     color='red', alpha=0.15, label='Loss zone')

    plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    plt.title(f'Equity Curve — {strategy_name}', fontsize=14)
    plt.xlabel('Date')
    plt.ylabel('Cumulative P&L')
    plt.legend()
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────
# 2. DRAWDOWN CHART
#    Shows how far below peak you are at each point
# ─────────────────────────────────────────
def plot_drawdown(paired, strategy_name="Strategy"):
    pnls = [t['pnl'] for t in paired]
    times = [t['exit_time'] for t in paired]

    cumulative = []
    total = 0
    for p in pnls:
        total += p
        cumulative.append(total)

    # Calculate drawdown at each point
    peak = 0
    drawdowns = []
    for c in cumulative:
        if c > peak:
            peak = c
        drawdowns.append(c - peak)  # always 0 or negative

    plt.figure(figsize=(12, 4))
    plt.fill_between(times, drawdowns, 0, color='red', alpha=0.4)
    plt.plot(times, drawdowns, color='darkred', linewidth=1)
    plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    plt.title(f'Drawdown Chart — {strategy_name}', fontsize=14)
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────
# 3. PERFORMANCE METRICS BAR CHART
#    Win rate, profit factor, risk/reward
# ─────────────────────────────────────────
def plot_metrics_bar(metrics, strategy_name="Strategy"):
    # Only show metrics that make sense on one scale
    labels = ['Win Rate (%)', 'Profit Factor', 'Risk/Reward']
    values = [
        metrics['win_rate'],
        min(metrics['profit_factor'], 10),  # cap at 10 so chart isn't distorted
        min(metrics['risk_reward'],   10),
    ]

    colors = ['steelblue', 'seagreen', 'darkorange']

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=colors, width=0.5)

    # Write value on top of each bar
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.5,
                 f'{val:.2f}',
                 ha='center', va='bottom', fontsize=11)

    plt.title(f'Performance Metrics — {strategy_name}', fontsize=14)
    plt.ylabel('Value')
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────
# 4. TRADE DISTRIBUTION PIE CHART
#    Winning vs Losing trades
# ─────────────────────────────────────────
def plot_trade_distribution(metrics, strategy_name="Strategy"):
    labels = ['Winning Trades', 'Losing Trades']
    sizes  = [metrics['winning_trades'], metrics['losing_trades']]
    colors = ['seagreen', 'crimson']
    explode = (0.05, 0)  # slightly separate the winning slice

    plt.figure(figsize=(6, 6))
    plt.pie(sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct='%1.1f%%',
            startangle=140)
    plt.title(f'Trade Distribution — {strategy_name}', fontsize=14)
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────
# 5. STRATEGY COMPARISON BAR CHART
#    Compare multiple strategies on same dataset
# ─────────────────────────────────────────
def plot_strategy_comparison(results: dict):
    """
    results = {
        'MA Crossover': {'win_rate': 55, 'total_pnl': 320, 'max_drawdown': 80},
        'RSI Strategy': {'win_rate': 48, 'total_pnl': 210, 'max_drawdown': 120},
    }
    """
    strategies = list(results.keys())
    win_rates   = [results[s]['win_rate']    for s in strategies]
    total_pnls  = [results[s]['total_pnl']   for s in strategies]
    drawdowns   = [results[s]['max_drawdown'] for s in strategies]

    x = range(len(strategies))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    b1 = ax.bar([i - width for i in x], win_rates,  width, label='Win Rate (%)',    color='steelblue')
    b2 = ax.bar([i         for i in x], total_pnls, width, label='Total P&L',       color='seagreen')
    b3 = ax.bar([i + width for i in x], drawdowns,  width, label='Max Drawdown',    color='crimson')

    ax.set_xticks(list(x))
    ax.set_xticklabels(strategies, fontsize=11)
    ax.set_title('Strategy Comparison', fontsize=14)
    ax.set_ylabel('Value')
    ax.legend()
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────
# 6. FULL DASHBOARD — all charts at once
# ─────────────────────────────────────────
def plot_dashboard(paired, metrics, strategy_name="Strategy"):
    times      = [t['exit_time'] for t in paired]
    pnls       = [t['pnl']       for t in paired]

    # Build cumulative and drawdown series
    cumulative, drawdowns = [], []
    total, peak = 0, 0
    for p in pnls:
        total += p
        cumulative.append(total)
        if total > peak:
            peak = total
        drawdowns.append(total - peak)

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(f'Backtest Dashboard — {strategy_name}', fontsize=16, y=1.01)
    gs  = gridspec.GridSpec(2, 2, figure=fig)

    # Top-left: Equity curve
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(times, cumulative, color='steelblue', linewidth=2)
    ax1.fill_between(times, cumulative, 0,
                     where=[c >= 0 for c in cumulative],
                     color='green', alpha=0.15)
    ax1.fill_between(times, cumulative, 0,
                     where=[c < 0 for c in cumulative],
                     color='red', alpha=0.15)
    ax1.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax1.set_title('Equity Curve')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative P&L')

    # Top-right: Drawdown
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.fill_between(times, drawdowns, 0, color='red', alpha=0.4)
    ax2.plot(times, drawdowns, color='darkred', linewidth=1)
    ax2.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax2.set_title('Drawdown')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown')

    # Bottom-left: Metrics bar
    ax3 = fig.add_subplot(gs[1, 0])
    labels = ['Win Rate (%)', 'Profit Factor', 'Risk/Reward']
    values = [
        metrics['win_rate'],
        min(metrics['profit_factor'], 10),
        min(metrics['risk_reward'],   10),
    ]
    bars = ax3.bar(labels, values,
                   color=['steelblue', 'seagreen', 'darkorange'], width=0.5)
    for bar, val in zip(bars, values):
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.3,
                 f'{val:.2f}', ha='center', fontsize=10)
    ax3.set_title('Performance Metrics')
    ax3.set_ylabel('Value')

    # Bottom-right: Pie chart
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.pie(
        [metrics['winning_trades'], metrics['losing_trades']],
        labels=['Winning', 'Losing'],
        colors=['seagreen', 'crimson'],
        autopct='%1.1f%%',
        startangle=140,
        explode=(0.05, 0)
    )
    ax4.set_title('Trade Distribution')

    plt.tight_layout()
    plt.show()