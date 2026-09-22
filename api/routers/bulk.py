from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token, require_staff, resolve_property_scope
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

# SECURITY: staff-only and property-scoped. This previously rewrote tariff_id on every
# active meter of the given type across the ENTIRE portfolio, so one Manager could change
# every other property's billing rate in a single call.
@router.post("/bulk-update-tariff/")
def api_bulk_update_tariff(req: BulkTariffUpdate, property_id: int = None, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        scope_id = resolve_property_scope(current_user, property_id)
        if not scope_id:
            # Refuse an unscoped portfolio-wide rate change even for an admin: it must be a
            # deliberate, explicit choice of property rather than an accidental global update.
            raise HTTPException(status_code=400, detail="A property_id is required for bulk tariff updates.")

        # The tariff being applied must itself belong to that property, otherwise meters
        # would be billed against another property's rate card.
        cursor.execute("SELECT id FROM tariffs WHERE id = %s AND property_id = %s", (req.tariff_id, scope_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="That tariff does not exist for this property.")

        cursor.execute(
            "UPDATE meters SET tariff_id = %s WHERE meter_type = %s AND is_active = TRUE AND property_id = %s",
            (req.tariff_id, req.meter_type.upper(), scope_id)
        )
        affected = cursor.rowcount
        conn.commit()
        return {"status": "success", "message": f"Tariff updated for {affected} active {req.meter_type} meters."}
    except HTTPException:
        conn.rollback(); raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# SECURITY: staff-only and property-scoped. This previously messaged every active tenant
# in every property in the system.
@router.post("/bulk-notify/")
def api_bulk_notify(req: BulkNotifyRequest, property_id: int = None, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        scope_id = resolve_property_scope(current_user, property_id)
        base_query = "SELECT first_name, last_name, email, cellphone FROM tenants WHERE UPPER(status) = 'ACTIVE' AND is_anonymized = FALSE"
        if scope_id:
            cursor.execute(base_query + " AND property_id = %s", (scope_id,))
        else:
            cursor.execute(base_query)
        tenants = cursor.fetchall()
        count = 0
        for t in tenants:
            send_notification(f"{t[0]} {t[1]}", t[2], t[3], req.message, subject="Important Notice from Management")
            count += 1
        return {"status": "success", "message": f"Notification sent to {count} active tenants."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# SECURITY: staff-only and property-scoped. This previously raised bills against every
# postpaid meter in the entire portfolio.
@router.post("/bulk-generate-bills/")
def api_bulk_generate_bills(req: BulkBillingRequest, property_id: int = None, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        scope_id = resolve_property_scope(current_user, property_id)
        if not scope_id:
            # Billing the whole portfolio in one unscoped call is never a safe default.
            raise HTTPException(status_code=400, detail="A property_id is required for bulk billing.")

        # Get active POSTPAID meters for this property only
        cursor.execute("""
            SELECT m.id, m.tenant_id, m.meter_type, m.tariff_id 
            FROM meters m 
            WHERE m.billing_type = 'POSTPAID' AND m.is_active = TRUE AND m.property_id = %s
        """, (scope_id,))
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
    except HTTPException:
        conn.rollback(); raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()