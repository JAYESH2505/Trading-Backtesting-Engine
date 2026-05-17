import mysql.connector
from mysql.connector import Error

def save_trades(signals, user_id, asset_id, strategy_id, quantity, conn):
    cursor = conn.cursor()
    try:
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
        print(f"[+] {len(signals)} trades saved.")
    except Exception as e:
        conn.rollback()
        print(f"[!] Failed to save trades: {e}")
    finally:
        cursor.close()