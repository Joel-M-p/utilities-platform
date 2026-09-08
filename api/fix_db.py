import os
import psycopg2

def fix_schema():
    print("Connecting to the EXACT SAME database as your FastAPI app...")
    
    # This is the exact same logic from your api/database.py file
    db_url = os.environ.get("DATABASE_URL")
    
    try:
        if db_url:
            print("Found DATABASE_URL. Connecting to your CLOUD database...")
            if "?sslmode=" not in db_url:
                db_url += "?sslmode=require"
            conn = psycopg2.connect(db_url)
        else:
            print("No DATABASE_URL found. Connecting to your LOCAL database...")
            conn = psycopg2.connect(
                dbname="utilities_platform",
                user="postgres",
                password="5432",
                host="localhost",
                port="5432"
            )
            
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding missing columns...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100) UNIQUE;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS before_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS after_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        
        print("\nSuccess! All missing columns have been added to the active database.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()