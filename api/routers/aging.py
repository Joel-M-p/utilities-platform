from fastapi import APIRouter, Depends
from api.database import get_db_connection
from api.security import verify_token
from datetime import datetime
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/arrears-aging/", dependencies=[Depends(verify_token)])
def api_get_arrears_aging():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Fetch all tenants with outstanding arrears
        cursor.execute("""
            SELECT t.id, t.first_name, t.last_name, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding, w.id
            FROM tenants t JOIN wallets w ON t.id = w.tenant_id 
            WHERE (t.rent_outstanding + t.electricity_outstanding + t.water_outstanding) > 0
            ORDER BY t.id ASC
        """)
        tenants = cursor.fetchall()
        
        aging_report = []
        
        # 2. For each tenant, fetch their transaction history and run FIFO allocation
        for t in tenants:
            tenant_id, first, last, rent, elec, water, wallet_id = t
            total_arrears = float(rent) + float(elec) + float(water)
            
            cursor.execute("""
                SELECT created_at, amount 
                FROM transactions 
                WHERE wallet_id = %s 
                ORDER BY created_at ASC
            """, (wallet_id,))
            txns = cursor.fetchall()
            
            # FIFO Logic: Bills (negative amounts) are added to a queue. Payments (positive) pay off the oldest bills first.
            bills_queue = []
            for tx in txns:
                date = tx[0]
                amount = float(tx[1])
                if amount < 0: # It's a bill
                    bills_queue.append({'date': date, 'amount': abs(amount)})
                else: # It's a payment
                    pay_remaining = amount
                    for b in bills_queue:
                        if pay_remaining <= 0: break
                        if b['amount'] <= pay_remaining:
                            pay_remaining -= b['amount']
                            b['amount'] = 0 # Fully paid
                        else:
                            b['amount'] -= pay_remaining
                            pay_remaining = 0
            
            today = datetime.now()
            buckets = {'current': 0.0, '30': 0.0, '60': 0.0, '90': 0.0}
            
            # Calculate age of remaining unpaid bills
            for b in bills_queue:
                if b['amount'] > 0.01: 
                    age_days = (today - b['date']).days
                    if age_days <= 30: buckets['current'] += b['amount']
                    elif age_days <= 60: buckets['30'] += b['amount']
                    elif age_days <= 90: buckets['60'] += b['amount']
                    else: buckets['90'] += b['amount']
            
            # Fix floating point precision so sum(buckets) == total_arrears
            diff = total_arrears - (buckets['current'] + buckets['30'] + buckets['60'] + buckets['90'])
            buckets['current'] += diff
            
            aging_report.append({
                "tenant_id": tenant_id,
                "tenant_name": f"{first} {last}",
                "total_arrears": round(total_arrears, 2),
                "current": round(buckets['current'], 2),
                "days_30": round(buckets['30'], 2),
                "days_60": round(buckets['60'], 2),
                "days_90": round(buckets['90'], 2)
            })
            
        return {"status": "success", "aging": aging_report}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        cursor.close()
        conn.close()