from api.database import get_db_connection

def add_hardware_type():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print("Adding 'hardware_type' column to meters table...")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS hardware_type VARCHAR(20) DEFAULT 'STS';")
        
        # Let's pretend Property 2, 3, and 4 use Smart Meters. 
        # We can update their meters to 'SMART_IOT'.
        # (Assuming property_id 1 is STS and 2,3,4 are Smart)
        cursor.execute("UPDATE meters SET hardware_type = 'SMART_IOT' WHERE property_id IN (2, 3, 4);")
        
        conn.commit()
        print("Success! Meters updated.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_hardware_type()