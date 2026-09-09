import psycopg2

def fix_cloud_schema():
    # PASTE YOUR RENDER DATABASE URL HERE:
    # You can find this on Render -> Your Web Service -> Environment -> DATABASE_URL
    db_url = "postgresql://neondb_owner:npg_uoBzf2j4TDCF@ep-shy-star-ayefo4p7-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    print("Connecting to Render cloud database...")
    
    try:
        # Cloud databases require SSL
        conn = psycopg2.connect(db_url, sslmode='require')
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding missing financial columns to transactions table...")
        
        # Add the missing columns one by one
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100);")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS before_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS after_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        
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
        
        print("\n✅ Success! The missing columns have been added to your Render database.")
        print("You can now top up wallets on your live app without errors!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_cloud_schema()