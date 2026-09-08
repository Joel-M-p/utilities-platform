from fastapi import APIRouter, Depends
from api.database import get_db_connection
from api.security import verify_token
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/financial-report/", dependencies=[Depends(verify_token)])
def api_get_financial_report():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as total_billed
            FROM transactions
        """)
        rev_data = cursor.fetchone()
        total_revenue = float(rev_data[0])
        total_billed = float(rev_data[1])
        
        cursor.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as revenue,
                   COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as billed
            FROM transactions
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        monthly_data = cursor.fetchall()
        monthly = [{"month": r[0], "revenue": float(r[1]), "billed": float(r[2])} for r in monthly_data]

        cursor.execute("""
            SELECT 
                COALESCE(SUM(rent_outstanding), 0),
                COALESCE(SUM(electricity_outstanding), 0),
                COALESCE(SUM(water_outstanding), 0)
            FROM tenants
        """)
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
            WHERE tx.amount < 0 AND (tx.transaction_type LIKE '%_BILL' OR tx.transaction_type LIKE '%_USAGE')
            GROUP BY t.first_name, t.last_name
            ORDER BY total_consumption DESC
            LIMIT 10
        """)
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
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()

# NEW: Payment Reconciliation Report
@router.get("/payment-reconciliation/", dependencies=[Depends(verify_token)])
def api_get_payment_reconciliation():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.id, t.first_name, t.last_name, t.email,
                   COALESCE(SUM(CASE WHEN tx.amount < 0 THEN ABS(tx.amount) ELSE 0 END), 0) as total_billed,
                   COALESCE(SUM(CASE WHEN tx.amount > 0 THEN tx.amount ELSE 0 END), 0) as total_paid,
                   w.balance as wallet_balance,
                   t.rent_outstanding, t.electricity_outstanding, t.water_outstanding
            FROM tenants t
            JOIN wallets w ON t.id = w.tenant_id
            LEFT JOIN transactions tx ON w.id = tx.wallet_id
            GROUP BY t.id, t.first_name, t.last_name, t.email, w.balance, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding
            HAVING (t.rent_outstanding + t.electricity_outstanding + t.water_outstanding) > 0
            ORDER BY t.first_name ASC
        """)
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
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()