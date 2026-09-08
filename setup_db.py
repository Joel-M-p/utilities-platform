import psycopg2
from psycopg2 import sql

# Connect to the default 'postgres' database to create our new one
try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="5432",  # Using the password you set during installation
        host="localhost",
        port="5432"
    )
    conn.autocommit = True  # Required for creating a new database
    cursor = conn.cursor()

    # Check if our database already exists, if not, create it
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'utilities_platform'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(sql.SQL("CREATE DATABASE utilities_platform"))
        print("SUCCESS: Database 'utilities_platform' created!")
    else:
        print("SUCCESS: Database 'utilities_platform' already exists!")

    cursor.close()
    conn.close()

except Exception as e:
    print("ERROR:", e)