import psycopg2

def get_db_connection():
    return psycopg2.connect(
        dbname="utilities_platform",
        user="postgres",
        password="5432",
        host="localhost",
        port="5432"
    )

conn = get_db_connection()
cursor = conn.cursor()

# This command deletes all old data AND resets the ID counter back to 1
cursor.execute("TRUNCATE TABLE transactions, wallets, tenants RESTART IDENTITY CASCADE;")

# Create a tenant who owes R1000 rent and R500 utilities
cursor.execute("""
    INSERT INTO tenants (first_name, last_name, rent_outstanding, utility_outstanding) 
    VALUES ('John', 'Doe', 1000.00, 500.00) RETURNING id
""")
tenant_id = cursor.fetchone()[0]

# Create their wallet
cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 0.00)", (tenant_id,))

conn.commit()
cursor.close()
conn.close()

print(f"SUCCESS: John Doe has been created! His Tenant ID is {tenant_id}.")
print("He owes R1000 for Rent and R500 for Utilities.")