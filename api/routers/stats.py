from fastapi import APIRouter, Depends, HTTPException
from api.database import get_db_connection
from api.security import verify_token, resolve_property_scope
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/dashboard-stats/")
def api_get_dashboard_stats(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # The client-supplied property_id was previously trusted as-is, which let a Manager
        # read another property's KPIs by changing the query string (or omitting it to get
        # portfolio-wide figures). Resolve it against the caller's own assignment instead.
        property_id = resolve_property_scope(current_user, property_id)
        # --- AUTOMATIC SCHEMA FIX ---
        # Ensure required columns exist to prevent crashes on older databases
        cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        cursor.execute("ALTER TABLE meters ADD COLUMN IF NOT EXISTS property_id INTEGER;")
        conn.commit()

        # 1. Revenue & Billed
        if property_id:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as total_billed
                FROM transactions t
                JOIN wallets w ON t.wallet_id = w.id
                JOIN tenants tn ON w.tenant_id = tn.id
                WHERE tn.property_id = %s
            """, (property_id,))
        else:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as total_billed
                FROM transactions t
            """)
        rev_data = cursor.fetchone()
        total_revenue = float(rev_data[0])
        total_billed = float(rev_data[1])
        collection_rate = (total_revenue / total_billed * 100) if total_billed > 0 else 0.0

        # 2. Arrears Summary
        if property_id:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(rent_outstanding), 0),
                    COALESCE(SUM(electricity_outstanding), 0),
                    COALESCE(SUM(water_outstanding), 0)
                FROM tenants
                WHERE property_id = %s
            """, (property_id,))
        else:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(rent_outstanding), 0),
                    COALESCE(SUM(electricity_outstanding), 0),
                    COALESCE(SUM(water_outstanding), 0)
                FROM tenants
            """)
        arr_data = cursor.fetchone()
        total_arrears = float(arr_data[0]) + float(arr_data[1]) + float(arr_data[2])

        # 3. Active Meter Counts & Statuses
        if property_id:
            cursor.execute("""
                SELECT meter_type, valve_status, COUNT(*)
                FROM meters
                WHERE is_active = TRUE AND property_id = %s
                GROUP BY meter_type, valve_status
            """, (property_id,))
        else:
            cursor.execute("""
                SELECT meter_type, valve_status, COUNT(*)
                FROM meters
                WHERE is_active = TRUE
                GROUP BY meter_type, valve_status
            """)
        meters_data = cursor.fetchall()
        
        meter_counts = {"ELECTRICITY": 0, "WATER_HOT": 0, "WATER_COLD": 0}
        valve_statuses = {"OPEN": 0, "TRICKLE": 0, "DISCONNECTED": 0}
        
        for row in meters_data:
            m_type, v_status, count = row[0], row[1], row[2]
            if m_type in meter_counts:
                meter_counts[m_type] += count
            if v_status in valve_statuses:
                valve_statuses[v_status] += count

        # 4. Consumption Trends (Last 6 Months)
        if property_id:
            cursor.execute("""
                SELECT TO_CHAR(t.created_at, 'YYYY-MM') as month, 
                       COALESCE(SUM(ABS(t.amount)), 0) as consumption_value
                FROM transactions t
                JOIN wallets w ON t.wallet_id = w.id
                JOIN tenants tn ON w.tenant_id = tn.id
                WHERE t.amount < 0 
                  AND (t.transaction_type LIKE '%%_BILL' OR t.transaction_type LIKE '%%_USAGE') 
                  AND tn.property_id = %s
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            """, (property_id,))
        else:
            cursor.execute("""
                SELECT TO_CHAR(t.created_at, 'YYYY-MM') as month, 
                       COALESCE(SUM(ABS(t.amount)), 0) as consumption_value
                FROM transactions t
                WHERE t.amount < 0 
                  AND (t.transaction_type LIKE '%%_BILL' OR t.transaction_type LIKE '%%_USAGE')
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            """)
        trend_data = cursor.fetchall()
        trends = [{"month": row[0], "value": float(row[1])} for row in trend_data]
        trends.reverse() # Chronological order for the UI

        # 5. Tenant Counts
        if property_id:
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END)
                FROM tenants
                WHERE property_id = %s
            """, (property_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END)
                FROM tenants
            """)
        tenant_data = cursor.fetchone()
        total_tenants = tenant_data[0]
        active_tenants = tenant_data[1] or 0

        return {
            "status": "success",
            "revenue": {
                "total_revenue": total_revenue,
                "total_billed": total_billed,
                "collection_rate": collection_rate
            },
            "arrears": {
                "total_arrears": total_arrears,
                "rent": float(arr_data[0]),
                "electricity": float(arr_data[1]),
                "water": float(arr_data[2])
            },
            "meters": {
                "counts": meter_counts,
                "statuses": valve_statuses
            },
            "trends": trends,
            "tenants": {
                "total": total_tenants,
                "active": active_tenants
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()