from fastapi import APIRouter, HTTPException, Depends, Body
from api.database import get_db_connection
from api.security import verify_token
from api.services.notifications import send_notification
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from fastapi.responses import JSONResponse

router = APIRouter()

class CreditNoteRequest(BaseModel):
    tenant_id: int
    amount: float
    reason: str

# 1. Generate Credit Note
@router.post("/generate-credit-note/", dependencies=[Depends(verify_token)])
def api_generate_credit_note(req: CreditNoteRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (req.tenant_id,))
        tenant = cursor.fetchone()
        if not tenant: raise HTTPException(status_code=404, detail="Tenant not found")
        
        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (req.tenant_id,))
        wallet_id = cursor.fetchone()[0]
        
        # Add positive amount to wallet (Credit)
        amount = Decimal(str(req.amount))
        cursor.execute("UPDATE wallets SET balance = balance + %s WHERE id = %s", (amount, wallet_id))
        cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'CREDIT_NOTE', %s)", (wallet_id, amount, req.reason))
        
        note_no = f"CN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{req.tenant_id}"
        conn.commit()
        
        send_notification(f"{tenant[0]} {tenant[1]}", tenant[2], f"Credit Note {note_no} for R{amount:.2f} applied to your account. Reason: {req.reason}")
        return {"status": "success", "message": "Credit Note generated.", "note_no": note_no, "amount": float(amount)}
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close(); conn.close()

# 2. Property-Level Report
@router.get("/property-report/", dependencies=[Depends(verify_token)])
def api_property_report():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS property_name VARCHAR(100) DEFAULT 'Little Manhattan Gardens'")
        cursor.execute("""
            SELECT t.property_name, 
                   COUNT(t.id), 
                   COALESCE(SUM(t.rent_outstanding + t.electricity_outstanding + t.water_outstanding), 0),
                   COALESCE(SUM(w.balance), 0)
            FROM tenants t JOIN wallets w ON t.id = w.tenant_id
            GROUP BY t.property_name
        """)
        data = cursor.fetchall()
        properties = [{"name": r[0], "tenant_count": r[1], "total_arrears": float(r[2]), "wallet_balance": float(r[3])} for r in data]
        return {"status": "success", "properties": properties}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 3. Management Fee Invoice
@router.get("/management-fee-invoice/", dependencies=[Depends(verify_token)])
def api_management_fee_invoice():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 10% of all positive collections (payments)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE amount > 0 AND transaction_type IN ('WALLET_TOPUP', 'RENT_PAYMENT', 'UTILITY_PAYMENT')")
        total_collections = float(cursor.fetchone()[0])
        management_fee = total_collections * 0.10
        
        # Count arrears loads (adjustments)
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE transaction_type = 'ADJUSTMENT_RENT'")
        arrears_loads = cursor.fetchone()[0]
        arrears_fee = arrears_loads * 95.00
        
        short_code_fee = 250.00
        
        subtotal = management_fee + arrears_fee + short_code_fee
        vat = subtotal * 0.15
        total = subtotal + vat
        
        return {
            "status": "success",
            "total_collections": total_collections,
            "items": [
                {"desc": "Transaction fees (10% of collections)", "amount": management_fee},
                {"desc": f"Arrears/Rent Recovery Fee ({arrears_loads} loads @ R95)", "amount": arrears_fee},
                {"desc": "Monthly Short Code Enquiry Fee", "amount": short_code_fee}
            ],
            "subtotal": subtotal,
            "vat": vat,
            "total": total
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 4. Bank Reconciliation
@router.get("/bank-reconciliation/", dependencies=[Depends(verify_token)])
def api_bank_reconciliation():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE amount > 0")
        total_in = float(cursor.fetchone()[0])
        cursor.execute("SELECT COALESCE(SUM(ABS(amount)), 0) FROM transactions WHERE amount < 0")
        total_out = float(cursor.fetchone()[0])
        
        return {
            "status": "success",
            "total_collected": total_in,
            "total_disbursed": total_out,
            "net_balance": total_in - total_out
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 5. 3-Month Comparative Stats
@router.get("/three-month-stats/", dependencies=[Depends(verify_token)])
def api_three_month_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN transaction_type LIKE '%ELECTRICITY%' THEN ABS(amount) ELSE 0 END), 0) as elec,
                   COALESCE(SUM(CASE WHEN transaction_type LIKE '%WATER%' THEN ABS(amount) ELSE 0 END), 0) as water
            FROM transactions
            WHERE amount < 0 AND created_at > NOW() - INTERVAL '3 months'
            GROUP BY month ORDER BY month ASC
        """)
        data = cursor.fetchall()
        stats = [{"month": r[0], "elec": float(r[1]), "water": float(r[2])} for r in data]
        return {"status": "success", "stats": stats}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()