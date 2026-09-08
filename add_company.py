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
    CREATE TABLE IF NOT EXISTS company (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        logo_path VARCHAR(255),
        address TEXT,
        vat_number VARCHAR(50),
        contact_email VARCHAR(100),
        contact_phone VARCHAR(20)
    )
""")

# Insert default data if the table is empty
cursor.execute("SELECT COUNT(*) FROM company")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO company (name, logo_path, address, vat_number, contact_email, contact_phone) 
        VALUES ('My Property Company', '/static/logo.png', '123 Main Street, Johannesburg, RSA', 'VAT4123456789', 'info@mycompany.co.za', '0111234567')
    """)

print("SUCCESS: Company settings table created and populated.")
cursor.close()
conn.close()