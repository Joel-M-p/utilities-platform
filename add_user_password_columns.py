from api.database import get_db_connection

def add_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP;")
        cursor.execute("UPDATE users SET must_change_password = TRUE WHERE must_change_password IS NULL OR must_change_password = FALSE;")
        cursor.execute("UPDATE users SET email = 'admin@elups.co.za' WHERE username = 'admin' AND (email IS NULL OR email = '');")
        conn.commit()
        print("SUCCESS: User password columns added!")
        print("  - email column added")
        print("  - must_change_password column added (all users must change)")
        print("  - password_changed_at column added")
        print("  - Default admin email set to admin@elups.co.za")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_columns()