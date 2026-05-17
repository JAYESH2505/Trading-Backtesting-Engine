import pandas as pd
def ma_crossover(df, fast_period=10, slow_period=50):
    df['fast_ma'] = df['close'].rolling(window=fast_period).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_period).mean()

    signals = []
    for i in range(1, len(df)):
        # Skip rows where MAs aren't ready yet
        if pd.isna(df['fast_ma'].iloc[i]) or pd.isna(df['slow_ma'].iloc[i]):
            continue

        if df['fast_ma'].iloc[i] > df['slow_ma'].iloc[i] and df['fast_ma'].iloc[i-1] <= df['slow_ma'].iloc[i-1]:
            signals.append({'index': i, 'signal': 'BUY',  'price': df['close'].iloc[i], 'timestamp': df['timestamp'].iloc[i]})

        elif df['fast_ma'].iloc[i] < df['slow_ma'].iloc[i] and df['fast_ma'].iloc[i-1] >= df['slow_ma'].iloc[i-1]:
            signals.append({'index': i, 'signal': 'SELL', 'price': df['close'].iloc[i], 'timestamp': df['timestamp'].iloc[i]})

    return signals