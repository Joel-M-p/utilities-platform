import os
import psycopg2

def fix_schema():
    print("Connecting to database...")
    db_url = os.getenv("postgresql://neondb_owner:npg_uoBzf2j4TDCF@ep-shy-star-ayefo4p7-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    
    try:
        if db_url:
            print("Found DATABASE_URL. Connecting to CLOUD (Render) database...")
            if "?sslmode=" not in db_url:
                db_url += "?sslmode=require"
            conn = psycopg2.connect(db_url)
        else:
            print("No DATABASE_URL found. Connecting to LOCAL database...")
            conn = psycopg2.connect(
                dbname="utilities_platform",
                user="postgres",
                password="5432",
                host="localhost",
                port="5432"
            )
            
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
        
        print("\n✅ Success! All missing columns (including cellphone) have been added.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()