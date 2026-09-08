import psycopg2

conn = psycopg2.connect(
    dbname="utilities_platform",
    user="postgres",
    password="5432",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

# Add POPIA consent and anonymization columns
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS popia_consent BOOLEAN DEFAULT FALSE")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_anonymized BOOLEAN DEFAULT FALSE")

print("SUCCESS: POPIA compliance columns added to tenants table.")
cursor.close()
conn.close()