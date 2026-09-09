import psycopg2

def fix_local_schema():
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
        
        print("Adding missing 'status' column to transactions...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'COMPLETED';")
        
        print("Adding missing 'meter_id' column to transactions...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meter_id INTEGER REFERENCES meters(id);")
        
        print("Creating missing 'meter_events' table...")
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
        
        print("Fixing email constraint on tenants table...")
        cursor.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_email_key;")
        cursor.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_email_unique;")
        cursor.execute("""
            DO $$             BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_property_email') THEN
                    ALTER TABLE tenants ADD CONSTRAINT uniq_property_email UNIQUE (property_id, email);
                END IF;
            END $$;
        """)
        
        print("\n✅ Success! The missing table and columns have been added to your local database.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_local_schema()