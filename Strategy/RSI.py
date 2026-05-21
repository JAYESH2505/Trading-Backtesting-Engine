import pandas as pd


def rsi_strategy(df, period=14, overbought=70, oversold=30):
    delta = df['close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = delta.where(delta < 0, 0) * -1

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    avg_loss = avg_loss.replace(0, 1e-10)  # prevent division by zero

    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    df['rsi'] = rsi
    signals = []

    for i in range(1, len(df)):
        if pd.isna(df['rsi'].iloc[i]):
            continue

        if df['rsi'].iloc[i-1] < oversold and df['rsi'].iloc[i] >= oversold:
            signals.append({
                'signal':    'BUY',
                'price':     df['close'].iloc[i],
                'timestamp': df['timestamp'].iloc[i]
            })

        elif df['rsi'].iloc[i-1] > overbought and df['rsi'].iloc[i] <= overbought:
            signals.append({
                'signal':    'SELL',
                'price':     df['close'].iloc[i],
                'timestamp': df['timestamp'].iloc[i]
            })

    return signals