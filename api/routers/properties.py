from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from decimal import Decimal

router = APIRouter()

# Public route for tenant login screen
@router.get("/public-properties/")
def get_public_properties():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- SELF-HEALING SCHEMA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                province VARCHAR(100) NOT NULL,
                address TEXT,
                utility_model VARCHAR(20) DEFAULT 'STS_TOKEN'
            );
        """)
        conn.commit()

        cursor.execute("SELECT id, name FROM properties ORDER BY name ASC")
        rows = cursor.fetchall()
        properties = [{"id": r[0], "name": r[1]} for r in rows]
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/properties/", dependencies=[Depends(verify_token)])
def get_properties():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.commit()

        cursor.execute("SELECT id, name, province, address, utility_model FROM properties ORDER BY id ASC")
        rows = cursor.fetchall()
        properties = []
        for r in rows:
            properties.append({
                "id": r[0], "name": r[1], "province": r[2], "address": r[3], 
                "utility_model": r[4] or "STS_TOKEN"
            })
        return {"properties": properties}
    except Exception as e:
        if "does not exist" in str(e):
            return {"properties": []}
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/properties/", dependencies=[Depends(verify_token)])
def create_property(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.commit()

        name = payload.get("name")
        province = payload.get("province")
        address = payload.get("address")
        utility_model = payload.get("utility_model", "STS_TOKEN").upper()
        
        if not name:
            raise HTTPException(status_code=400, detail="Property name is required")
            
        cursor.execute("""
            INSERT INTO properties (name, province, address, utility_model) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (name, province, address, utility_model))
        prop_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "message": "Property created successfully", "property_id": prop_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.put("/properties/{property_id}", dependencies=[Depends(verify_token)])
def update_property(property_id: int, payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.commit()

        name = payload.get("name")
        province = payload.get("province")
        address = payload.get("address")
        utility_model = payload.get("utility_model", "STS_TOKEN").upper()
        
        cursor.execute("""
            UPDATE properties 
            SET name = %s, province = %s, address = %s, utility_model = %s 
            WHERE id = %s
        """, (name, province, address, utility_model, property_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Property not found")
            
        conn.commit()
        return {"status": "success", "message": "Property updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()