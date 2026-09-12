import psycopg2

def fix_cloud_schema():
    print("Please paste your exact Render DATABASE_URL and press Enter:")
    db_url = input()
    
    if not db_url:
        print("No URL entered. Exiting.")
        return

    print("\nConnecting to database...")
    
    try:
        # Ensure SSL is required for cloud databases
        if "?sslmode=" not in db_url:
            db_url += "?sslmode=require"
            
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding missing transaction columns...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100);")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS before_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS after_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meter_id INTEGER;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'COMPLETED';")
        
        print("Adding missing wallet columns (Emergency Fund)...")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_balance DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_debt DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_taps_used INT DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_reset_month VARCHAR(7);")
        
        print("Adding missing tenant columns (Cellphone)...")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS cellphone VARCHAR(20);")
        
        print("Creating missing meter_events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_events (
                id SERIAL PRIMARY KEY,
                meter_id INTEGER REFERENCES meters(id),
                tenant_id INTEGER REFERENCES tenants(id),
                property_id INTEGER REFERENCES properties(id),
                event_type VARCHAR(50),
                event_notes TEXT,
                recorded_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        print("\n✅ Success! The missing columns (including cellphone) have been added to your cloud database.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    fix_cloud_schema()