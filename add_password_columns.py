from api.database import get_db_connection

def add_password_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT TRUE;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP;")
        conn.commit()
        print("SUCCESS: Password columns added to tenants table!")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_password_columns()