from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token

router = APIRouter()

@router.get("/audit-log/", dependencies=[Depends(verify_token)])
def get_audit_log():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- SELF-HEALING SCHEMA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(50),
                action VARCHAR(255),
                details TEXT
            );
        """)
        conn.commit()

        cursor.execute("SELECT id, timestamp, username, action, details FROM audit_log ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "timestamp": r[1].strftime("%Y-%m-%d %H:%M:%S"),
                "username": r[2],
                "action": r[3],
                "details": r[4]
            })
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/audit-log/", dependencies=[Depends(verify_token)])
def create_audit_log(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- SELF-HEALING SCHEMA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(50),
                action VARCHAR(255),
                details TEXT
            );
        """)
        conn.commit()

        username = payload.get("username", "Unknown")
        action = payload.get("action", "Unknown Action")
        details = payload.get("details", "")
        
        cursor.execute("""
            INSERT INTO audit_log (username, action, details) 
            VALUES (%s, %s, %s)
        """, (username, action, details))
        conn.commit()
        return {"status": "success", "message": "Audit log created."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()