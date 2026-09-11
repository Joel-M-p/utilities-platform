import psycopg2

def fix_meters():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(
            dbname="utilities_platform",
            user="postgres",
            password="5432",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Enter the OLD Tenant ID here (the one that was vacated)
        old_tenant_id = input("Enter the OLD Tenant ID that is stuck on the meter: ")
        
        print(f"Forcefully freeing all meters from Tenant ID {old_tenant_id}...")
        # This sets tenant_id to NULL and is_active to FALSE for ALL meters linked to that tenant
        cursor.execute("UPDATE meters SET tenant_id = NULL, is_active = FALSE WHERE tenant_id = %s", (old_tenant_id,))
        
        print("\n✅ Success! All meters have been freed. You can now assign them to the new tenant.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_meters()