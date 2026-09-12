from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from api.database import get_db_connection
from api.schemas import TenantRequest, MeterRequest, MeterUpdateRequest, TenantUpdateRequest, ExitFormRequest, InspectionResultRequest
from api.security import verify_token, enforce_property_access, require_staff
from api.services.notifications import send_notification
import datetime
import os
import random
from decimal import Decimal

router = APIRouter()

# --- Helper Function for Authorization ---
def check_tenant_access(cursor, tenant_id: int, current_user: dict):
    """Fetches a tenant's property_id/status and authorizes the current user against it."""
    cursor.execute("SELECT property_id, status FROM tenants WHERE id = %s", (tenant_id,))
    tenant_info = cursor.fetchone()
    if not tenant_info:
        raise HTTPException(status_code=404, detail="Tenant not found")
    target_property_id, target_status = tenant_info

    role = current_user.get("role")
    if role == "TENANT":
        if current_user.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=403, detail="Forbidden: you can only access your own tenant account.")
        if target_status == "VACATED":
            raise HTTPException(status_code=401, detail="This tenant account has been vacated. Please contact your property manager.")
    else:
        enforce_property_access(current_user, target_property_id)

    return target_property_id

# --- Tenant Endpoints ---

@router.post("/create-tenant/")
def api_create_tenant(payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        property_id = payload.get("property_id")
        enforce_property_access(current_user, property_id)

        first_name = payload.get("first_name")
        last_name = payload.get("last_name")
        email = payload.get("email")
        cellphone = payload.get("cellphone")
        rent_outstanding = payload.get("rent_outstanding", 0)
        electricity_outstanding = payload.get("electricity_outstanding", 0)
        water_outstanding = payload.get("water_outstanding", 0)
        unit_number = payload.get("unit_number")
        
        if unit_number and property_id:
            cursor.execute("SELECT id FROM tenants WHERE unit_number = %s AND property_id = %s AND status = 'ACTIVE'", (unit_number, property_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Unit {unit_number} is currently occupied by an active tenant.")
        
        if email and property_id:
            cursor.execute("SELECT id FROM tenants WHERE email = %s AND property_id = %s AND status = 'ACTIVE'", (email, property_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Email {email} is already registered to an active tenant at this property.")
        
        cursor.execute("""
            INSERT INTO tenants (first_name, last_name, email, cellphone, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (first_name, last_name, email, cellphone, rent_outstanding, electricity_outstanding, water_outstanding, property_id, unit_number))
        new_tenant_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 0.00)", (new_tenant_id,))
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, cellphone, "Welcome to the Utilities Platform!")
        return {"status": "success", "message": "Tenant created successfully!", "tenant_id": new_tenant_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/grant-consent/{tenant_id}")
def api_grant_consent(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("UPDATE tenants SET popia_consent = TRUE WHERE id = %s", (tenant_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tenant not found")
        conn.commit()
        return {"status": "success", "message": "POPIA consent granted successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/anonymize-tenant/{tenant_id}")
def api_anonymize_tenant(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("""
            UPDATE tenants 
            SET first_name = 'ANONYMIZED', 
                last_name = 'TENANT', 
                email = 'anonymized@redacted.com',
                cellphone = '0000000000', 
                is_anonymized = TRUE 
            WHERE id = %s
        """, (tenant_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tenant not found")
        conn.commit()
        return {"status": "success", "message": "Tenant data anonymized successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/credit-check/{tenant_id}")
def api_credit_check(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        
        cursor.execute("SELECT first_name, last_name, email, popia_consent FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email, consent = tenant_data

        if not consent:
            raise HTTPException(status_code=403, detail="POPIA Violation: Cannot perform credit check without explicit tenant consent.")

        score = random.randint(300, 850)
        if score >= 650:
            status = "CLEAR"
        elif score >= 550:
            status = "MEDIUM RISK"
        else:
            status = "HIGH RISK"
            
        cursor.execute("UPDATE tenants SET credit_status = %s, credit_score = %s WHERE id = %s", (status, score, tenant_id))
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, None, f"Credit check completed. Status: {status} (Score: {score}).")
        return {"status": "success", "message": f"Credit check completed.", "credit_status": status, "credit_score": score}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/lease-reminder/{tenant_id}")
def api_lease_reminder(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("SELECT first_name, last_name, email, lease_expiry_date FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email, lease_date = tenant_data
        
        if not lease_date:
            raise HTTPException(status_code=400, detail="Tenant has no lease expiry date set.")
            
        send_notification(f"{first_name} {last_name}", email, None, f"Lease Expiry Reminder: Your lease expires on {lease_date}.", subject="Lease Expiry Reminder")
        return {"status": "success", "message": "Lease expiry reminder sent."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/notice-to-vacate/{tenant_id}")
def api_notice_to_vacate(tenant_id: int, req: ExitFormRequest, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email = tenant_data
        
        cursor.execute("""
            UPDATE tenants 
            SET exit_date = %s, exit_reason = %s, inspection_status = 'PENDING_INSPECTION', status = 'PENDING_EXIT'
            WHERE id = %s
        """, (req.exit_date, req.exit_reason, tenant_id))
        conn.commit()
        
        send_notification(f"{first_name} {last_name}", email, None, f"Notice to Vacate received. Exit scheduled for {req.exit_date}.")
        
        return {"status": "success", "message": "Notice to Vacate submitted. PM notified for inspection."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/inspection-result/{tenant_id}")
def api_inspection_result(tenant_id: int, req: InspectionResultRequest, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        first_name, last_name, email = tenant_data
        
        cursor.execute("""
            UPDATE tenants 
            SET inspection_status = %s, inspection_notes = %s
            WHERE id = %s
        """, (req.status.upper(), req.notes, tenant_id))
        
        if req.status.upper() == "PASSED":
            cursor.execute("UPDATE tenants SET status = 'VACATED', vacated_at = CURRENT_TIMESTAMP WHERE id = %s", (tenant_id,))
            # --- AUTOMATIC METER FREEING ---
            cursor.execute("UPDATE meters SET is_active = FALSE, tenant_id = NULL WHERE tenant_id = %s", (tenant_id,))
            send_notification(f"{first_name} {last_name}", email, None, "Inspection passed. Account officially closed. Goodbye!")
        
        conn.commit()
        return {"status": "success", "message": f"Inspection result recorded. Status: {req.status.upper()}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.put("/update-tenant/{tenant_id}")
def api_update_tenant(tenant_id: int, tenant: TenantUpdateRequest, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        prop_id = check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Tenant wallet not found.")
        wallet_id = wallet_data[0]

        cursor.execute("SELECT COUNT(*) FROM transactions WHERE wallet_id = %s", (wallet_id,))
        txn_count = cursor.fetchone()[0]

        cursor.execute("SELECT first_name, last_name, email, cellphone, status FROM tenants WHERE id = %s", (tenant_id,))
        current_data = cursor.fetchone()
        
        curr_first, curr_last, curr_email, curr_cell, curr_status = current_data

        if txn_count > 0:
            if tenant.first_name != curr_first or tenant.last_name != curr_last:
                raise HTTPException(status_code=400, detail="Cannot change Tenant Name once billing information exists.")
        
        if tenant.email != curr_email:
            cursor.execute("SELECT id FROM tenants WHERE email = %s AND property_id = %s AND status = 'ACTIVE' AND id != %s", (tenant.email, prop_id, tenant_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Email {tenant.email} is already registered to an active tenant at this property.")

            cursor.execute("SELECT previous_emails FROM tenants WHERE id = %s", (tenant_id,))
            prev_log = cursor.fetchone()[0] or ""
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_log_entry = f"{curr_email} (changed on {timestamp}); "
            updated_log = prev_log + new_log_entry
            cursor.execute("UPDATE tenants SET email = %s, previous_emails = %s WHERE id = %s", (tenant.email, updated_log, tenant_id))

        # Update cellphone
        if tenant.cellphone != curr_cell:
             cursor.execute("UPDATE tenants SET cellphone = %s WHERE id = %s", (tenant.cellphone, tenant_id))

        if txn_count == 0:
            cursor.execute("UPDATE tenants SET first_name = %s, last_name = %s WHERE id = %s", (tenant.first_name, tenant.last_name, tenant_id))
        
        new_status = tenant.status.upper()
        if new_status != curr_status:
            if new_status == 'SUSPENDED':
                cursor.execute("UPDATE tenants SET status = 'SUSPENDED', suspended_at = CURRENT_TIMESTAMP, vacated_at = NULL WHERE id = %s", (tenant_id,))
                cursor.execute("UPDATE meters SET is_active = FALSE WHERE tenant_id = %s", (tenant_id,))
            elif new_status == 'VACATED':
                cursor.execute("UPDATE tenants SET status = 'VACATED', vacated_at = CURRENT_TIMESTAMP, suspended_at = NULL WHERE id = %s", (tenant_id,))
                # --- AUTOMATIC METER FREEING ---
                cursor.execute("UPDATE meters SET is_active = FALSE, tenant_id = NULL WHERE tenant_id = %s", (tenant_id,))
            elif new_status == 'ACTIVE':
                cursor.execute("UPDATE tenants SET status = 'ACTIVE', suspended_at = NULL, vacated_at = NULL WHERE id = %s", (tenant_id,))
        else:
            cursor.execute("UPDATE tenants SET status = %s WHERE id = %s", (new_status, tenant_id))
            
        conn.commit()
        return {"status": "success", "message": f"Tenant {tenant_id} updated successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/suspend-tenant/{tenant_id}")
def api_suspend_tenant(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("UPDATE tenants SET status = 'SUSPENDED', suspended_at = CURRENT_TIMESTAMP, vacated_at = NULL WHERE id = %s", (tenant_id,))
        cursor.execute("UPDATE meters SET is_active = FALSE WHERE tenant_id = %s", (tenant_id,))
        conn.commit()
        return {"status": "success", "message": f"Tenant {tenant_id} has been suspended. Meters deactivated."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/vacate-tenant/{tenant_id}")
def api_vacate_tenant(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("UPDATE tenants SET status = 'VACATED', vacated_at = CURRENT_TIMESTAMP, suspended_at = NULL WHERE id = %s", (tenant_id,))
        # --- AUTOMATIC METER FREEING (PRODUCTION SAFE) ---
        cursor.execute("UPDATE meters SET is_active = FALSE, tenant_id = NULL WHERE tenant_id = %s", (tenant_id,))
        conn.commit()
        return {"status": "success", "message": f"Tenant {tenant_id} has been vacated. Meters freed for reassignment."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/tenant-balance/{tenant_id}")
def api_get_tenant_balance(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        
        # --- AUTOMATIC SCHEMA FIX ---
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_limit DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_balance DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_debt DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_taps_used INT DEFAULT 0;")
        cursor.execute("ALTER TABLE wallets ADD COLUMN IF NOT EXISTS credit_reset_month VARCHAR(7);")
        cursor.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS cellphone VARCHAR(20);")
        conn.commit()

        cursor.execute("""
            SELECT t.first_name, t.last_name, t.cellphone, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding, t.property_id, p.utility_model 
            FROM tenants t 
            LEFT JOIN properties p ON t.property_id = p.id 
            WHERE t.id = %s
        """, (tenant_id,))
        tenant_data = cursor.fetchone()
            
        first_name, last_name, cellphone, rent_owed, elec_owed, water_owed, prop_id, utility_model = tenant_data
        if not utility_model:
            utility_model = "STS_TOKEN"
            
        cursor.execute("SELECT balance, credit_limit, credit_balance, credit_taps_used FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT id, meter_type, serial_number, billing_type, meter_balance, hardware_type 
            FROM meters 
            WHERE tenant_id = %s AND is_active = TRUE
        """, (tenant_id,))
        meters_data = cursor.fetchall()
        
        elec_balance_kwh = 0
        water_balance_kl = 0
        assigned_meters = []
        
        for m in meters_data:
            m_id, m_type, m_serial, m_billing, m_balance, m_hardware = m
            assigned_meters.append({
                "meter_id": m_id,
                "meter_type": m_type,
                "serial_number": m_serial,
                "billing_type": m_billing,
                "balance": float(m_balance or 0),
                "hardware_type": m_hardware
            })
            if m_type == 'ELECTRICITY' and m_hardware == 'SMART_IOT':
                elec_balance_kwh = float(m_balance)
            elif m_type.startswith('WATER') and m_hardware == 'SMART_IOT':
                water_balance_kl = float(m_balance)

        credit_limit = wallet_data[1] if wallet_data[1] is not None else 0
        tap_size = (Decimal(str(credit_limit)) / Decimal(3)).quantize(Decimal('0.01')) if credit_limit > 0 else 0

        return {
            "tenant_name": f"{first_name} {last_name}",
            "cellphone": cellphone or "Not set",
            "rent_outstanding": float(rent_owed),
            "electricity_outstanding": float(elec_owed),
            "water_outstanding": float(water_owed),
            "wallet_balance": float(wallet_data[0]),
            "credit_limit": float(credit_limit),
            "credit_balance": float(wallet_data[2] if wallet_data[2] is not None else 0),
            "credit_taps_used": wallet_data[3] if wallet_data[3] is not None else 0,
            "tap_size": float(tap_size),
            "elec_meter_balance_kwh": elec_balance_kwh,
            "water_meter_balance_kl": water_balance_kl,
            "utility_model": utility_model,
            "property_id": prop_id,
            "assigned_meters": assigned_meters
        }
    finally:
        cursor.close()
        conn.close()

@router.get("/tenant-statement/{tenant_id}")
def api_get_tenant_statement(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("SELECT first_name, last_name, email, rent_outstanding, electricity_outstanding, water_outstanding, status FROM tenants WHERE id = %s", (tenant_id,))
        t = cursor.fetchone()
            
        cursor.execute("SELECT id, balance, credit_limit FROM wallets WHERE tenant_id = %s", (tenant_id,))
        w = cursor.fetchone()
        wallet_id = w[0]
        
        cursor.execute("""
            SELECT created_at, amount, transaction_type, reference 
            FROM transactions 
            WHERE wallet_id = %s 
            ORDER BY created_at DESC 
            LIMIT 15
        """, (wallet_id,))
        txns = cursor.fetchall()
        
        txns_list = []
        for row in txns:
            txns_list.append({
                "date": row[0].strftime("%Y-%m-%d %H:%M"),
                "amount": float(row[1]),
                "type": row[2],
                "reference": row[3]
            })
            
        total_arrears = float(t[3]) + float(t[4]) + float(t[5])
        
        return {
            "tenant_name": f"{t[0]} {t[1]}",
            "email": t[2],
            "status": t[6],
            "rent_outstanding": float(t[3]),
            "electricity_outstanding": float(t[4]),
            "water_outstanding": float(t[5]),
            "total_arrears": total_arrears,
            "wallet_balance": float(w[1]),
            "credit_limit": float(w[2] if w[2] is not None else 0),
            "transactions": txns_list
        }
    finally:
        cursor.close()
        conn.close()

@router.get("/all-tenants/")
def api_get_all_tenants(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        user_role = current_user.get("role")
        user_prop_id = current_user.get("property_id")

        target_property_id = None
        if user_role == "ADMIN":
            if property_id is not None and property_id > 0:
                target_property_id = property_id
        else:
            target_property_id = user_prop_id

        if target_property_id:
            cursor.execute("UPDATE tenants SET property_id = %s WHERE property_id IS NULL", (target_property_id,))
            cursor.execute("UPDATE meters SET property_id = %s WHERE property_id IS NULL AND tenant_id IN (SELECT id FROM tenants WHERE property_id = %s)", (target_property_id, target_property_id))
            conn.commit()
        elif user_role == "ADMIN" and not property_id:
            cursor.execute("SELECT COUNT(*) FROM properties")
            if cursor.fetchone()[0] == 1:
                cursor.execute("SELECT id FROM properties LIMIT 1")
                single_prop_id = cursor.fetchone()[0]
                cursor.execute("UPDATE tenants SET property_id = %s WHERE property_id IS NULL", (single_prop_id,))
                cursor.execute("UPDATE meters SET property_id = %s WHERE property_id IS NULL", (single_prop_id,))
                conn.commit()

        if target_property_id:
            cursor.execute("""
                SELECT t.id, t.unit_number, t.first_name, t.last_name, t.email, t.cellphone, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding, w.balance, w.credit_limit, t.status, t.suspended_at, t.vacated_at, t.credit_status, t.credit_score, t.inspection_status, t.popia_consent, t.is_anonymized, t.lease_expiry_date, t.property_id, p.name
                FROM tenants t 
                JOIN wallets w ON t.id = w.tenant_id 
                LEFT JOIN properties p ON t.property_id = p.id
                WHERE t.property_id = %s
                ORDER BY t.id ASC
            """, (target_property_id,))
        else:
            cursor.execute("""
                SELECT t.id, t.unit_number, t.first_name, t.last_name, t.email, t.cellphone, t.rent_outstanding, t.electricity_outstanding, t.water_outstanding, w.balance, w.credit_limit, t.status, t.suspended_at, t.vacated_at, t.credit_status, t.credit_score, t.inspection_status, t.popia_consent, t.is_anonymized, t.lease_expiry_date, t.property_id, p.name
                FROM tenants t 
                JOIN wallets w ON t.id = w.tenant_id 
                LEFT JOIN properties p ON t.property_id = p.id
                ORDER BY t.id ASC
            """)

        rows = cursor.fetchall()
        tenants_list = []
        for row in rows:
            tenants_list.append({
                "tenant_id": row[0], "unit_number": row[1], "first_name": row[2], "last_name": row[3], "email": row[4],
                "cellphone": row[5] or "",
                "rent_outstanding": float(row[6]), "electricity_outstanding": float(row[7]),
                "water_outstanding": float(row[8]), "wallet_balance": float(row[9]),
                "credit_limit": float(row[10] if row[10] is not None else 0),
                "status": row[11],
                "suspended_at": row[12].strftime("%Y-%m-%d %H:%M") if row[12] else None,
                "vacated_at": row[13].strftime("%Y-%m-%d %H:%M") if row[13] else None,
                "credit_status": row[14], "credit_score": row[15],
                "inspection_status": row[16],
                "popia_consent": row[17],
                "is_anonymized": row[18],
                "lease_expiry_date": row[19].strftime("%Y-%m-%d") if row[19] else None,
                "property_id": row[20],
                "property_name": row[21] if row[21] else "Unassigned"
            })
        return {"status": "success", "tenants": tenants_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# --- Document Endpoints ---

@router.post("/upload-doc/{tenant_id}")
async def api_upload_doc(tenant_id: int, doc_type: str = Form(...), file: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        folder_path = f"uploads/{tenant_id}"
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        cursor.execute("""
            INSERT INTO documents (tenant_id, doc_type, file_path) 
            VALUES (%s, %s, %s) RETURNING id
        """, (tenant_id, doc_type.upper(), file_path))
        doc_id = cursor.fetchone()[0]
        conn.commit()
        
        return {"status": "success", "message": f"{doc_type} uploaded successfully!", "doc_id": doc_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/get-docs/{tenant_id}")
def api_get_docs(tenant_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_tenant_access(cursor, tenant_id, current_user)
        cursor.execute("""
            SELECT id, doc_type, file_path, uploaded_at 
            FROM documents 
            WHERE tenant_id = %s 
            ORDER BY uploaded_at DESC
        """, (tenant_id,))
        rows = cursor.fetchall()
        docs_list = []
        for row in rows:
            docs_list.append({
                "doc_id": row[0], "doc_type": row[1], 
                "file_name": os.path.basename(row[2]),
                "uploaded_at": row[3].strftime("%Y-%m-%d %H:%M:%S")
            })
        return {"status": "success", "documents": docs_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# --- Meter Endpoints ---

@router.get("/available-meters/")
def api_get_available_meters(current_user: dict = Depends(verify_token)):
    """Fetches meters that are vacant (tenant_id IS NULL) so PMs can reassign them easily."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        user_role = current_user.get("role")
        user_prop_id = current_user.get("property_id")

        query = """
            SELECT id, serial_number, meter_type, billing_type, tariff_id 
            FROM meters 
            WHERE tenant_id IS NULL AND is_active = FALSE
        """
        params = []
        if user_role != "ADMIN" and user_prop_id:
            query += " AND property_id = %s"
            params.append(user_prop_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        meters_list = []
        for row in rows:
            meters_list.append({
                "id": row[0],
                "serial_number": row[1],
                "meter_type": row[2],
                "billing_type": row[3],
                "tariff_id": row[4]
            })
        return {"status": "success", "meters": meters_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/assign-meter/")
def api_assign_meter(payload: dict, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tenant_id = payload.get("tenant_id")
        prop_id = check_tenant_access(cursor, tenant_id, current_user)

        cursor.execute("SELECT status, unit_number FROM tenants WHERE id = %s", (tenant_id,))
        tenant_status_row = cursor.fetchone()
        if not tenant_status_row or tenant_status_row[0] != 'ACTIVE':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot assign a meter to tenant {tenant_id}: tenant status is "
                       f"'{tenant_status_row[0] if tenant_status_row else 'UNKNOWN'}', not ACTIVE. "
                       f"If this unit was re-let, make sure the current tenant record is selected."
            )

        meter_type = payload.get("meter_type").upper()
        serial_number = payload.get("serial_number")
        billing_type = payload.get("billing_type").upper()

        # --- AUTO-FETCH TARIFF ---
        cursor.execute("SELECT id FROM tariffs WHERE property_id = %s AND meter_type = %s", (prop_id, meter_type))
        tariff_data = cursor.fetchone()
        if not tariff_data:
            raise HTTPException(status_code=400, detail=f"No {meter_type} tariff configured for this property. Please create a tariff first.")
        tariff_id = tariff_data[0]

        cursor.execute("""
            SELECT id FROM meters 
            WHERE tenant_id = %s AND meter_type = %s AND is_active = TRUE
        """, (tenant_id, meter_type))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Tenant already has an active {meter_type} meter. Deactivate the existing one first if you need to replace it.")

        cursor.execute("""
            SELECT id FROM meters 
            WHERE serial_number = %s AND property_id = %s
        """, (serial_number, prop_id))
        existing_meter = cursor.fetchone()

        if existing_meter:
            meter_id = existing_meter[0]
            cursor.execute("""
                UPDATE meters 
                SET tenant_id = %s, tariff_id = %s, billing_type = %s, is_active = TRUE, valve_status = 'OPEN' 
                WHERE id = %s
            """, (tenant_id, tariff_id, billing_type, meter_id))
        else:
            cursor.execute("""
                INSERT INTO meters (tenant_id, meter_type, billing_type, serial_number, tariff_id, property_id) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (tenant_id, meter_type, billing_type, serial_number, tariff_id, prop_id))
            meter_id = cursor.fetchone()[0]

        conn.commit()
        return {"status": "success", "message": f"{meter_type} meter assigned successfully!", "meter_id": meter_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.put("/update-meter/{meter_id}")
def api_update_meter(meter_id: int, meter: MeterUpdateRequest, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT tenant_id FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        if meter_data[0]:
            check_tenant_access(cursor, meter_data[0], current_user)

        cursor.execute("""
            UPDATE meters 
            SET meter_type = %s, billing_type = %s, serial_number = %s, tariff_id = %s 
            WHERE id = %s
        """, (meter.meter_type.upper(), meter.billing_type.upper(), meter.serial_number, meter.tariff_id, meter_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Meter not found.")
        conn.commit()
        return {"status": "success", "message": f"Meter {meter_id} updated successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/all-meters/")
def api_get_all_meters(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        user_role = current_user.get("role")
        user_prop_id = current_user.get("property_id")

        target_property_id = None
        if user_role == "ADMIN":
            if property_id is not None and property_id > 0:
                target_property_id = property_id
        else:
            target_property_id = user_prop_id

        if target_property_id:
            cursor.execute("""
                SELECT m.id, t.first_name, t.last_name, m.meter_type, m.billing_type, m.serial_number, m.valve_status, m.is_active, m.tariff_id, m.property_id, p.name
                FROM meters m
                LEFT JOIN tenants t ON m.tenant_id = t.id
                LEFT JOIN properties p ON m.property_id = p.id
                WHERE m.property_id = %s
                ORDER BY m.id ASC
            """, (target_property_id,))
        else:
            cursor.execute("""
                SELECT m.id, t.first_name, t.last_name, m.meter_type, m.billing_type, m.serial_number, m.valve_status, m.is_active, m.tariff_id, m.property_id, p.name
                FROM meters m
                LEFT JOIN tenants t ON m.tenant_id = t.id
                LEFT JOIN properties p ON m.property_id = p.id
                ORDER BY m.id ASC
            """)

        rows = cursor.fetchall()
        meters_list = []
        for row in rows:
            meters_list.append({
                "meter_id": row[0], "tenant_name": f"{row[1] or 'Vacant'} {row[2] or ''}".strip(),
                "meter_type": row[3], "billing_type": row[4], "serial_number": row[5],
                "valve_status": row[6], "is_active": row[7], "tariff_id": row[8],
                "property_id": row[9],
                "property_name": row[10] if row[10] else "Unassigned"
            })
        return {"status": "success", "meters": meters_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/deactivate-meter/{meter_id}")
def api_deactivate_meter(meter_id: int, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT tenant_id FROM meters WHERE id = %s", (meter_id,))
        meter_data = cursor.fetchone()
        if not meter_data:
            raise HTTPException(status_code=404, detail="Meter not found.")
        if meter_data[0]:
            check_tenant_access(cursor, meter_data[0], current_user)

        cursor.execute("UPDATE meters SET is_active = FALSE WHERE id = %s", (meter_id,))
        conn.commit()
        return {"status": "success", "message": f"Meter {meter_id} deactivated successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()