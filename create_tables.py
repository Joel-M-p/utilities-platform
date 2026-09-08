import psycopg2

# Connect to the NEW 'utilities_platform' database we just created
try:
    conn = psycopg2.connect(
        dbname="utilities_platform",
        user="postgres",
        password="5432",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 1. Create the Tenants Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            phone_number VARCHAR(20),
            status VARCHAR(20) DEFAULT 'active',
            rent_outstanding DECIMAL(10, 2) DEFAULT 0.00,
            utility_outstanding DECIMAL(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Create the Wallets Table (Connects to Tenants)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL REFERENCES tenants(id),
            balance DECIMAL(10, 2) DEFAULT 0.00,
            credit_limit DECIMAL(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Create the Transactions Ledger Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            wallet_id INT NOT NULL REFERENCES wallets(id),
            amount DECIMAL(10, 2) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            reference VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("SUCCESS: Tables (tenants, wallets, transactions) created successfully!")

    cursor.close()
    conn.close()

except Exception as e:
    print("ERROR:", e)