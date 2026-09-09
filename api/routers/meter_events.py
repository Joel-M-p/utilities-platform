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
        # 1. Fetch meter and verify ownership
        cursor.execute("SELECT tenant_id, property_id FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        
        tenant_id, property_id = meter_data
        enforce_property_access(current_user, property_id)

        event_type = payload.get("event_type", "GENERAL_EVENT").upper()
        event_notes = payload.get("event_notes", "")
        
        # --- NEW: Fetch username from DB using user_id in token ---
        user_id = current_user.get("user_id")
        recorded_by = "Unknown PM"
        if user_id is not None:
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                recorded_by = user_data[0]

        # 2. Insert the event
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
        # 1. Verify ownership of the meter
        cursor.execute("SELECT property_id FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        enforce_property_access(current_user, meter_data[0])

        # 2. Fetch all transactions linked to this meter
        cursor.execute("""
            SELECT t.created_at, t.amount, t.transaction_type, t.reference, t.status
            FROM transactions t
            WHERE t.meter_id = %s
            ORDER BY t.created_at DESC
            LIMIT 50
        """, (meter_id,))
        txns = cursor.fetchall()
        
        history = []
        for row in txns:
            history.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "type": row[2],
                "details": row[3],
                "amount": float(row[1]),
                "category": "TRANSACTION",
                "status": row[4] or "COMPLETED"
            })

        # 3. Fetch all events (tamper/bypass) linked to this meter
        cursor.execute("""
            SELECT e.created_at, e.event_type, e.event_notes, e.recorded_by
            FROM meter_events e
            WHERE e.meter_id = %s
            ORDER BY e.created_at DESC
            LIMIT 50
        """, (meter_id,))
        events = cursor.fetchall()

        for row in events:
            history.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "type": row[1],
                "details": f"{row[2]} (Logged by: {row[3]})",
                "amount": 0.0,
                "category": "EVENT",
                "status": "LOGGED"
            })

        # 4. Sort combined history by date descending
        history.sort(key=lambda x: x["date"], reverse=True)

        return {"status": "success", "history": history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()