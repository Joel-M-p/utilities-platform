import os
import psycopg2
import hashlib
from decimal import Decimal
import sys

# Add the current directory to path so we can import api.models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.models import init_db

def reset_database():
    print("Connecting to LOCAL database to wipe data...")
    
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
        
        print("Dropping ALL existing tables for a clean slate...")
        # Drop tables in the correct order to avoid foreign key errors
        cursor.execute("""
            DROP TABLE IF EXISTS audit_log, transactions, documents, meters, wallets, tenants, tariffs, users, properties, invoices, reconciliation, meter_events, invoice_items CASCADE;
        """)
        
        cursor.close()
        conn.close()
        print("Tables dropped successfully.\n")
        
        print("Rebuilding fresh schema via init_db()...")
        # This will recreate all tables with the latest columns and constraints
        init_db()
        print("Schema rebuilt successfully.\n")
        
        print("Inserting fresh test data...")
        conn = psycopg2.connect(
            dbname="utilities_platform",
            user="postgres",
            password="5432",
            host="localhost",
            port="5432"
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 1. PROPERTIES
        cursor.execute("INSERT INTO properties (id, name, province, address, utility_model) VALUES (%s, %s, %s, %s, %s)", 
                       (1, 'Sunrise Gardens', 'Gauteng', '123 Main St', 'STS_TOKEN'))
        cursor.execute("INSERT INTO properties (id, name, province, address, utility_model) VALUES (%s, %s, %s, %s, %s)", 
                       (2, 'Moonlight Complex', 'Western Cape', '456 Beach Rd', 'STS_TOKEN'))
                       
        # 2. USERS (Admin + 2 Managers)
        admin_pass = hashlib.sha256("password123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (id, username, password, role, property_id) VALUES (%s, %s, %s, %s, %s)", 
                       (1, 'admin', admin_pass, 'ADMIN', None))
                       
        manager_pass = hashlib.sha256("manager123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (id, username, password, role, property_id) VALUES (%s, %s, %s, %s, %s)", 
                       (2, 'manager1', manager_pass, 'PM_USER', 1))
        cursor.execute("INSERT INTO users (id, username, password, role, property_id) VALUES (%s, %s, %s, %s, %s)", 
                       (3, 'manager2', manager_pass, 'PM_USER', 2))

        # 3. TARIFFS (1 Elec, 1 Water per property)
        cursor.execute("INSERT INTO tariffs (id, name, meter_type, property_id, structure_type, rate_flat) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (1, 'Sunrise Elec Flat', 'ELECTRICITY', 1, 'FLAT', 2.50))
        cursor.execute("INSERT INTO tariffs (id, name, meter_type, property_id, structure_type, rate_flat) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (2, 'Sunrise Water Flat', 'WATER_COLD', 1, 'FLAT', 15.00))
                       
        cursor.execute("INSERT INTO tariffs (id, name, meter_type, property_id, structure_type, rate_flat) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (3, 'Moonlight Elec Flat', 'ELECTRICITY', 2, 'FLAT', 3.00))
        cursor.execute("INSERT INTO tariffs (id, name, meter_type, property_id, structure_type, rate_flat) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (4, 'Moonlight Water Flat', 'WATER_COLD', 2, 'FLAT', 20.00))

        # 4. TENANTS & WALLETS (2 per property)
        # Property 1 Tenants
        cursor.execute("INSERT INTO tenants (id, first_name, last_name, email, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                       (1, 'John', 'Doe', 'john@test.com', Decimal('500.00'), Decimal('0'), Decimal('0'), 1, '101', 'ACTIVE'))
        cursor.execute("INSERT INTO wallets (tenant_id, balance, credit_limit) VALUES (%s, %s, %s)", (1, Decimal('1000.00'), Decimal('100.00')))

        cursor.execute("INSERT INTO tenants (id, first_name, last_name, email, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                       (2, 'Jane', 'Smith', 'jane@test.com', Decimal('0'), Decimal('0'), Decimal('0'), 1, '102', 'ACTIVE'))
        cursor.execute("INSERT INTO wallets (tenant_id, balance, credit_limit) VALUES (%s, %s, %s)", (2, Decimal('50.00'), Decimal('0')))

        # Property 2 Tenants
        cursor.execute("INSERT INTO tenants (id, first_name, last_name, email, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                       (3, 'Mike', 'Ross', 'mike@test.com', Decimal('1000.00'), Decimal('0'), Decimal('0'), 2, '201', 'ACTIVE'))
        cursor.execute("INSERT INTO wallets (tenant_id, balance, credit_limit) VALUES (%s, %s, %s)", (3, Decimal('500.00'), Decimal('0')))

        cursor.execute("INSERT INTO tenants (id, first_name, last_name, email, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                       (4, 'Rachel', 'Zane', 'rachel@test.com', Decimal('0'), Decimal('0'), Decimal('0'), 2, '202', 'ACTIVE'))
        cursor.execute("INSERT INTO wallets (tenant_id, balance, credit_limit) VALUES (%s, %s, %s)", (4, Decimal('0.00'), Decimal('0')))

        # 5. METERS (1 Elec, 1 Water per tenant)
        # John (Tenant 1)
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (1, 'ELECTRICITY', 'PREPAID', 'STS-ELEC-001', 1, 1, 'STS', 'OPEN', True))
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (1, 'WATER_COLD', 'PREPAID', 'IOT-WATER-001', 2, 1, 'SMART_IOT', 'OPEN', True))
                       
        # Jane (Tenant 2)
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (2, 'ELECTRICITY', 'PREPAID', 'STS-ELEC-002', 1, 1, 'STS', 'OPEN', True))
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (2, 'WATER_COLD', 'POSTPAID', 'IOT-WATER-002', 2, 1, 'SMART_IOT', 'OPEN', True))

        # Mike (Tenant 3)
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (3, 'ELECTRICITY', 'PREPAID', 'STS-ELEC-003', 3, 2, 'STS', 'OPEN', True))
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (3, 'WATER_COLD', 'PREPAID', 'IOT-WATER-003', 4, 2, 'SMART_IOT', 'OPEN', True))

        # Rachel (Tenant 4)
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (4, 'ELECTRICITY', 'PREPAID', 'STS-ELEC-004', 3, 2, 'STS', 'OPEN', True))
        cursor.execute("INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id, hardware_type, valve_status, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (4, 'WATER_COLD', 'POSTPAID', 'IOT-WATER-004', 4, 2, 'SMART_IOT', 'OPEN', True))

        conn.commit()
        print("\n✅ SUCCESS! Local database completely wiped and fresh test data created.")
        print("\n--- LOGIN CREDENTIALS ---")
        print("Admin: username='admin', password='password123'")
        print("Manager 1 (Sunrise): username='manager1', password='manager123'")
        print("Manager 2 (Moonlight): username='manager2', password='manager123'")
        print("\n--- TENANT PORTAL ---")
        print("Property 1 (Sunrise) -> Unit 101 -> Email: john@test.com")
        print("Property 2 (Moonlight) -> Unit 201 -> Email: mike@test.com")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reset_database()