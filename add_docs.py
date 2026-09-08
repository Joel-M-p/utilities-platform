import psycopg2

conn = psycopg2.connect(
    dbname="utilities_platform",
    user="postgres",
    password="5432",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

# Create documents table without destroying existing tenant data!
cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        tenant_id INT NOT NULL REFERENCES tenants(id),
        doc_type VARCHAR(50) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Ensure the 'uploads' folder exists on your computer
import os
if not os.path.exists('uploads'):
    os.makedirs('uploads')

print("SUCCESS: Documents table created and 'uploads' folder is ready.")
cursor.close()
conn.close()