from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token, enforce_property_access
import datetime

router = APIRouter()

@router.post("/log-meter-event/{meter_id}")
def api_log_meter_event(meter_id: int, payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT tenant_id, property_id FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        
        tenant_id, property_id = meter_data
        enforce_property_access(current_user, property_id)

        event_type = payload.get("event_type", "GENERAL_EVENT").upper()
        event_notes = payload.get("event_notes", "")
        recorded_by = current_user.get("username", "Unknown PM")

        cursor.execute("""
            INSERT INTO meter_events (meter_id, tenant_id, property_id, event_type, event_notes, recorded_by) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (meter_id, tenant_id, property_id, event_type, event_notes, recorded_by))
        event_id = cursor.fetchone()[0]
        conn.commit()

        return {"status": "success", "message": "Meter event logged successfully.", "event_id": event_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/meter-audit-history/{meter_id}")
def api_get_meter_history(meter_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTOMATIC SCHEMA FIX ---
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meter_id INTEGER;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_events (
                id SERIAL PRIMARY KEY,
                meter_id INTEGER REFERENCES meters(id),
                tenant_id INTEGER REFERENCES tenants(id),
                property_id INTEGER REFERENCES properties(id),
                event_type VARCHAR(50),
                event_notes TEXT,
                recorded_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        # 1. Verify ownership of the meter and get details
        cursor.execute("SELECT property_id, serial_number, meter_type FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        
        enforce_property_access(current_user, meter_data[0])
        serial_number = meter_data[1]
        meter_type = meter_data[2]

        # 2. Fetch all transactions linked to this meter, JOINING with tenants to get the name
        cursor.execute("""
            SELECT t.created_at, t.amount, t.transaction_type, t.reference, t.status, tn.first_name, tn.last_name
            FROM transactions t
            JOIN wallets w ON t.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
            WHERE t.meter_id = %s
            ORDER BY t.created_at DESC
            LIMIT 100
        """, (meter_id,))
        txns = cursor.fetchall()
        
        history = []
        for row in txns:
            tenant_name = f"{row[5]} {row[6]}" if row[5] else "Unknown"
            history.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "type": row[2],
                "details": row[3],
                "amount": float(row[1]),
                "category": "TRANSACTION",
                "status": row[4] or "COMPLETED",
                "tenant": tenant_name
            })

        # 3. Fetch all events (tamper/bypass) linked to this meter, JOINING with tenants
        cursor.execute("""
            SELECT e.created_at, e.event_type, e.event_notes, e.recorded_by, tn.first_name, tn.last_name
            FROM meter_events e
            LEFT JOIN tenants tn ON e.tenant_id = tn.id
            WHERE e.meter_id = %s
            ORDER BY e.created_at DESC
            LIMIT 100
        """, (meter_id,))
        events = cursor.fetchall()

        for row in events:
            tenant_name = f"{row[4]} {row[5]}" if row[4] else "Vacant/Unknown"
            history.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "type": row[1],
                "details": f"{row[2]} (Logged by: {row[3]})",
                "amount": 0.0,
                "category": "EVENT",
                "status": "LOGGED",
                "tenant": tenant_name
            })

        # 4. Sort combined history by date descending
        history.sort(key=lambda x: x["date"], reverse=True)

        return {
            "status": "success", 
            "meter_id": meter_id,
            "serial_number": serial_number,
            "meter_type": meter_type,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()