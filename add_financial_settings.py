import psycopg2
import os

db_url = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(db_url, sslmode='require') if db_url else psycopg2.connect(dbname="utilities_platform", user="postgres", password="5432", host="localhost", port="5432")
conn.autocommit = True
cursor = conn.cursor()

# Add financial settings columns to the company table
cursor.execute("ALTER TABLE company ADD COLUMN IF NOT EXISTS vat_rate DECIMAL(5,2) DEFAULT 15.00")
cursor.execute("ALTER TABLE company ADD COLUMN IF NOT EXISTS mgmt_fee_pct DECIMAL(5,2) DEFAULT 10.00")
cursor.execute("ALTER TABLE company ADD COLUMN IF NOT EXISTS arrears_fee DECIMAL(10,2) DEFAULT 95.00")
cursor.execute("ALTER TABLE company ADD COLUMN IF NOT EXISTS shortcode_fee DECIMAL(10,2) DEFAULT 250.00")

print("SUCCESS: Financial settings (VAT, Management Fees) added to company table.")
cursor.close()
conn.close()