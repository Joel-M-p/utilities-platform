from api.database import get_db_connection

def add_meter_balance():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print("Adding 'meter_balance' column to meters table...")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS meter_balance DECIMAL DEFAULT 0;")
        conn.commit()
        print("Success! 'meter_balance' column added.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_meter_balance()