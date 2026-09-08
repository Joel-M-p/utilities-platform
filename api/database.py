import psycopg2
import os

def get_db_connection():
    # This tells the app to use the Cloud Database URL if it exists. 
    # If you are running locally on your laptop, it will fall back to your local database.
    db_url = os.environ.get("DATABASE_URL")
    
    if db_url:
        # Cloud databases (like Neon/Render) require SSL for security
        conn = psycopg2.connect(db_url, sslmode='require')
    else:
        # Local laptop fallback
        conn = psycopg2.connect(
            dbname="utilities_platform",
            user="postgres",
            password="5432",
            host="localhost",
            port="5432"
        )
    
    # Ensure we use strict transactions (must call conn.commit() to save)
    conn.autocommit = False
    return conn