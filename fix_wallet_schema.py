import psycopg2

def fix_wallet_schema():
    print("Connecting to local database...")
    
    try:
        conn = psycopg2.connect(
            dbname="utilities_platform",
            user="postgres",
            password="5432",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding missing micro-credit columns to wallets table...")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_balance DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_taps_used INT DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_reset_month VARCHAR(7);")
        
        print("\n✅ Success! The micro-credit columns have been added to your local database.")
        print("You can now set credit limits and use the 3-tap wallet feature.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_wallet_schema()