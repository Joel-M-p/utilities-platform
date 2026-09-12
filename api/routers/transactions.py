from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token, enforce_property_access, require_staff
from api.routers.tenants import check_tenant_access
from api.services.waterfall import process_waterfall_payment
from api.services.token_engine import generate_token
from api.services.notifications import send_notification
from decimal import Decimal
import datetime
import uuid
import psycopg2

router = APIRouter()

@router.post("/process-payment/")
def api_process_payment(payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tenant_id = payload.get("tenant_id")
        amount = payload.get("amount")
        rent_pct = payload.get("rent_pct")
        elec_pct = payload.get("elec_pct")
        water_pct = payload.get("water_pct")

        prop_id = check_tenant_access(cursor, tenant_id, current_user)

        idempotency_key = payload.get("idempotency_key") or str(uuid.uuid4())
        cursor.execute("SELECT id FROM transactions WHERE idempotency_key LIKE %s", (f"{idempotency_key}-%",))
        if cursor.fetchone():
            return {"status": "success", "message": "Payment already processed."}

        result = process_waterfall_payment(cursor, tenant_id, amount, rent_pct, elec_pct, water_pct, idempotency_key)
        
        cursor.execute("SELECT first_name, last_name, email, cellphone FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cursor.fetchone()
        first_name, last_name, email, cellphone = tenant
        
        receipt_no = f"RCP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{tenant_id}"
        receipt_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.commit()
        
        receipt_message = f"Payment of R{amount:.2f} received. Receipt No: {receipt_no}. Date: {receipt_date}. Thank you for your payment!"
        send_notification(f"{first_name} {last_name}", email, cellphone, receipt_message, subject=f"Payment Receipt - {receipt_no}")
        
        return {
            "status": "success", 
            "message": "Payment allocated successfully!", 
            "receipt_no": receipt_no,
            "receipt_date": receipt_date,
            "amount": amount
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"status": "success", "message": "Payment already processed."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/buy-utility/")
def api_buy_utility(req: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tenant_id = req.get("tenant_id")
        utility_type = req.get("utility_type").upper()
        amount = req.get("amount")
        amount_decimal = Decimal(str(amount))

        prop_id = check_tenant_access(cursor, tenant_id, current_user)

        idempotency_key = req.get("idempotency_key") or str(uuid.uuid4())
        cursor.execute("SELECT id FROM transactions WHERE idempotency_key = %s", (idempotency_key,))
        if cursor.fetchone():
            return {"status": "success", "message": "Purchase already processed."}

        cursor.execute("SELECT first_name, last_name, email, rent_outstanding, cellphone FROM tenants WHERE id = %s FOR UPDATE", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email, rent_owed, cellphone = tenant_data
        
        if rent_owed > 0:
            raise HTTPException(status_code=403, detail=f"Action Blocked: You have outstanding rent arrears of R{rent_owed:.2f}. Please clear your rent first before purchasing utilities.")
        
        cursor.execute("""
            SELECT m.id, m.billing_type, m.valve_status, m.hardware_type, m.tariff_id 
            FROM meters m
            WHERE m.tenant_id = %s AND m.meter_type = %s AND m.billing_type = 'PREPAID' AND m.is_active = TRUE
            FOR UPDATE
        """, (tenant_id, utility_type))
        meter_data = cursor.fetchone()
        
        if not meter_data:
            raise HTTPException(status_code=404, detail=f"No active PREPAID {utility_type} meter found.")
            
        meter_id, billing_type, current_valve_status, hardware_type, tariff_id = meter_data
        
        # --- EMERGENCY FUND LOGIC (SIMPLIFIED & ACCURATE) ---
        cursor.execute("SELECT id, balance, credit_limit, credit_balance, credit_taps_used, credit_reset_month FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id, current_balance, credit_limit, credit_balance, credit_taps_used, credit_reset_month = wallet_data
        
        current_month = datetime.datetime.now().strftime("%Y-%m")
        if credit_reset_month != current_month:
            credit_balance = credit_limit or Decimal('0')
            credit_taps_used = 0
            cursor.execute("UPDATE wallets SET credit_balance = %s, credit_taps_used = 0, credit_reset_month = %s WHERE id = %s", (credit_balance, current_month, wallet_id))

        available_funds = current_balance + (credit_balance or Decimal('0'))
        if available_funds < amount_decimal:
            raise HTTPException(status_code=400, detail=f"Insufficient funds. Available: R{available_funds:.2f}.")
        
        needs_credit = False
        credit_to_use = Decimal('0.00')
        if current_balance < amount_decimal:
            needs_credit = True
            credit_to_use = amount_decimal - current_balance
            if credit_taps_used >= 3:
                raise HTTPException(status_code=403, detail="Insufficient main wallet funds. You have used your 3 allowed emergency fund taps for this month.")

        if needs_credit:
            new_balance = Decimal('0.00')
            new_credit_balance = (credit_balance or Decimal('0')) - credit_to_use
            credit_taps_used += 1
            cursor.execute("UPDATE wallets SET balance = 0.00, credit_balance = %s, credit_taps_used = %s WHERE id = %s", (new_credit_balance, credit_taps_used, wallet_id))
        else:
            new_balance = current_balance - amount_decimal
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
        
        token = None
        reference_text = ""
        units_purchased = Decimal('0')
        vat_amount = Decimal('0.00')
        txn_status = "FAILED_DELIVERY"
        
        cursor.execute("SELECT rate_flat FROM tariffs WHERE id = %s", (tariff_id,))
        tariff_data = cursor.fetchone()
        if tariff_data and tariff_data[0]:
            rate = Decimal(str(tariff_data[0]))
        else:
            rate = Decimal('1.0')

        cursor.execute("SELECT vat_percent FROM company WHERE id = 1")
        company_vat = cursor.fetchone()
        if company_vat and company_vat[0]:
            vat_percent = Decimal(str(company_vat[0])) / Decimal(100)
        else:
            vat_percent = Decimal('0.15')

        if hardware_type == 'STS':
            token = generate_token()
            txn_status = "TOKEN_ISSUED"
            vat_amount = (amount_decimal / (Decimal('1') + vat_percent)) * vat_percent
            amount_ex_vat = amount_decimal - vat_amount
            if rate > 0:
                units_purchased = amount_ex_vat / rate
            
            # --- FIX: Dynamic label based on utility type ---
            unit_name = "kWh" if utility_type == "ELECTRICITY" else "kL"
            label = "Net Energy" if utility_type == "ELECTRICITY" else "Net Volume"
            reference_text = f"Token: {token} | {units_purchased:.2f} {unit_name}"
            message = f"Purchase Successful!\nAmount Paid: R{amount_decimal:.2f}\nVAT ({int(vat_percent * 100)}%): R{vat_amount:.2f}\n{label}: {units_purchased:.2f} {unit_name}\nToken: {token}"
            
        elif hardware_type == 'SMART_IOT':
            txn_status = "WALLET_CREDITED"
            if rate > 0:
                units_purchased = amount_decimal / rate
            cursor.execute("UPDATE meters SET meter_balance = meter_balance + %s WHERE id = %s", (units_purchased, meter_id))
            unit_name = "kWh" if utility_type == "ELECTRICITY" else "kL"
            reference_text = f"Smart Meter Top-up: {units_purchased:.2f} {unit_name}"
            message = f"Your smart meter has been credited with {units_purchased:.2f} {unit_name}."
            
        else:
            token = generate_token()
            txn_status = "TOKEN_ISSUED"
            vat_amount = (amount_decimal / (Decimal('1') + vat_percent)) * vat_percent
            amount_ex_vat = amount_decimal - vat_amount
            units_purchased = amount_ex_vat / rate if rate > 0 else Decimal('0')
            unit_name = "kWh" if utility_type == "ELECTRICITY" else "kL"
            label = "Net Energy" if utility_type == "ELECTRICITY" else "Net Volume"
            reference_text = f"Token: {token} | {units_purchased:.2f} {unit_name}"
            message = f"Purchase Successful! Token: {token}"

        cursor.execute("""
            INSERT INTO transactions (wallet_id, amount, transaction_type, reference, idempotency_key, property_id, before_balance, after_balance, meter_id, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (wallet_id, amount_decimal, f"{utility_type}_PURCHASE", reference_text, idempotency_key, prop_id, current_balance, new_balance, meter_id, txn_status))
        
        if current_valve_status in ['TRICKLE', 'DISCONNECTED']:
            cursor.execute("UPDATE meters SET valve_status = 'OPEN' WHERE tenant_id = %s AND meter_type = %s", (tenant_id, utility_type))
            send_notification(f"{first_name} {last_name}", email, cellphone, f"Your {utility_type} has been reconnected.")
        
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, cellphone, message)
        return {
            "status": "success", 
            "message": message, 
            "token": token, 
            "amount_paid": float(amount_decimal), 
            "vat_amount": float(vat_amount),
            "new_wallet_balance": float(new_balance),
            "units_purchased": float(units_purchased)
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"status": "success", "message": "Purchase already processed."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/set-credit-limit/{tenant_id}")
def api_set_credit_limit(tenant_id: int, limit: float, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        limit_dec = Decimal(str(limit))
        current_month = datetime.datetime.now().strftime("%Y-%m")
        
        cursor.execute("UPDATE wallets SET credit_limit = %s, credit_balance = %s, credit_taps_used = 0, credit_reset_month = %s WHERE tenant_id = %s", 
                       (limit_dec, limit_dec, current_month, tenant_id))
        conn.commit()
        return {"status": "success", "message": f"Emergency Fund limit set to R{limit:.2f}."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/adjust-account/{tenant_id}")
def api_adjust_account(tenant_id: int, req: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        prop_id = check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id, current_balance = wallet_data
        
        amount_input = Decimal(str(req.get("amount")))
        target = req.get("target").upper()
        reason = req.get("reason")
        
        cursor.execute("SELECT rent_outstanding, electricity_outstanding, water_outstanding FROM tenants WHERE id = %s FOR UPDATE", (tenant_id,))
        rent_owed, elec_owed, water_owed = cursor.fetchone()

        if target == "RENT":
            amount_input = min(amount_input, rent_owed)
        elif target == "ELECTRICITY":
            amount_input = min(amount_input, elec_owed)
        elif target == "WATER":
            amount_input = min(amount_input, water_owed)

        if target in ["RENT", "ELECTRICITY", "WATER"]:
            if amount_input <= 0:
                raise HTTPException(status_code=400, detail="No arrears to adjust for this utility.")

            new_balance = current_balance - amount_input
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
            
            if target == "RENT":
                cursor.execute("UPDATE tenants SET rent_outstanding = GREATEST(0, rent_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))
            elif target == "ELECTRICITY":
                cursor.execute("UPDATE tenants SET electricity_outstanding = GREATEST(0, electricity_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))
            elif target == "WATER":
                cursor.execute("UPDATE tenants SET water_outstanding = GREATEST(0, water_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))

            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, -amount_input, f"ADJUSTMENT_{target}", reason, prop_id, current_balance, new_balance, "COMPLETED"))

        elif target == "WALLET":
            new_balance = current_balance + amount_input
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, amount_input, f"ADJUSTMENT_{target}", reason, prop_id, current_balance, new_balance, "COMPLETED"))
        else:
            raise HTTPException(status_code=400, detail="Invalid target.")
            
        conn.commit()
        return {"status": "success", "message": f"Successfully adjusted {target} by R{float(amount_input):.2f}. Wallet balance updated."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/transactions/{tenant_id}")
def api_get_transactions(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id = wallet_data[0]
        
        cursor.execute("""
            SELECT created_at, amount, transaction_type, reference, status 
            FROM transactions 
            WHERE wallet_id = %s 
            ORDER BY created_at DESC
        """, (wallet_id,))
        
        rows = cursor.fetchall()
        txns_list = []
        for row in rows:
            txns_list.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "amount": float(row[1]),
                "type": row[2],
                "reference": row[3],
                "status": row[4] or "COMPLETED"
            })
        return {"status": "success", "transactions": txns_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# --- SEPARATED UTILITY HISTORY & TOKEN REPRINTS ---
@router.get("/tenant-utility-history/{tenant_id}")
def api_get_tenant_utility_history(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        if not wallet_data:
            return {"status": "success", "electricity": [], "water": []}
        wallet_id = wallet_data[0]
        
        cursor.execute("""
            SELECT created_at, amount, transaction_type, reference 
            FROM transactions 
            WHERE wallet_id = %s AND (transaction_type LIKE '%%_PURCHASE' OR transaction_type LIKE '%%_USAGE' OR transaction_type LIKE '%%_BILL')
            ORDER BY created_at DESC
            LIMIT 100
        """, (wallet_id,))
        
        rows = cursor.fetchall()
        
        elec_list = []
        water_list = []
        
        for row in rows:
            date_str = row[0].strftime("%Y-%m-%d %H:%M")
            amount = float(abs(row[1]))
            txn_type = row[2]
            ref = row[3] or ""
            
            token = None
            units = ""
            
            if "Token:" in ref:
                parts = ref.split("|")
                token = parts[0].replace("Token:", "").strip()
                if len(parts) > 1:
                    units = parts[1].strip()
            elif "Top-up:" in ref:
                units = ref.replace("Smart Meter Top-up:", "").strip()
            elif "BILL" in txn_type:
                units = "Postpaid Bill"
                
            record = {
                "date": date_str,
                "amount": amount,
                "type": txn_type,
                "token": token,
                "units": units
            }
            
            if "ELECTRICITY" in txn_type:
                elec_list.append(record)
            elif "WATER" in txn_type:
                water_list.append(record)
                
        return {
            "status": "success", 
            "electricity": elec_list, 
            "water": water_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/restrict-water/{tenant_id}")
def api_restrict_water(tenant_id: int, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("SELECT balance FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        if wallet_data[0] > 0:
            raise HTTPException(status_code=400, detail="Cannot restrict. Positive wallet balance.")

        cursor.execute("""
            UPDATE meters SET valve_status = 'TRICKLE' 
            WHERE tenant_id = %s AND meter_type LIKE 'WATER%%' AND billing_type = 'POSTPAID' AND is_active = TRUE
        """, (tenant_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="No active POSTPAID water meters.")
        conn.commit()
        return {"status": "success", "message": "Water restricted to TRICKLE."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/unrestrict-water/{tenant_id}")
def api_unrestrict_water(tenant_id: int, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("""
            UPDATE meters SET valve_status = 'OPEN' 
            WHERE tenant_id = %s AND meter_type LIKE 'WATER%%' AND is_active = TRUE
        """, (tenant_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="No active water meters.")
        conn.commit()
        return {"status": "success", "message": "Water flow restored."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/admin-reset-wallet/{tenant_id}")
def api_admin_reset_wallet(tenant_id: int, current_user: dict = Depends(require_staff)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("UPDATE wallets SET balance = 0.00 WHERE tenant_id = %s", (tenant_id,))
        cursor.execute("UPDATE tenants SET rent_outstanding = 0.00, electricity_outstanding = 0.00, water_outstanding = 0.00 WHERE id = %s", (tenant_id,))
        conn.commit()
        return {"status": "success", "message": f"Tenant {tenant_id} reset."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()