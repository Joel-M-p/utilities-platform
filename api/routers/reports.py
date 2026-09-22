from fastapi import APIRouter, Depends, HTTPException
from api.database import get_db_connection
from api.security import verify_token, resolve_property_scope
from api.services.tx_classification import MONEY_IN_SQL, MONEY_OUT_SQL
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/financial-report/")
def api_get_financial_report(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: revenue, arrears and consumption are per-property financial data.
        scope_id = resolve_property_scope(current_user, property_id)
        tx_scope = """
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
        """
        tx_where = " WHERE tn.property_id = %s" if scope_id else ""
        params = (scope_id,) if scope_id else ()
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN """ + MONEY_IN_SQL + """ THEN tx.amount ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN """ + MONEY_OUT_SQL + """ THEN ABS(tx.amount) ELSE 0 END), 0) as total_billed
        """ + tx_scope + tx_where, params)
        rev_data = cursor.fetchone()
        total_revenue = float(rev_data[0])
        total_billed = float(rev_data[1])
        
        cursor.execute("""
            SELECT TO_CHAR(tx.created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN """ + MONEY_IN_SQL + """ THEN tx.amount ELSE 0 END), 0) as revenue,
                   COALESCE(SUM(CASE WHEN """ + MONEY_OUT_SQL + """ THEN ABS(tx.amount) ELSE 0 END), 0) as billed
        """ + tx_scope + tx_where + """
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """, params)
        monthly_data = cursor.fetchall()
        monthly = [{"month": r[0], "revenue": float(r[1]), "billed": float(r[2])} for r in monthly_data]

        cursor.execute("""
            SELECT 
                COALESCE(SUM(rent_outstanding), 0),
                COALESCE(SUM(electricity_outstanding), 0),
                COALESCE(SUM(water_outstanding), 0)
            FROM tenants
        """ + (" WHERE property_id = %s" if scope_id else ""), params)
        arr_data = cursor.fetchone()
        arrears = {
            "rent": float(arr_data[0]),
            "electricity": float(arr_data[1]),
            "water": float(arr_data[2]),
            "total": float(arr_data[0]) + float(arr_data[1]) + float(arr_data[2])
        }

        cursor.execute("""
            SELECT t.first_name, t.last_name, 
                   COALESCE(SUM(ABS(tx.amount)), 0) as total_consumption
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
            WHERE """ + MONEY_OUT_SQL + """
        """ + (" AND t.property_id = %s" if scope_id else "") + """
            GROUP BY t.first_name, t.last_name
            ORDER BY total_consumption DESC
            LIMIT 10
        """, params)
        cons_data = cursor.fetchall()
        consumption = [{"tenant": f"{r[0]} {r[1]}", "value": float(r[2])} for r in cons_data]

        return {
            "status": "success",
            "revenue": {
                "total_revenue": total_revenue,
                "total_billed": total_billed,
                "collection_rate": (total_revenue / total_billed * 100) if total_billed > 0 else 0.0,
                "monthly": monthly
            },
            "arrears": arrears,
            "consumption": consumption
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()

# NEW: Payment Reconciliation Report
@router.get("/payment-reconciliation/")
def api_get_payment_reconciliation(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: per-tenant billing/payment reconciliation is property-level data.
        scope_id = resolve_property_scope(current_user, property_id)
        cursor.execute("""
            SELECT t.id, t.first_name, t.last_name, t.email,
                   COALESCE(SUM(CASE WHEN """ + MONEY_OUT_SQL + """ THEN ABS(tx.amount) ELSE 0 END), 0) as total_billed,
                   COALESCE(SUM(CASE WHEN """ + MONEY_IN_SQL + """ THEN tx.amount ELSE 0 END), 0) as total_paid,
                   w.balance as wallet_balance,
                   t.rent_outstanding, t.electricity_outstanding, t.water_outstanding
            FROM tenants t
            JOIN wallets w ON t.id = w.tenant_id
            LEFT JOIN transactions tx ON w.id = tx.wallet_id
        """ + (" WHERE t.property_id = %s" if scope_id else "") + """
            GROUP BY t.id, t.first_name, t.last_name, t.email, w.balance, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding
            HAVING (t.rent_outstanding + t.electricity_outstanding + t.water_outstanding) > 0
            ORDER BY t.first_name ASC
        """, (scope_id,) if scope_id else ())
        rows = cursor.fetchall()
        recon_list = []
        for row in rows:
            total_billed = float(row[4])
            total_paid = float(row[5])
            wallet_balance = float(row[6])
            total_arrears = float(row[7]) + float(row[8]) + float(row[9])
            
            recon_list.append({
                "tenant_id": row[0],
                "tenant_name": f"{row[1]} {row[2]}",
                "email": row[3],
                "total_billed": total_billed,
                "total_paid": total_paid,
                "wallet_balance": wallet_balance,
                "rent_arrears": float(row[7]),
                "elec_arrears": float(row[8]),
                "water_arrears": float(row[9]),
                "total_arrears": total_arrears,
                # Net amount they owe us (Total Arrears minus any positive wallet credit)
                "balance_due": total_arrears - wallet_balance 
            })
        return {"status": "success", "reconciliation": recon_list}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()