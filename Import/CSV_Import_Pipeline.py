import pandas as pd
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

# ─────────────────────────────────────────
# 1. DATABASE CONNECTION
# ─────────────────────────────────────────
def get_connection():
    return mysql.connector.connect(
        **DB_CONFIG
    )

# ─────────────────────────────────────────
# 2. GET OR CREATE ASSET
#    - If symbol exists → return its asset_id
#    - If not → insert it and return new asset_id
# ─────────────────────────────────────────
def get_or_create_asset(cursor, symbol, name, asset_type):
    # Your exact query — check if asset exists
    cursor.execute(
        "SELECT asset_id FROM assets WHERE symbol = %s",
        (symbol,)
    )
    row = cursor.fetchone()

    if row:
        print(f"[+] Asset '{symbol}' already exists. asset_id = {row[0]}")
        return row[0]
    else:
        # Asset doesn't exist — insert it
        cursor.execute(
            """
            INSERT INTO assets (symbol, name, asset_type)
            VALUES (%s, %s, %s)
            """,
            (symbol, name, asset_type)
        )
        print(f"[+] Asset '{symbol}' created. asset_id = {cursor.lastrowid}")
        return cursor.lastrowid

# ─────────────────────────────────────────
# 3. VALIDATE CSV
#    - Check that all required columns exist
#    - Check for nulls in critical columns
# ─────────────────────────────────────────
def validate_csv(df):
    required_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    # Check for nulls in critical columns
    if df[list(required_columns)].isnull().any().any():
        raise ValueError("CSV contains NULL values in critical columns.")

    print(f"[+] CSV validated. {len(df)} rows found.")

# ─────────────────────────────────────────
# 4. IMPORT PRICES
#    - Uses INSERT IGNORE to skip duplicates
#    - Inserts in batches for performance
# ─────────────────────────────────────────
def import_prices(cursor, df, asset_id):
    # Convert timestamp column to proper datetime
    # df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Build list of row tuples for batch insert
    rows = [
        (
            asset_id,
            row['open'],
            row['high'],
            row['low'],
            row['close'],
            row['volume'],
            row['timestamp']
        )
        for _, row in df.iterrows()
    ]

    # INSERT IGNORE skips duplicate (asset_id + timestamp) rows silently
    insert_query = """
        INSERT IGNORE INTO historical_prices
            (asset_id, open, high, low, close, volume, timestamp)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """

    # executemany inserts all rows in one batch — much faster than one by one
    cursor.executemany(insert_query, rows)
    print(f"[+] {cursor.rowcount} rows inserted. Duplicates skipped automatically.")

# ─────────────────────────────────────────
# 5. MAIN FUNCTION
#    - Ties everything together
# ─────────────────────────────────────────
def import_csv(filepath, symbol, name, asset_type,date_from=None,date_to=None):
    try:
        # Read CSV
        df = pd.read_csv(filepath)

        # Convert FIRST, then filter
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Apply date filters if specified
        if date_from is not None:
            df = df[df['timestamp'] >= date_from]
        if date_to is not None:
            df = df[df['timestamp'] <= date_to]

        # Validate structure
        validate_csv(df)

        # Connect to DB
        conn = get_connection()
        cursor = conn.cursor()
    
        # Get or create the asset
        asset_id = get_or_create_asset(cursor, symbol, name, asset_type)

        # Import price rows
        import_prices(cursor, df, asset_id)

        # Commit transaction — nothing is saved until this line
        conn.commit()
        print("[+] Import complete. Transaction committed.")

    except ValueError as ve:
        print(f"[!] Validation Error: {ve}")

    except Error as e:
        print(f"[!] Database Error: {e}")
        conn.rollback()  # Undo everything if something went wrong
        print("[!] Transaction rolled back.")

    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────
# 6. RUN IT
# ─────────────────────────────────────────
if __name__ == "__main__":
    import_csv(
        filepath="AAPL_data.csv",
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock"
    )