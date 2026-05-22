import yfinance as yf

df = yf.download("AAPL", start="2020-01-01", end="2023-12-31")
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
df.columns = ['open', 'high', 'low', 'close', 'volume']
df.index.name = 'timestamp'
df.to_csv("AAPL_2023.csv")
print("Done — AAPL_2023.csv saved.")