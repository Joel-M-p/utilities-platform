from api.database import get_db_connection

def add_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings (
                id SERIAL PRIMARY KEY,
                meter_id INTEGER,
                tenant_id INTEGER,
                property_id INTEGER,
                meter_type VARCHAR(50),
                serial_number VARCHAR(255),
                reading_value DECIMAL,
                previous_reading DECIMAL DEFAULT 0,
                consumption DECIMAL,
                rate DECIMAL,
                amount DECIMAL,
                reading_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recorded_by VARCHAR(50)
            );
        """)
        conn.commit()
        print("SUCCESS: meter_readings table created!")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_table()