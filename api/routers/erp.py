from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from api.services.notifications import send_notification
from decimal import Decimal
import uuid

router = APIRouter()

def process_rent_sync_for_tenant(cursor, tenant_id: int, amount_to_add: Decimal):
    """Helper to add rent and sweep wallet for a single tenant."""
    # Lock tenant
    cursor.execute("SELECT rent_outstanding FROM tenants WHERE id = %s FOR UPDATE", (tenant_id,))
    tenant_data = cursor.fetchone()
    if not tenant_data:
        return
        
    current_rent = Decimal(tenant_data[0])
    new_rent_total = current_rent + amount_to_add
    cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (new_rent_total, tenant_id))
    
    # Lock wallet
    cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
    wallet_data = cursor.fetchone()
    
    if wallet_data:
        wallet_id, wallet_balance = wallet_data
        if wallet_balance > 0:
            payment = min(wallet_balance, new_rent_total)
            final_wallet_balance = wallet_balance - payment
            final_rent_balance = new_rent_total - payment
            
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (final_wallet_balance, wallet_id))
            cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (final_rent_balance, tenant_id))
            
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference, before_balance, after_balance, idempotency_key) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (wallet_id, payment, 'RENT_PAYMENT', 'Mock Rent Sync Auto-Deduct', wallet_balance, final_wallet_balance, str(uuid.uuid4())))

# 1. THIS IS THE WEBHOOK: For the external ERP system
@router.post("/erp-webhook/rent-update")
def receive_rent_update_from_erp(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tenant_id = payload.get("tenant_id")
        erp_rent_owed = Decimal(str(payload.get("rent_outstanding", 0.0)))
        
        process_rent_sync_for_tenant(cursor, tenant_id, erp_rent_owed)
        conn.commit()
        return {"status": "success", "message": "Rent synced from ERP."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# 2. GLOBAL SYNC: Simulates ERP sending rent bills to ALL tenants
@router.post("/trigger-mock-rent", dependencies=[Depends(verify_token)])
@router.post("/trigger-mock-rent/", dependencies=[Depends(verify_token)])
def trigger_mock_rent_all():
    print("--- MOCK RENT SYNC TRIGGERED FOR ALL TENANTS ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM tenants WHERE status = 'ACTIVE'")
        tenants = cursor.fetchall()
        
        for t in tenants:
            tenant_id = t[0]
            try:
                process_rent_sync_for_tenant(cursor, tenant_id, Decimal('4500.00'))
            except Exception as e:
                print(f"Error syncing tenant {tenant_id}: {e}")
                conn.rollback()
                
        conn.commit()
        print(f"--- SYNC COMPLETE. Processed {len(tenants)} tenants. ---")
        return {"status": "success", "message": "Mock rent bill added to all tenants. Wallets auto-deducted."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# 3. SINGLE TENANT SYNC: Simulates ERP sending rent bill to ONE tenant
@router.post("/trigger-mock-rent/{tenant_id}", dependencies=[Depends(verify_token)])
def trigger_mock_rent_single(tenant_id: int):
    print(f"--- MOCK RENT SYNC TRIGGERED FOR TENANT {tenant_id} ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        process_rent_sync_for_tenant(cursor, tenant_id, Decimal('4500.00'))
        conn.commit()
        return {"status": "success", "message": "Mock rent bill added. Wallet auto-deducted."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()