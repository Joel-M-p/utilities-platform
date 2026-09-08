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

cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_limit DECIMAL(10, 2) DEFAULT 0.00")

print("SUCCESS: 'credit_limit' column added to wallets.")
cursor.close()
conn.close()