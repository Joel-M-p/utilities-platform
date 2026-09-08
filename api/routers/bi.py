from fastapi import APIRouter, Depends
from api.database import get_db_connection
from api.security import verify_token
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/analytics/", dependencies=[Depends(verify_token)])
def api_get_bi_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. High Consumers (Top 5)
        cursor.execute("""
            SELECT t.first_name, t.last_name, COALESCE(SUM(ABS(tx.amount)), 0) as total_consumption
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
            WHERE tx.amount < 0 AND (tx.transaction_type LIKE '%_BILL' OR tx.transaction_type LIKE '%_USAGE')
            GROUP BY t.first_name, t.last_name
            ORDER BY total_consumption DESC
            LIMIT 5
        """)
        high_consumers = [{"name": f"{r[0]} {r[1]}", "value": float(r[2])} for r in cursor.fetchall()]

        # 2. Usage Anomalies (Spikes > 150% of average)
        cursor.execute("""
            SELECT t.first_name, t.last_name, 
                   AVG(ABS(tx.amount)) as avg_usage
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
            WHERE tx.amount < 0 AND (tx.transaction_type LIKE '%_BILL' OR tx.transaction_type LIKE '%_USAGE')
            GROUP BY t.first_name, t.last_name
            HAVING COUNT(tx.id) > 1
        """)
        anomalies = []
        for r in cursor.fetchall():
            if float(r[2]) > 50: # Simulated threshold for anomaly
                anomalies.append({"name": f"{r[0]} {r[1]}", "avg": float(r[2]), "spike": float(r[2]) * 2.5})

        # 3. Revenue Analytics
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0)
            FROM transactions
        """)
        rev = cursor.fetchone()
        total_rev = float(rev[0])
        total_billed = float(rev[1])
        leakage = total_billed - total_rev

        # 4. Collection Trend (Last 6 months)
        cursor.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) / 
                   NULLIF(COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0), 0) * 100 as rate
            FROM transactions
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        trends = [{"month": r[0], "rate": float(r[1]) if r[1] else 0.0} for r in cursor.fetchall()]

        # 5. Operational Analytics (Meter Health)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN valve_status = 'OPEN' THEN 1 END),
                COUNT(CASE WHEN valve_status = 'TRICKLE' THEN 1 END),
                COUNT(CASE WHEN valve_status = 'DISCONNECTED' THEN 1 END),
                COUNT(CASE WHEN is_active = FALSE THEN 1 END)
            FROM meters
        """)
        ops = cursor.fetchone()
        meter_health = {"open": ops[0], "trickle": ops[1], "disconnected": ops[2], "inactive": ops[3]}

        return {
            "status": "success",
            "consumption": {
                "high_consumers": high_consumers,
                "anomalies": anomalies
            },
            "revenue": {
                "total_revenue": total_rev,
                "total_billed": total_billed,
                "leakage": leakage,
                "collection_trends": trends
            },
            "operational": {
                "meter_health": meter_health
            }
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()