from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.schemas import InvoiceGenerateRequest
from api.security import verify_token
from decimal import Decimal
import datetime

router = APIRouter()

@router.post("/generate-invoice/", dependencies=[Depends(verify_token)])
def api_generate_invoice(req: InvoiceGenerateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTOMATIC SCHEMA FIX FOR INVOICES ---
        cursor.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS billing_period VARCHAR(20);")
        cursor.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS cycle_type VARCHAR(20);")
        cursor.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_amount DECIMAL DEFAULT 0;")
        cursor.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'UNPAID';")
        
        # Ensure invoice_items table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER,
                description TEXT,
                quantity DECIMAL,
                unit_price DECIMAL,
                total DECIMAL,
                drill_down TEXT
            );
        """)
        conn.commit()

        # 1. Get Tenant Info & Arrears
        cursor.execute("SELECT first_name, last_name, rent_outstanding, electricity_outstanding, water_outstanding FROM tenants WHERE id = %s", (req.tenant_id,))
        tenant = cursor.fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        rent_due, elec_due, water_due = Decimal(str(tenant[2])), Decimal(str(tenant[3])), Decimal(str(tenant[4]))
        total_amount = rent_due + elec_due + water_due
        
        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Tenant has no outstanding arrears to invoice.")
            
        # 2. Create Invoice Header
        cursor.execute("""
            INSERT INTO invoices (tenant_id, billing_period, total_amount, status) 
            VALUES (%s, %s, %s, 'DUE') RETURNING id
        """, (req.tenant_id, req.billing_period, total_amount))
        invoice_id = cursor.fetchone()[0]
        
        # 3. Create Line Items with Drill-Down details
        if rent_due > 0:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, f"Rent ({req.cycle_type})", 1, rent_due, rent_due, f"Property rent for period {req.billing_period}"))
            
        if elec_due > 0:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, "Electricity Charges", 1, elec_due, elec_due, f"Total electricity usage and arrears for period {req.billing_period}"))
            
        if water_due > 0:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, "Water Charges (Hot/Cold)", 1, water_due, water_due, f"Total water usage and arrears for period {req.billing_period}"))
            
        conn.commit()
        return {"status": "success", "message": "Invoice generated successfully!", "invoice_id": invoice_id, "total": float(total_amount)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/invoices/", dependencies=[Depends(verify_token)])
def api_get_invoices():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- AUTOMATIC SCHEMA FIX ---
        cursor.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_amount DECIMAL DEFAULT 0;")
        conn.commit()

        cursor.execute("""
            SELECT i.id, t.first_name, t.last_name, i.billing_period, i.total_amount, i.status, i.created_at 
            FROM invoices i 
            JOIN tenants t ON i.tenant_id = t.id 
            ORDER BY i.created_at DESC
        """)
        rows = cursor.fetchall()
        inv_list = []
        for row in rows:
            inv_list.append({
                "id": row[0], "tenant_name": f"{row[1]} {row[2]}",
                "period": row[3], "total": float(row[4] or 0), "status": row[5],
                "date": row[6].strftime("%Y-%m-%d")
            })
        return {"status": "success", "invoices": inv_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/invoice/{invoice_id}", dependencies=[Depends(verify_token)])
def api_view_invoice(invoice_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT i.id, t.first_name, t.last_name, t.email, i.billing_period, i.total_amount, i.status, i.created_at 
            FROM invoices i 
            JOIN tenants t ON i.tenant_id = t.id 
            WHERE i.id = %s
        """, (invoice_id,))
        inv = cursor.fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        cursor.execute("SELECT description, quantity, unit_price, total, drill_down FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
        items = cursor.fetchall()
        
        items_list = []
        for row in items:
            items_list.append({
                "description": row[0], "quantity": float(row[1]),
                "unit_price": float(row[2]), "total": float(row[3]),
                "drill_down": row[4]
            })
            
        return {
            "id": inv[0], "tenant_name": f"{inv[1]} {inv[2]}", "email": inv[3],
            "period": inv[4], "total": float(inv[5] or 0), "status": inv[6],
            "date": inv[7].strftime("%Y-%m-%d"), "items": items_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()