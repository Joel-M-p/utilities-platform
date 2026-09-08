from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from api.services.notifications import send_notification
from pydantic import BaseModel
from decimal import Decimal
import random

router = APIRouter()

class BulkTariffUpdate(BaseModel):
    meter_type: str
    tariff_id: int

class BulkNotifyRequest(BaseModel):
    message: str

class BulkBillingRequest(BaseModel):
    month: str

@router.post("/bulk-update-tariff/", dependencies=[Depends(verify_token)])
def api_bulk_update_tariff(req: BulkTariffUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE meters SET tariff_id = %s WHERE meter_type = %s AND is_active = TRUE", (req.tariff_id, req.meter_type.upper()))
        affected = cursor.rowcount
        conn.commit()
        return {"status": "success", "message": f"Tariff updated for {affected} active {req.meter_type} meters."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/bulk-notify/", dependencies=[Depends(verify_token)])
def api_bulk_notify(req: BulkNotifyRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE status = 'ACTIVE' AND is_anonymized = FALSE")
        tenants = cursor.fetchall()
        count = 0
        for t in tenants:
            send_notification(f"{t[0]} {t[1]}", t[2], req.message, subject="Important Notice from Management")
            count += 1
        return {"status": "success", "message": f"Notification sent to {count} active tenants."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/bulk-generate-bills/", dependencies=[Depends(verify_token)])
def api_bulk_generate_bills(req: BulkBillingRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get all active POSTPAID meters
        cursor.execute("""
            SELECT m.id, m.tenant_id, m.meter_type, m.tariff_id 
            FROM meters m 
            WHERE m.billing_type = 'POSTPAID' AND m.is_active = TRUE
        """)
        meters = cursor.fetchall()
        billed_count = 0
        
        for m in meters:
            meter_id, tenant_id, m_type, tariff_id = m
            
            # Simulate a meter reading (random 5-50 units)
            units_used = Decimal(str(random.uniform(5.0, 50.0)))
            
            # Fetch tariff
            cursor.execute("SELECT structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate FROM tariffs WHERE id = %s", (tariff_id,))
            tariff = cursor.fetchone()
            if not tariff: continue
            
            structure = tariff[0]
            bill_amount = Decimal('0.0')
            
            if structure == 'FLAT':
                bill_amount = units_used * (tariff[1] or Decimal('0'))
            elif structure == 'TIERED':
                limit = tariff[2] or 0
                if units_used <= limit:
                    bill_amount = units_used * (tariff[3] or Decimal('0'))
                else:
                    bill_amount = (Decimal(limit) * (tariff[3] or Decimal('0'))) + ((units_used - Decimal(limit)) * (tariff[4] or Decimal('0')))
            elif structure == 'TOU':
                peak_units = units_used / 2
                offpeak_units = units_used / 2
                bill_amount = (peak_units * (tariff[5] or Decimal('0'))) + (offpeak_units * (tariff[6] or Decimal('0')))
            else:
                continue
                
            # Fetch Wallet
            cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
            w = cursor.fetchone()
            if not w: continue
            wallet_id = w[0]
            
            # Update Arrears
            if m_type == 'ELECTRICITY':
                cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding + %s WHERE id = %s", (bill_amount, tenant_id))
            elif m_type.startswith('WATER'):
                cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding + %s WHERE id = %s", (bill_amount, tenant_id))
                
            # Insert Transaction
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, %s, %s)", (wallet_id, bill_amount, f"{m_type}_BILL", f"Bulk Billing - {req.month}"))
            billed_count += 1
            
        conn.commit()
        return {"status": "success", "message": f"Bulk billing complete for {req.month}. {billed_count} postpaid meters billed."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()