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

# Add suspended_at and vacated_at columns without deleting existing data
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS vacated_at TIMESTAMP")

print("SUCCESS: 'suspended_at' and 'vacated_at' date columns added to tenants table.")
cursor.close()
conn.close()