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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS recons (
        id SERIAL PRIMARY KEY,
        utility_type VARCHAR(20) NOT NULL,
        reading_month VARCHAR(7) NOT NULL, -- e.g., '2023-10'
        municipal_units DECIMAL(10, 3) NOT NULL,
        submeter_units DECIMAL(10, 3) NOT NULL,
        variance DECIMAL(10, 3) NOT NULL,
        status VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("SUCCESS: Reconciliation (recons) table created.")
cursor.close()
conn.close()