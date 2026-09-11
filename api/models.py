import hashlib
from api.database import get_db_connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- PREVENT RENDER MULTI-INSTANCE RACE CONDITIONS ---
        cursor.execute("SELECT pg_try_advisory_lock(123456789)")
        locked = cursor.fetchone()[0]
        
        if not locked:
            print("Database initialization already running on another instance. Skipping.")
            conn.commit()
            return

        # --- 1. PROPERTIES TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                province VARCHAR(100) NOT NULL,
                address TEXT,
                utility_model VARCHAR(20) DEFAULT 'STS_TOKEN'
            );
        """)

        # --- 2. TENANTS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255),
                rent_outstanding DECIMAL DEFAULT 0,
                electricity_outstanding DECIMAL DEFAULT 0,
                water_outstanding DECIMAL DEFAULT 0,
                status VARCHAR(50) DEFAULT 'ACTIVE',
                property_id INTEGER REFERENCES properties(id)
            );
        """)

        # --- 3. WALLETS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER UNIQUE,
                balance DECIMAL DEFAULT 0,
                credit_limit DECIMAL DEFAULT 0
            );
        """)

        # --- 4. TRANSACTIONS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER,
                amount DECIMAL,
                transaction_type VARCHAR(50),
                reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # --- 5. TARIFFS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tariffs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                meter_type VARCHAR(50),
                property_id INTEGER REFERENCES properties(id)
            );
        """)

        # --- 6. METERS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER,
                meter_type VARCHAR(50),
                billing_type VARCHAR(50),
                serial_number VARCHAR(255),
                valve_status VARCHAR(50) DEFAULT 'OPEN',
                is_active BOOLEAN DEFAULT TRUE,
                tariff_id INTEGER,
                property_id INTEGER REFERENCES properties(id)
            );
        """)

        # --- 7. DOCUMENTS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER,
                doc_type VARCHAR(50),
                file_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # --- 8. COMPANY TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                logo_path TEXT,
                address TEXT,
                vat_number VARCHAR(50),
                contact_email VARCHAR(255),
                contact_phone VARCHAR(50)
            );
        """)
        cursor.execute("""
            INSERT INTO company (id, name) 
            VALUES (1, 'Elups Utilities') 
            ON CONFLICT (id) DO NOTHING;
        """)

        # --- 9. INVOICES TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER,
                billing_period VARCHAR(20),
                cycle_type VARCHAR(20),
                total DECIMAL DEFAULT 0,
                status VARCHAR(20) DEFAULT 'UNPAID',
                date DATE,
                period VARCHAR(20)
            );
        """)

        # --- 10. RECONCILIATION TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation (
                id SERIAL PRIMARY KEY,
                date DATE DEFAULT CURRENT_DATE,
                month VARCHAR(20),
                utility_type VARCHAR(50),
                municipal_units DECIMAL,
                submeter_units DECIMAL,
                variance DECIMAL,
                status VARCHAR(50)
            );
        """)

        # --- 11. USERS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'PM_USER',
                property_id INTEGER
            );
        """)
        admin_pass = hashlib.sha256("password123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (id, username, password, role, property_id) 
            VALUES (1, 'admin', %s, 'ADMIN', NULL) 
            ON CONFLICT (id) DO NOTHING;
        """, (admin_pass,))

        # --- 12. AUDIT LOG TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(50),
                action VARCHAR(255),
                details TEXT
            );
        """)

        # --- 13. METER EVENTS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_events (
                id SERIAL PRIMARY KEY,
                meter_id INTEGER REFERENCES meters(id),
                tenant_id INTEGER REFERENCES tenants(id),
                property_id INTEGER REFERENCES properties(id),
                event_type VARCHAR(50),
                event_notes TEXT,
                recorded_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # --- ADD/UPDATE MISSING COLUMNS FOR EXISTING TABLES ---
        cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS utility_model VARCHAR(20) DEFAULT 'STS_TOKEN';")
        cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS address TEXT;")
        
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS credit_status VARCHAR(20) DEFAULT 'PENDING';")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS credit_score INT DEFAULT 0;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS inspection_status VARCHAR(20) DEFAULT 'N/A';")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS popia_consent BOOLEAN DEFAULT FALSE;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_anonymized BOOLEAN DEFAULT FALSE;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS lease_expiry_date DATE;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS previous_emails TEXT;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS vacated_at TIMESTAMP;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS exit_date DATE;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS exit_reason TEXT;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS inspection_notes TEXT;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS unit_number VARCHAR(50);")

        # --- NEW: MICRO-CREDIT WALLET COLUMNS ---
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_balance DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_taps_used INT DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_reset_month VARCHAR(7);")

        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS hardware_type VARCHAR(20) DEFAULT 'STS';")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS meter_balance DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS tariff_id INTEGER;")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS valve_status VARCHAR(50) DEFAULT 'OPEN';")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")

        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS structure_type VARCHAR(50) DEFAULT 'FLAT';")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS rate_flat DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_2_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_peak_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_offpeak_rate DECIMAL DEFAULT 0;")

        cursor.execute("ALTER TABLE company ADD COLUMN IF NOT EXISTS vat_percent DECIMAL DEFAULT 15;")

        # --- WATERTIGHT FINANCIAL COLUMNS ---
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100) UNIQUE;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS before_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS after_balance DECIMAL;")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meter_id INTEGER REFERENCES meters(id);")
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'COMPLETED';")
        
        # COMMIT FINANCIAL COLUMNS FIRST SO THEY ARE NEVER ROLLED BACK
        conn.commit()

        # --- ENFORCE UNIQUE EMAIL PER PROPERTY ---
        cursor.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_email_key;")
        cursor.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_email_unique;")
        cursor.execute("""
            DO $$             BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_property_email') THEN
                    ALTER TABLE tenants ADD CONSTRAINT uniq_property_email UNIQUE (property_id, email);
                END IF;
            END $$;
        """)

        conn.commit()
        print("Database initialized and updated successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()