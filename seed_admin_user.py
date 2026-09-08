"""
Creates the 'users' table (missing from this backup's database.py) and
seeds one admin account, hashed exactly the way api/routers/auth.py checks
it: hashlib.sha256(password).hexdigest() against a plain 'password' column.

Run from the same folder as utilities_platform.db:

    python seed_admin_user.py

Change ADMIN_USERNAME / ADMIN_PASSWORD below before running if you want
different credentials. Safe to run more than once - it won't duplicate the
user if one with the same username already exists.
"""
import sqlite3
import hashlib

DB_PATH = "utilities_platform.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "ADMIN"


def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'PM_USER',
            property_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("Ensured 'users' table exists.")

    cursor.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,))
    existing = cursor.fetchone()
    if existing:
        print(f"User '{ADMIN_USERNAME}' already exists (id={existing[0]}) - not creating a duplicate.")
    else:
        password_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, role, property_id) VALUES (?, ?, ?, ?)",
            (ADMIN_USERNAME, password_hash, ADMIN_ROLE, None)
        )
        conn.commit()
        print(f"Created user '{ADMIN_USERNAME}' with role '{ADMIN_ROLE}'.")
        print(f"Login with username='{ADMIN_USERNAME}', password='{ADMIN_PASSWORD}'")

    conn.close()


if __name__ == "__main__":
    seed()