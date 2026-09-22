from api.database import get_db_connection
from api.services.passwords import hash_password, generate_temp_password

def set_temp_passwords():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, first_name, last_name, unit_number FROM tenants WHERE password_hash IS NULL OR password_hash = ''")
        tenants = cursor.fetchall()
        
        if not tenants:
            print("All tenants already have passwords set.")
            return
        
        print(f"Found {len(tenants)} tenant(s) without passwords:\n")
        
        for t in tenants:
            tenant_id = t[0]
            name = f"{t[1] or ''} {t[2] or ''}".strip()
            unit = t[3] or 'N/A'
            
            temp_pw = generate_temp_password()
            hashed = hash_password(temp_pw)
            
            cursor.execute(
                "UPDATE tenants SET password_hash = %s, must_change_password = TRUE WHERE id = %s",
                (hashed, tenant_id)
            )
            conn.commit()
            
            print(f"Tenant ID: {tenant_id}")
            print(f"  Name: {name}")
            print(f"  Unit: {unit}")
            print(f"  Temp Password: {temp_pw}")
            print(f"  (Must change on first login)")
            print()
        
        print("Done! Share these passwords with the tenants.")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    set_temp_passwords()