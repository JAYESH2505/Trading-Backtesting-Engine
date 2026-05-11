def save_trades(signals, user_id, asset_id, strategy_id, quantity, conn):
    cursor = conn.cursor()
    for signal in signals:
        cursor.execute("""
            INSERT INTO trades 
                (user_id, asset_id, strategy_id, trade_type, quantity, entry_price, entry_time, status)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            asset_id,
            strategy_id,
            signal['signal'],
            quantity,
            signal['price'],
            signal['timestamp'],
            'OPEN'
        ))
    conn.commit()