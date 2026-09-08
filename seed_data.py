import psycopg2
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Use cloud DB URL if available, otherwise use local
db_url = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(db_url, sslmode='require') if db_url else psycopg2.connect(
    dbname="utilities_platform", user="postgres", password="5432", host="localhost", port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

print("Clearing old data...")
cursor.execute("TRUNCATE TABLE transactions, meters, wallets, tenants, tariffs RESTART IDENTITY CASCADE;")

print("Creating Tariffs...")
cursor.execute("INSERT INTO tariffs (name, meter_type, structure_type, rate_flat) VALUES ('Standard Electricity', 'ELECTRICITY', 'FLAT', 2.50)")
cursor.execute("INSERT INTO tariffs (name, meter_type, structure_type, rate_flat) VALUES ('Standard Water', 'WATER_COLD', 'FLAT', 15.00)")

print("Creating Tenants & Wallets...")
# 1. James Bond - Active, has arrears and wallet credit
cursor.execute("INSERT INTO tenants (first_name, last_name, email, status, rent_outstanding, electricity_outstanding, water_outstanding) VALUES ('James', 'Bond', 'james@example.com', 'ACTIVE', 5000.00, 500.00, 200.00) RETURNING id")
tenant1_id = cursor.fetchone()[0]
cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 150.00)", (tenant1_id,))

# 2. Sarah Connor - Active, no arrears, zero balance
cursor.execute("INSERT INTO tenants (first_name, last_name, email, status, rent_outstanding, electricity_outstanding, water_outstanding) VALUES ('Sarah', 'Connor', 'sarah@example.com', 'ACTIVE', 0.00, 0.00, 0.00) RETURNING id")
tenant2_id = cursor.fetchone()[0]
cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 0.00)", (tenant2_id,))

# 3. John Doe - Suspended, high arrears, negative wallet
cursor.execute("INSERT INTO tenants (first_name, last_name, email, status, rent_outstanding, electricity_outstanding, water_outstanding) VALUES ('John', 'Doe', 'john@example.com', 'SUSPENDED', 12000.00, 3000.00, 1500.00) RETURNING id")
tenant3_id = cursor.fetchone()[0]
cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, -50.00)", (tenant3_id,))

# 4. Bruce Wayne - Active, no arrears, high wallet balance
cursor.execute("INSERT INTO tenants (first_name, last_name, email, status, rent_outstanding, electricity_outstanding, water_outstanding) VALUES ('Bruce', 'Wayne', 'bruce@example.com', 'ACTIVE', 0.00, 0.00, 0.00) RETURNING id")
tenant4_id = cursor.fetchone()[0]
cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 5000.00)", (tenant4_id,))

print("Assigning Meters...")
# James Bond: Prepaid Elec, Postpaid Water
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'ELECTRICITY', 'PREPAID', 'ELEC-001', 1, 'OPEN')", (tenant1_id,))
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'WATER_COLD', 'POSTPAID', 'WATER-001', 2, 'OPEN')", (tenant1_id,))

# Sarah Connor: Prepaid Elec, Prepaid Water
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'ELECTRICITY', 'PREPAID', 'ELEC-002', 1, 'OPEN')", (tenant2_id,))
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'WATER_COLD', 'PREPAID', 'WATER-002', 2, 'OPEN')", (tenant2_id,))

# John Doe: Postpaid Elec (Disconnected), Postpaid Water (Trickled)
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'ELECTRICITY', 'POSTPAID', 'ELEC-003', 1, 'DISCONNECTED')", (tenant3_id,))
cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, valve_status) VALUES (%s, 'WATER_COLD', 'POSTPAID', 'WATER-003', 2, 'TRICKLE')", (tenant3_id,))

print("Creating Historical Transactions (Bills & Payments)...")
# James Bond: Paid R5000 last month, used R500 elec & R200 water this month
cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant1_id,))
w1 = cursor.fetchone()[0]
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, 5000.00, 'WALLET_TOPUP', 'Bank EFT', %s)", (w1, datetime.now() - timedelta(days=30)))
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, -500.00, 'ELECTRICITY_BILL', 'Meter Read', %s)", (w1, datetime.now() - timedelta(days=15)))
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, -200.00, 'WATER_BILL', 'Meter Read', %s)", (w1, datetime.now() - timedelta(days=15)))

# Sarah Connor: Paid R1000, no usage yet
cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant2_id,))
w2 = cursor.fetchone()[0]
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, 1000.00, 'WALLET_TOPUP', 'Card Payment', %s)", (w2, datetime.now() - timedelta(days=10)))

# John Doe: Owes massive amounts, paid R1000 60 days ago
cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant3_id,))
w3 = cursor.fetchone()[0]
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, 1000.00, 'WALLET_TOPUP', 'Cash', %s)", (w3, datetime.now() - timedelta(days=60)))
cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at) VALUES (%s, -3000.00, 'ELECTRICITY_BILL', 'Meter Read', %s)", (w3, datetime.now() - timedelta(days=45)))

print("\nSUCCESS: Test data created successfully!")
print(f"Created 4 tenants, 4 wallets, 6 meters, and historical transactions.")
print("You can now log into your Mobile App and test all widgets.")

cursor.close()
conn.close()