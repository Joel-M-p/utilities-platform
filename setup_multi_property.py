from api.database import get_db_connection

def setup_properties():
    print("Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create the Properties table
        print("Creating 'properties' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                province VARCHAR(100) NOT NULL,
                address TEXT
            );
        """)

        # 2. Insert the 4 properties (if they don't exist)
        print("Adding 4 sample properties...")
        properties = [
            ("Sandton Sky Complex", "Gauteng", "123 Main Rd, Sandton"),
            ("Cape Bay Apartments", "Western Cape", "45 Beach Rd, Cape Town"),
            ("Durban Sands Estate", "KwaZulu-Natal", "78 Marine Pde, Durban"),
            ("PE Industrial Park", "Eastern Cape", "12 Govan Mbeki Ave, PE")
        ]
        
        for p in properties:
            cursor.execute("INSERT INTO properties (name, province, address) SELECT %s, %s, %s WHERE NOT EXISTS (SELECT 1 FROM properties WHERE name = %s)", (p[0], p[1], p[2], p[0]))

        # 3. Add property_id column to tenants and meters (if missing)
        print("Linking tenants and meters to properties...")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id);")

        # 4. Auto-assign existing tenants to Property 1 (just so no one is left unassigned)
        cursor.execute("UPDATE tenants SET property_id = 1 WHERE property_id IS NULL;")
        cursor.execute("UPDATE meters SET property_id = 1 WHERE property_id IS NULL;")

        conn.commit()
        print("\nSuccess! Multi-property schema created.")
        print(" - 4 Properties added (Gauteng, WC, KZN, EC).")
        print(" - Existing tenants assigned to Property 1.")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_properties()