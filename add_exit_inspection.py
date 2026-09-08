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

# Add exit and inspection columns without deleting existing data
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS exit_date DATE")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS exit_reason TEXT")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS inspection_status VARCHAR(20) DEFAULT 'N/A'")
cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS inspection_notes TEXT")

print("SUCCESS: Exit form and inspection columns added to tenants table.")
cursor.close()
conn.close()