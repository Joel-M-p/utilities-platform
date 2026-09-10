import psycopg2

def fix_cloud_schema():
    # PASTE YOUR RENDER DATABASE URL HERE:
    db_url = "postgresql://neondb_owner:npg_uoBzf2j4TDCF@ep-shy-star-ayefo4p7-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    print("Connecting to Render cloud database...")
    
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding missing transaction columns...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'COMPLETED';")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meter_id INTEGER REFERENCES meters(id);")
        
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
        
        print("\n✅ Success! The missing table and columns have been added to your Render database.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_cloud_schema()