import psycopg2
import os

db_url = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(db_url, sslmode='require') if db_url else psycopg2.connect(dbname="utilities_platform", user="postgres", password="5432", host="localhost", port="5432")
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS property_name VARCHAR(100) DEFAULT 'Little Manhattan Gardens'")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS credit_note_reason TEXT")

print("SUCCESS: 'property_name' and 'credit_note_reason' columns added.")
cursor.close()
conn.close()