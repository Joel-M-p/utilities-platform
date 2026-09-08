from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token, enforce_property_access
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
        
        if current_user.get("role") == "TENANT":
            if current_user.get("tenant_id") != tenant_id:
                raise HTTPException(status_code=403, detail="Forbidden: You can only process payments for your own account.")

        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        idempotency_key = payload.get("idempotency_key") or str(uuid.uuid4())
        cursor.execute("SELECT id FROM transactions WHERE idempotency_key LIKE %s", (f"{idempotency_key}-%",))
        if cursor.fetchone():
            return {"status": "success", "message": "Payment already processed."}

        result = process_waterfall_payment(cursor, tenant_id, amount, rent_pct, elec_pct, water_pct, idempotency_key)
        
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cursor.fetchone()
        first_name, last_name, email = tenant
        
        receipt_no = f"RCP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{tenant_id}"
        receipt_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.commit()
        
        receipt_message = f"Payment of R{amount:.2f} received. Receipt No: {receipt_no}. Date: {receipt_date}. Thank you for your payment!"
        send_notification(f"{first_name} {last_name}", email, receipt_message, subject=f"Payment Receipt - {receipt_no}")
        
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

@router.post("/apply-wallet-to-arrears/{tenant_id}")
def api_apply_wallet_to_arrears(tenant_id: int, current_user: dict = Depends(verify_token)):
    """
    Takes the existing positive balance in the wallet and pushes it through the 
    rent-first waterfall to clear arrears automatically.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
        wallet_data = cursor.fetchone()
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet not found.")
        wallet_id, wallet_balance = wallet_data

        if wallet_balance <= 0:
            raise HTTPException(status_code=400, detail="Wallet balance is zero or negative. Nothing to apply.")

        cursor.execute("SELECT rent_outstanding, electricity_outstanding, water_outstanding FROM tenants WHERE id = %s FOR UPDATE", (tenant_id,))
        rent_owed, elec_owed, water_owed = cursor.fetchone()

        available_funds = Decimal(str(wallet_balance))
        
        rent_paid = Decimal('0')
        elec_paid = Decimal('0')
        water_paid = Decimal('0')

        if available_funds > 0 and rent_owed > 0:
            rent_paid = min(available_funds, rent_owed)
            available_funds -= rent_paid
            cursor.execute("UPDATE tenants SET rent_outstanding = rent_outstanding - %s WHERE id = %s", (rent_paid, tenant_id))

        if available_funds > 0 and elec_owed > 0:
            elec_paid = min(available_funds, elec_owed)
            available_funds -= elec_paid
            cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding - %s WHERE id = %s", (elec_paid, tenant_id))

        if available_funds > 0 and water_owed > 0:
            water_paid = min(available_funds, water_owed)
            available_funds -= water_paid
            cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding - %s WHERE id = %s", (water_paid, tenant_id))

        total_paid = rent_paid + elec_paid + water_paid
        new_wallet_balance = wallet_balance - total_paid
        cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_wallet_balance, wallet_id))

        idempotency_key = str(uuid.uuid4())
        if rent_paid > 0:
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, rent_paid, 'RENT_PAYMENT', 'Wallet Sweep - Rent', tenant_info[0], wallet_balance, new_wallet_balance, f"{idempotency_key}-RENT"))
            wallet_balance = new_wallet_balance 

        if elec_paid > 0:
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, elec_paid, 'ELECTRICITY_PAYMENT', 'Wallet Sweep - Electricity', tenant_info[0], wallet_balance, new_wallet_balance, f"{idempotency_key}-ELEC"))
            wallet_balance = new_wallet_balance

        if water_paid > 0:
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, water_paid, 'WATER_PAYMENT', 'Wallet Sweep - Water', tenant_info[0], wallet_balance, new_wallet_balance, f"{idempotency_key}-WATER"))

        conn.commit()
        return {
            "status": "success", 
            "message": f"Successfully applied R{total_paid:.2f} from wallet to arrears.",
            "new_wallet_balance": float(new_wallet_balance)
        }
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

        if current_user.get("role") == "TENANT":
            if current_user.get("tenant_id") != tenant_id:
                raise HTTPException(status_code=403, detail="Forbidden: You can only buy utilities for your own account.")

        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        idempotency_key = req.get("idempotency_key") or str(uuid.uuid4())
        cursor.execute("SELECT id FROM transactions WHERE idempotency_key = %s", (idempotency_key,))
        if cursor.fetchone():
            return {"status": "success", "message": "Purchase already processed."}

        cursor.execute("SELECT first_name, last_name, email, rent_outstanding FROM tenants WHERE id = %s FOR UPDATE", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email, rent_owed = tenant_data
        
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
        
        cursor.execute("SELECT id, balance, credit_limit FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id, current_balance, credit_limit = wallet_data
        
        available_funds = current_balance + (credit_limit or Decimal('0'))
        if available_funds < amount_decimal:
            raise HTTPException(status_code=400, detail=f"Insufficient funds. Balance: R{current_balance:.2f}, Credit: R{credit_limit or 0:.2f}.")
            
        new_balance = current_balance - amount_decimal
        cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
        
        token = None
        reference_text = ""
        units_purchased = Decimal('0')
        vat_amount = Decimal('0.00') # Initialize for safety
        
        cursor.execute("SELECT rate_flat FROM tariffs WHERE id = %s", (tariff_id,))
        tariff_data = cursor.fetchone()
        rate = Decimal(str(tariff_data[0])) if tariff_data and tariff_data[0] else Decimal('1.0')

        # Fetch Company VAT percentage
        cursor.execute("SELECT vat_percent FROM company WHERE id = 1")
        company_vat = cursor.fetchone()
        vat_percent = (Decimal(str(company_vat[0])) / Decimal(100)) if company_vat and company_vat[0] else Decimal('0.15')

        if hardware_type == 'STS':
            token = generate_token()
            
            # Calculate VAT and Net Amount for STS Electricity
            vat_amount = (amount_decimal / (Decimal('1') + vat_percent)) * vat_percent
            amount_ex_vat = amount_decimal - vat_amount
            
            # Calculate kWh using ex-VAT amount
            if rate > 0:
                units_purchased = amount_ex_vat / rate
                
            reference_text = f"Token: {token} | {units_purchased:.2f} kWh"
            
            # Create a multi-line message for the frontend alert
            message = (
                f"Purchase Successful!\n"
                f"Amount Paid: R{amount_decimal:.2f}\n"
                f"VAT ({int(vat_percent * 100)}%): R{vat_amount:.2f}\n"
                f"Net Energy: {units_purchased:.2f} kWh\n"
                f"Token: {token}"
            )
            
        elif hardware_type == 'SMART_IOT':
            if rate > 0:
                units_purchased = amount_decimal / rate
            cursor.execute("UPDATE meters SET meter_balance = meter_balance + %s WHERE id = %s", (units_purchased, meter_id))
            unit_name = "kWh" if utility_type == "ELECTRICITY" else "kL"
            reference_text = f"Smart Meter Top-up: {units_purchased:.2f} {unit_name}"
            message = f"Your smart meter has been credited with {units_purchased:.2f} {unit_name}."
            
        else:
            token = generate_token()
            vat_amount = (amount_decimal / (Decimal('1') + vat_percent)) * vat_percent
            amount_ex_vat = amount_decimal - vat_amount
            units_purchased = amount_ex_vat / rate if rate > 0 else Decimal('0')
            reference_text = f"Token: {token} | {units_purchased:.2f} kWh"
            message = f"Purchase Successful! Token: {token}"

        cursor.execute("""
            INSERT INTO transactions (wallet_id, amount, transaction_type, reference, idempotency_key, property_id, before_balance, after_balance) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (wallet_id, amount_decimal, f"{utility_type}_PURCHASE", reference_text, idempotency_key, tenant_info[0], current_balance, new_balance))
        
        if current_valve_status in ['TRICKLE', 'DISCONNECTED']:
            cursor.execute("UPDATE meters SET valve_status = 'OPEN' WHERE tenant_id = %s AND meter_type = %s", (tenant_id, utility_type))
            send_notification(f"{first_name} {last_name}", email, f"Your {utility_type} has been reconnected.")
        
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, message)
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
def api_set_credit_limit(tenant_id: int, limit: float, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        cursor.execute("UPDATE wallets SET credit_limit = %s WHERE tenant_id = %s", (Decimal(str(limit)), tenant_id))
        conn.commit()
        return {"status": "success", "message": f"Credit limit set to R{limit:.2f}."}
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
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id, current_balance = wallet_data
        
        amount_input = Decimal(str(req.get("amount")))
        target = req.get("target").upper()
        reason = req.get("reason")
        
        # Cap the adjustment amount to what is actually owed so we don't over-deduct from the wallet
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

            # Deduct from wallet
            new_balance = current_balance - amount_input
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
            
            # Clear the arrears
            if target == "RENT":
                cursor.execute("UPDATE tenants SET rent_outstanding = GREATEST(0, rent_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))
            elif target == "ELECTRICITY":
                cursor.execute("UPDATE tenants SET electricity_outstanding = GREATEST(0, electricity_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))
            elif target == "WATER":
                cursor.execute("UPDATE tenants SET water_outstanding = GREATEST(0, water_outstanding - %s) WHERE id = %s", (amount_input, tenant_id))

            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, -amount_input, f"ADJUSTMENT_{target}", reason, tenant_info[0], current_balance, new_balance))

        elif target == "WALLET":
            new_balance = current_balance + amount_input
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, amount_input, f"ADJUSTMENT_{target}", reason, tenant_info[0], current_balance, new_balance))
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
        if current_user.get("role") == "TENANT":
            if current_user.get("tenant_id") != tenant_id:
                raise HTTPException(status_code=403, detail="Forbidden: You can only view your own transactions.")

        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        wallet_id = wallet_data[0]
        
        cursor.execute("""
            SELECT created_at, amount, transaction_type, reference 
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
                "reference": row[3]
            })
        return {"status": "success", "transactions": txns_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/restrict-water/{tenant_id}")
def api_restrict_water(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

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
def api_unrestrict_water(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

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
def api_admin_reset_wallet(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        tenant_info = cursor.fetchone()
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant not found")
        enforce_property_access(current_user, tenant_info[0])

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