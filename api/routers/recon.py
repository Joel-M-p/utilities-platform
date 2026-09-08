from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.schemas import ReconRequest
from api.security import verify_token
from decimal import Decimal

router = APIRouter()

@router.post("/recon/", dependencies=[Depends(verify_token)])
def api_create_recon(recon: ReconRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        muni_units = Decimal(str(recon.municipal_units))
        sub_units = Decimal(str(recon.submeter_units))
        variance = muni_units - sub_units
        
        if abs(variance) <= (muni_units * Decimal('0.05')): # Allow 5% tolerance for rounding
            status = "BALANCED"
        elif variance > 0:
            status = "LOSS (Leak/Theft)"
        else:
            status = "GAIN (Meter Fault)"
            
        cursor.execute("""
            INSERT INTO recons (utility_type, reading_month, municipal_units, submeter_units, variance, status) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (recon.utility_type.upper(), recon.reading_month, muni_units, sub_units, variance, status))
        recon_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            "status": "success", 
            "message": "Reconciliation saved.",
            "recon_id": recon_id,
            "variance": float(variance),
            "result": status
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/recon/", dependencies=[Depends(verify_token)])
def api_get_recons():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, utility_type, reading_month, municipal_units, submeter_units, variance, status, created_at FROM recons ORDER BY created_at DESC")
        rows = cursor.fetchall()
        recons_list = []
        for row in rows:
            recons_list.append({
                "id": row[0], "utility_type": row[1], "month": row[2],
                "municipal_units": float(row[3]), "submeter_units": float(row[4]),
                "variance": float(row[5]), "status": row[6],
                "date": row[7].strftime("%Y-%m-%d %H:%M")
            })
        return {"status": "success", "recons": recons_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()