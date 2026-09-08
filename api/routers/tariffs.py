from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token, enforce_property_access
from decimal import Decimal

router = APIRouter()

@router.get("/tariffs/")
def api_get_tariffs(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTOMATIC SCHEMA FIX ---
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS structure_type VARCHAR(50) DEFAULT 'FLAT';")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS rate_flat DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_2_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_peak_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_offpeak_rate DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        conn.commit()

        user_role = current_user.get("role")
        user_prop_id = current_user.get("property_id")

        # Determine target property ID
        target_property_id = None
        if user_role == "ADMIN":
            if property_id:  # Admin selected a specific property on the frontend
                target_property_id = property_id
        else:
            # Managers are strictly locked to their own property
            target_property_id = user_prop_id

        if target_property_id:
            # --- AUTOMATIC DATA FIX ---
            # If you have old tariffs with no property assigned (NULL), this will 
            # automatically assign them to the property you are currently looking at.
            cursor.execute("UPDATE tariffs SET property_id = %s WHERE property_id IS NULL", (target_property_id,))
            conn.commit()

            cursor.execute("""
                SELECT id, name, meter_type, structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate 
                FROM tariffs 
                WHERE property_id = %s
                ORDER BY id ASC
            """, (target_property_id,))
        else:
            # Admin viewing all properties
            cursor.execute("""
                SELECT id, name, meter_type, structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate 
                FROM tariffs 
                ORDER BY id ASC
            """)

        rows = cursor.fetchall()
        tariffs = []
        for r in rows:
            tariffs.append({
                "tariff_id": r[0], "name": r[1], "meter_type": r[2], "structure_type": r[3],
                "rate_flat": float(r[4] or 0), "tier_1_limit": float(r[5] or 0), "tier_1_rate": float(r[6] or 0),
                "tier_2_rate": float(r[7] or 0), "tou_peak_rate": float(r[8] or 0), "tou_offpeak_rate": float(r[9] or 0)
            })
        return {"tariffs": tariffs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/tariffs/")
def api_create_tariff(payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTOMATIC SCHEMA FIX ---
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        conn.commit()

        name = payload.get("name")
        meter_type = payload.get("meter_type")
        structure_type = payload.get("structure_type", "FLAT")
        rate_flat = payload.get("rate_flat", 0)
        tier_1_limit = payload.get("tier_1_limit", 0)
        tier_1_rate = payload.get("tier_1_rate", 0)
        tier_2_rate = payload.get("tier_2_rate", 0)
        tou_peak_rate = payload.get("tou_peak_rate", 0)
        tou_offpeak_rate = payload.get("tou_offpeak_rate", 0)
        
        # SECURITY: Determine property_id safely
        user_role = current_user.get("role")
        if user_role == "ADMIN":
            property_id = payload.get("property_id")
        else:
            # Managers can only create tariffs for their own property
            property_id = current_user.get("property_id")
            
        if not property_id:
            raise HTTPException(status_code=400, detail="A property_id must be assigned to this tariff.")
        
        # --- PREVENT DUPLICATE TARIFFS PER UTILITY PER PROPERTY ---
        cursor.execute("""
            SELECT id FROM tariffs 
            WHERE property_id = %s AND meter_type = %s
        """, (property_id, meter_type))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"A {meter_type} tariff already exists for this property. Please update the existing one instead of creating a new one.")

        cursor.execute("""
            INSERT INTO tariffs (name, meter_type, structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate, property_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (name, meter_type, structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate, property_id))
        tariff_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "message": "Tariff created successfully", "tariff_id": tariff_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.put("/tariffs/{tariff_id}")
def api_update_tariff(tariff_id: int, payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Fetch the tariff to ensure it exists and check authorization
        cursor.execute("SELECT property_id, meter_type FROM tariffs WHERE id = %s", (tariff_id,))
        tariff_data = cursor.fetchone()
        if not tariff_data:
            raise HTTPException(status_code=404, detail="Tariff not found.")
            
        tariff_property_id, original_meter_type = tariff_data
        
        # SECURITY: Admins can edit any tariff. Managers can only edit their own.
        enforce_property_access(current_user, tariff_property_id)

        # Extract updated fields from payload
        name = payload.get("name")
        meter_type = payload.get("meter_type", original_meter_type)
        structure_type = payload.get("structure_type", "FLAT")
        rate_flat = payload.get("rate_flat", 0)
        tier_1_limit = payload.get("tier_1_limit", 0)
        tier_1_rate = payload.get("tier_1_rate", 0)
        tier_2_rate = payload.get("tier_2_rate", 0)
        tou_peak_rate = payload.get("tou_peak_rate", 0)
        tou_offpeak_rate = payload.get("tou_offpeak_rate", 0)

        # --- PREVENT DUPLICATE TARIFFS IF METER TYPE IS CHANGED ---
        if meter_type != original_meter_type:
            cursor.execute("""
                SELECT id FROM tariffs 
                WHERE property_id = %s AND meter_type = %s AND id != %s
            """, (tariff_property_id, meter_type, tariff_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"A {meter_type} tariff already exists for this property. Cannot change meter type.")

        # 2. Execute the update
        cursor.execute("""
            UPDATE tariffs 
            SET name = %s, meter_type = %s, structure_type = %s, rate_flat = %s, 
                tier_1_limit = %s, tier_1_rate = %s, tier_2_rate = %s, 
                tou_peak_rate = %s, tou_offpeak_rate = %s
            WHERE id = %s
        """, (name, meter_type, structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate, tariff_id))
        
        conn.commit()
        return {"status": "success", "message": f"Tariff {tariff_id} updated successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()