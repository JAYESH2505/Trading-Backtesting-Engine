project/
│
├── Assets/
├── ENV/
├── Import/
├── SQL/
│   ├── Schema.sql
│   └── Views.sql               # Step 6 — DB views for analytics queries
│
├── Strategy/
│   ├── MovingAverageCrossOver.py
│   ├── RSI.py                  # Next strategies
│   ├── Breakout.py
│   ├── SupportResistance.py
│   └── Save_Trades.py
│
├── Backtest/
│   └── BacktestEngine.py       # Runs a strategy on historical data end-to-end
│
├── Metrics/
│   └── PerformanceMetrics.py   # Win rate, P&L, drawdown, profit factor
│
├── Analytics/
│   └── Charts.py               # Matplotlib/Plotly visualizations
│
├── config.py                   # DB credentials — loaded from .env file
├── .env                        # Secrets file — NEVER push to GitHub
├── .gitignore
├── README.md
└── requirements.txt