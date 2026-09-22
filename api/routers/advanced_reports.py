from fastapi import APIRouter, HTTPException, Depends, Body
from api.database import get_db_connection
from api.security import verify_token, require_staff, resolve_property_scope
from api.routers.tenants import check_tenant_access
from api.services.notifications import send_notification
from api.services.tx_classification import MONEY_IN_SQL, MONEY_OUT_SQL
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse

router = APIRouter()

class CreditNoteRequest(BaseModel):
    tenant_id: int
    amount: float
    reason: str

# 1. Generate Credit Note
# SECURITY: this endpoint creates real money in a tenant's wallet, so it is staff-only
# (require_staff) and property-scoped (check_tenant_access). It previously accepted any
# valid token of any role and any tenant_id, letting a tenant credit their own wallet or a
# Manager credit a tenant at a property they don't manage.
@router.post("/generate-credit-note/")
def api_generate_credit_note(req: CreditNoteRequest, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, req.tenant_id, current_user)

        amount = Decimal(str(req.amount))
        # A "credit note" that subtracts from the wallet is really an unlogged debit; those
        # belong in /adjust-account/ where before/after balances are audited.
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Credit note amount must be greater than zero.")
        if not req.reason or not req.reason.strip():
            raise HTTPException(status_code=400, detail="A reason is required for a credit note.")

        cursor.execute("SELECT first_name, last_name, email, cellphone FROM tenants WHERE id = %s", (req.tenant_id,))
        tenant = cursor.fetchone()
        if not tenant: raise HTTPException(status_code=404, detail="Tenant not found")

        # Lock the wallet so a concurrent purchase/payment can't interleave with this credit.
        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (req.tenant_id,))
        wallet_row = cursor.fetchone()
        if not wallet_row:
            raise HTTPException(status_code=404, detail="Tenant wallet not found.")
        wallet_id, before_balance = wallet_row
        after_balance = before_balance + amount

        cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (after_balance, wallet_id))
        cursor.execute(
            """
            INSERT INTO transactions (wallet_id, amount, transaction_type, reference, before_balance, after_balance, idempotency_key)
            VALUES (%s, %s, 'CREDIT_NOTE', %s, %s, %s, %s)
            """,
            (wallet_id, amount, req.reason, before_balance, after_balance, str(uuid.uuid4()))
        )

        note_no = f"CN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{req.tenant_id}"
        conn.commit()
        
        send_notification(
            f"{tenant[0]} {tenant[1]}", tenant[2], tenant[3],
            f"Credit Note {note_no} for R{amount:.2f} applied to your account. Reason: {req.reason}",
            subject="Credit Note Issued"
        )
        return {"status": "success", "message": "Credit Note generated.", "note_no": note_no, "amount": float(amount)}
    except HTTPException:
        conn.rollback(); raise
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close(); conn.close()

# 2. Property-Level Report
@router.get("/property-report/")
def api_property_report(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: a non-admin only ever sees their own property's roll-up.
        scope_id = resolve_property_scope(current_user, property_id)

        # Joins the real properties table via property_id instead of the legacy free-text
        # tenants.property_name column, which was defaulted to a hardcoded test name and
        # never stayed in sync when a property was renamed.
        base_query = """
            SELECT p.name,
                   COUNT(t.id),
                   COALESCE(SUM(t.rent_outstanding + t.electricity_outstanding + t.water_outstanding), 0),
                   COALESCE(SUM(w.balance), 0)
            FROM tenants t
            JOIN wallets w ON t.id = w.tenant_id
            LEFT JOIN properties p ON t.property_id = p.id
        """
        if scope_id:
            cursor.execute(base_query + " WHERE t.property_id = %s GROUP BY p.id, p.name ORDER BY p.name", (scope_id,))
        else:
            cursor.execute(base_query + " GROUP BY p.id, p.name ORDER BY p.name")

        data = cursor.fetchall()
        properties = [{"name": r[0] or "Unassigned", "tenant_count": r[1], "total_arrears": float(r[2]), "wallet_balance": float(r[3])} for r in data]
        return {"status": "success", "properties": properties}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 3. Management Fee Invoice
@router.get("/management-fee-invoice/")
def api_management_fee_invoice(property_id: int = None, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: management fees are billed per property, so a Manager must not see
        # (or invoice against) collections from properties they don't manage.
        scope_id = resolve_property_scope(current_user, property_id)
        scope_join = """
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
        """
        scope_where = " AND tn.property_id = %s" if scope_id else ""
        params = (scope_id,) if scope_id else ()

        cursor.execute(
            "SELECT COALESCE(SUM(tx.amount), 0)" + scope_join +
            "WHERE " + MONEY_IN_SQL + scope_where,
            params
        )
        total_collections = float(cursor.fetchone()[0])
        management_fee = total_collections * 0.10
        
        cursor.execute(
            "SELECT COUNT(*)" + scope_join +
            "WHERE tx.transaction_type = 'ADJUSTMENT_RENT'" + scope_where,
            params
        )
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
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 4. Bank Reconciliation
@router.get("/bank-reconciliation/")
def api_bank_reconciliation(property_id: int = None, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: bank reconciliation totals are financial data per property.
        scope_id = resolve_property_scope(current_user, property_id)
        scope_join = """
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
        """
        scope_where = " AND tn.property_id = %s" if scope_id else ""
        params = (scope_id,) if scope_id else ()

        cursor.execute("SELECT COALESCE(SUM(tx.amount), 0)" + scope_join + "WHERE " + MONEY_IN_SQL + scope_where, params)
        total_in = float(cursor.fetchone()[0])
        cursor.execute("SELECT COALESCE(SUM(ABS(tx.amount)), 0)" + scope_join + "WHERE " + MONEY_OUT_SQL + scope_where, params)
        total_out = float(cursor.fetchone()[0])
        
        return {
            "status": "success",
            "total_collected": total_in,
            "total_disbursed": total_out,
            "net_balance": total_in - total_out
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()

# 5. 3-Month Comparative Stats
@router.get("/three-month-stats/")
def api_three_month_stats(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: consumption stats must not leak other properties' usage patterns.
        scope_id = resolve_property_scope(current_user, property_id)
        query = """
            SELECT TO_CHAR(tx.created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN tx.transaction_type LIKE '%%ELECTRICITY%%' THEN ABS(tx.amount) ELSE 0 END), 0) as elec,
                   COALESCE(SUM(CASE WHEN tx.transaction_type LIKE '%%WATER%%' THEN ABS(tx.amount) ELSE 0 END), 0) as water
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
            WHERE """ + MONEY_OUT_SQL + """ AND tx.created_at > NOW() - INTERVAL '3 months'
        """
        if scope_id:
            cursor.execute(query + " AND tn.property_id = %s GROUP BY month ORDER BY month ASC", (scope_id,))
        else:
            cursor.execute(query + " GROUP BY month ORDER BY month ASC")

        data = cursor.fetchall()
        stats = [{"month": r[0], "elec": float(r[1]), "water": float(r[2])} for r in data]
        return {"status": "success", "stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close(); conn.close()