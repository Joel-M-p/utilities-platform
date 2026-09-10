from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.schemas import BillRequest
from api.security import verify_token, enforce_property_access
from api.services.notifications import send_notification
from decimal import Decimal
import uuid
import psycopg2

router = APIRouter()

@router.post("/generate-bill/")
def api_generate_bill(bill: BillRequest, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTHORIZATION & IDEMPOTENCY ---
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (bill.tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        idempotency_key = str(uuid.uuid4())
        cursor.execute("SELECT id FROM transactions WHERE idempotency_key = %s", (idempotency_key,))
        if cursor.fetchone():
            return {"status": "success", "message": "Bill already processed."}

        # --- ROW LOCKING ---
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s FOR UPDATE", (bill.tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email = tenant_data
        
        utility_type = bill.utility_type.upper()
        
        # --- SMART METER MATCHING ---
        if utility_type == 'WATER':
            cursor.execute("""
                SELECT m.id, m.billing_type, m.valve_status, m.tariff_id, m.meter_type 
                FROM meters m
                WHERE m.tenant_id = %s AND m.meter_type LIKE 'WATER%%' AND m.is_active = TRUE
                FOR UPDATE
            """, (bill.tenant_id,))
        else:
            cursor.execute("""
                SELECT m.id, m.billing_type, m.valve_status, m.tariff_id, m.meter_type 
                FROM meters m
                WHERE m.tenant_id = %s AND m.meter_type = %s AND m.is_active = TRUE
                FOR UPDATE
            """, (bill.tenant_id, utility_type))
            
        meter_data = cursor.fetchone()
        
        if not meter_data:
            raise HTTPException(status_code=404, detail=f"No active {utility_type} meter found for this tenant.")
            
        meter_id, billing_type, current_valve_status, tariff_id, actual_meter_type = meter_data
        utility_type = actual_meter_type

        if bill.manual_entry and billing_type == 'PREPAID':
            raise HTTPException(status_code=400, detail=f"Manual billing is disabled for Prepaid meters. {utility_type} is deducted automatically by the smart meter.")

        if not tariff_id:
            raise HTTPException(status_code=400, detail="No tariff assigned to this meter.")
            
        cursor.execute("""
            SELECT structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate 
            FROM tariffs WHERE id = %s
        """, (tariff_id,))
        tariff_data = cursor.fetchone()
        if not tariff_data:
            raise HTTPException(status_code=404, detail="Tariff not found.")
            
        structure = tariff_data[0]
        rate_flat = tariff_data[1] or Decimal('0')
        tier_1_limit = tariff_data[2] or 0
        tier_1_rate = tariff_data[3] or Decimal('0')
        tier_2_rate = tariff_data[4] or Decimal('0')
        tou_peak_rate = tariff_data[5] or Decimal('0')
        tou_offpeak_rate = tariff_data[6] or Decimal('0')

        bill_amount = Decimal('0.0')
        
        if structure == 'FLAT':
            units = Decimal(str(bill.amount))
            bill_amount = units * rate_flat
            
        elif structure == 'TIERED':
            units = Decimal(str(bill.amount))
            if units <= tier_1_limit:
                bill_amount = units * tier_1_rate
            else:
                bill_amount = (Decimal(tier_1_limit) * tier_1_rate) + ((units - Decimal(tier_1_limit)) * tier_2_rate)
                
        elif structure == 'TOU':
            peak_units = Decimal(str(bill.peak_units))
            offpeak_units = Decimal(str(bill.offpeak_units))
            bill_amount = (peak_units * tou_peak_rate) + (offpeak_units * tou_offpeak_rate)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tariff structure: {structure}")

        # --- SAFE WALLET UPDATE ---
        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (bill.tenant_id,))
        wallet_data = cursor.fetchone()
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet not found.")
        wallet_id, current_balance = wallet_data
        
        is_restricted = False

        if billing_type == 'POSTPAID':
            if utility_type == 'ELECTRICITY':
                cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding + %s WHERE id = %s", (bill_amount, bill.tenant_id))
            elif utility_type.startswith('WATER'):
                cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding + %s WHERE id = %s", (bill_amount, bill.tenant_id))
                
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, 'Postpaid Meter Reading', %s, %s, %s, %s)
            """, (wallet_id, bill_amount, f"{utility_type}_BILL", tenant_info[0], current_balance, current_balance, idempotency_key))
            
            msg = f"Your {utility_type} bill of R{bill_amount:.2f} has been generated. You now have arrears. Please pay to avoid restrictions."
            send_notification(f"{first_name} {last_name}", email, msg, subject="Bill Generated & Arrears Detected")
            
        elif billing_type == 'PREPAID':
            new_balance = current_balance - bill_amount
            
            if new_balance < 0:
                shortfall = abs(new_balance)
                new_balance = Decimal('0.00')
                
                if utility_type == 'ELECTRICITY':
                    cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding + %s WHERE id = %s", (shortfall, bill.tenant_id))
                elif utility_type.startswith('WATER'):
                    cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding + %s WHERE id = %s", (shortfall, bill.tenant_id))
                
                if utility_type.startswith('WATER'):
                    restrict_status = 'TRICKLE'
                elif utility_type == 'ELECTRICITY':
                    restrict_status = 'DISCONNECTED'
                
                cursor.execute("UPDATE meters SET valve_status = %s WHERE id = %s", (restrict_status, meter_id))
                is_restricted = True
                
                action_word = 'restricted to trickle' if utility_type.startswith('WATER') else 'DISCONNECTED'
                msg = f"Your {utility_type} has been {action_word}! Shortfall of R{shortfall:.2f} added to arrears."
                send_notification(f"{first_name} {last_name}", email, msg, subject="Utility Disconnected/Restricted")
            else:
                if new_balance < 50:
                    msg = f"Low Wallet Balance Alert: Your balance is R{new_balance:.2f}. Please top up to avoid disconnection."
                    send_notification(f"{first_name} {last_name}", email, msg, subject="Low Wallet Balance Alert")
            
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, 'Prepaid Meter Deduction', %s, %s, %s, %s)
            """, (wallet_id, bill_amount, f"{utility_type}_USAGE", tenant_info[0], current_balance, new_balance, idempotency_key))
            
        conn.commit()
        
        cursor.execute("SELECT rent_outstanding, electricity_outstanding, water_outstanding FROM tenants WHERE id = %s", (bill.tenant_id,))
        t = cursor.fetchone()
        cursor.execute("SELECT balance FROM wallets WHERE id = %s", (wallet_id,))
        w = cursor.fetchone()

        return {
            "status": "success", 
            "message": f"{utility_type} {'bill generated' if billing_type == 'POSTPAID' else 'usage processed'}! (Structure: {structure})", 
            "billing_type": billing_type,
            "restricted": is_restricted,
            "new_wallet_balance": float(w[0]),
            "new_rent_outstanding": float(t[0]),
            "new_electricity_outstanding": float(t[1]),
            "new_water_outstanding": float(t[2])
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"status": "success", "message": "Bill already processed."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()