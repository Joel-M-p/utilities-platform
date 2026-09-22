from fastapi import APIRouter, Depends, HTTPException
from api.database import get_db_connection
from api.security import verify_token, resolve_property_scope
from fastapi.responses import JSONResponse
from api.services.tx_classification import MONEY_IN_SQL, MONEY_OUT_SQL

router = APIRouter()

@router.get("/analytics/")
def api_get_bi_analytics(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Scoped: BI analytics expose tenant names, consumption and revenue per property.
        scope_id = resolve_property_scope(current_user, property_id)
        t_filter = " AND t.property_id = %s" if scope_id else ""
        params = (scope_id,) if scope_id else ()
        # 1. High Consumers (Top 5)
        cursor.execute("""
            SELECT t.first_name, t.last_name, COALESCE(SUM(ABS(tx.amount)), 0) as total_consumption
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
            WHERE """ + MONEY_OUT_SQL + """
        """ + t_filter + """
            GROUP BY t.first_name, t.last_name
            ORDER BY total_consumption DESC
            LIMIT 5
        """, params)
        high_consumers = [{"name": f"{r[0]} {r[1]}", "value": float(r[2])} for r in cursor.fetchall()]

        # 2. Usage Anomalies (Spikes > 150% of average)
        cursor.execute("""
            SELECT t.first_name, t.last_name, 
                   AVG(ABS(tx.amount)) as avg_usage
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
            WHERE """ + MONEY_OUT_SQL + """
        """ + t_filter + """
            GROUP BY t.first_name, t.last_name
            HAVING COUNT(tx.id) > 1
        """, params)
        anomalies = []
        for r in cursor.fetchall():
            if float(r[2]) > 50: # Simulated threshold for anomaly
                anomalies.append({"name": f"{r[0]} {r[1]}", "avg": float(r[2]), "spike": float(r[2]) * 2.5})

        # 3. Revenue Analytics
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN """ + MONEY_IN_SQL + """ THEN tx.amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN """ + MONEY_OUT_SQL + """ THEN ABS(tx.amount) ELSE 0 END), 0)
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
        """ + (" WHERE t.property_id = %s" if scope_id else ""), params)
        rev = cursor.fetchone()
        total_rev = float(rev[0])
        total_billed = float(rev[1])
        leakage = total_billed - total_rev

        # 4. Collection Trend (Last 6 months)
        cursor.execute("""
            SELECT TO_CHAR(tx.created_at, 'YYYY-MM') as month,
                   COALESCE(SUM(CASE WHEN """ + MONEY_IN_SQL + """ THEN tx.amount ELSE 0 END), 0) / 
                   NULLIF(COALESCE(SUM(CASE WHEN """ + MONEY_OUT_SQL + """ THEN ABS(tx.amount) ELSE 0 END), 0), 0) * 100 as rate
            FROM transactions tx
            JOIN wallets w ON tx.wallet_id = w.id
            JOIN tenants t ON w.tenant_id = t.id
        """ + (" WHERE t.property_id = %s" if scope_id else "") + """
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """, params)
        trends = [{"month": r[0], "rate": float(r[1]) if r[1] else 0.0} for r in cursor.fetchall()]

        # 5. Operational Analytics (Meter Health)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN valve_status = 'OPEN' THEN 1 END),
                COUNT(CASE WHEN valve_status = 'TRICKLE' THEN 1 END),
                COUNT(CASE WHEN valve_status = 'DISCONNECTED' THEN 1 END),
                COUNT(CASE WHEN is_active = FALSE THEN 1 END)
            FROM meters
        """ + (" WHERE property_id = %s" if scope_id else ""), params)
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
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()