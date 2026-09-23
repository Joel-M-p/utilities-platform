from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from decimal import Decimal

router = APIRouter()

@router.get("/company-settings", dependencies=[Depends(verify_token)])
def get_company_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure column exists
        conn.commit()

        cursor.execute("SELECT name, logo_path, address, vat_number, contact_email, contact_phone, vat_percent FROM company WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            # Create default if missing
            cursor.execute("INSERT INTO company (id, name, vat_percent) VALUES (1, 'Default Company', 15.00) ON CONFLICT (id) DO NOTHING;")
            conn.commit()
            cursor.execute("SELECT name, logo_path, address, vat_number, contact_email, contact_phone, vat_percent FROM company WHERE id = 1")
            row = cursor.fetchone()

        return {
            "name": row[0], "logo_path": row[1], "address": row[2],
            "vat_number": row[3], "contact_email": row[4], "contact_phone": row[5],
            # Frontend expects 'vat_rate', not 'vat_percent'
            "vat_rate": float(row[6]) if row[6] is not None else 15.0 
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/company-settings", dependencies=[Depends(verify_token)])
def update_company_settings(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure column exists
        conn.commit()

        name = payload.get("name")
        logo_path = payload.get("logo_path")
        address = payload.get("address")
        vat_number = payload.get("vat_number")
        contact_email = payload.get("contact_email")
        contact_phone = payload.get("contact_phone")
        # Frontend sends 'vat_rate', map it to DB 'vat_percent'
        vat_rate = payload.get("vat_rate", 15.0)

        cursor.execute("""
            UPDATE company 
            SET name = %s, logo_path = %s, address = %s, vat_number = %s, contact_email = %s, contact_phone = %s, vat_percent = %s 
            WHERE id = 1
        """, (name, logo_path, address, vat_number, contact_email, contact_phone, vat_rate))
        
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO company (id, name, logo_path, address, vat_number, contact_email, contact_phone, vat_percent)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s)
            """, (name, logo_path, address, vat_number, contact_email, contact_phone, vat_rate))
        
        conn.commit()
        return {"status": "success", "message": "Company settings updated successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()