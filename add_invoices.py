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
    CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY,
        tenant_id INT NOT NULL REFERENCES tenants(id),
        invoice_date DATE DEFAULT CURRENT_DATE,
        billing_period VARCHAR(20),
        total_amount DECIMAL(10, 2) DEFAULT 0.00,
        status VARCHAR(20) DEFAULT 'DUE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id SERIAL PRIMARY KEY,
        invoice_id INT NOT NULL REFERENCES invoices(id),
        description VARCHAR(255),
        quantity DECIMAL(10, 3),
        unit_price DECIMAL(10, 3),
        total DECIMAL(10, 2),
        drill_down TEXT
    )
""")

print("SUCCESS: Invoices and Invoice Items tables created.")
cursor.close()
conn.close()