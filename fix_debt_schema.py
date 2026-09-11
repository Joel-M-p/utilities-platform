import psycopg2

def fix_schema():
    print("Connecting to database...")
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
        
        print("Adding credit_debt column to wallets...")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_debt DECIMAL DEFAULT 0;")
        
        # Initialize debt to 0 for existing wallets
        cursor.execute("UPDATE wallets SET credit_debt = 0 WHERE credit_debt IS NULL;")
        
        print("\n✅ Success! 'credit_debt' column added/verified.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()