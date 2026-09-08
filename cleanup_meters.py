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

# This deletes ALL meters for Tenant 1 so we can start fresh!
cursor.execute("DELETE FROM meters WHERE tenant_id = 1;")
print("SUCCESS: All meters for Sarah Connor have been deleted.")

cursor.close()
conn.close()