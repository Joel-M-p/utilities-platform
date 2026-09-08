from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from decimal import Decimal
import datetime

router = APIRouter()

@router.post("/generate-invoice/", dependencies=[Depends(verify_token)])
def api_generate_invoice(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tenant_id = payload.get("tenant_id")
        billing_period = payload.get("billing_period")
        cycle_type = payload.get("cycle_type", "MONTHLY")

        cursor.execute("SELECT id, first_name, last_name, email, property_id, rent_outstanding, electricity_outstanding, water_outstanding FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cursor.fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        t_id, f_name, l_name, email, prop_id, rent_owed, elec_owed, water_owed = tenant
        
        # Check for existing invoice this period
        cursor.execute("SELECT id FROM invoices WHERE tenant_id = %s AND billing_period = %s", (tenant_id, billing_period))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Invoice for period {billing_period} already exists.")

        # --- Calculate Line Items ---
        items = []
        subtotal = Decimal('0.00')

        # 1. Rent Arrears (if any)
        if rent_owed > 0:
            items.append({"description": "Rent Arrears", "quantity": 1, "unit_price": float(rent_owed), "total": float(rent_owed), "drill_down": "Outstanding rent from previous periods."})
            subtotal += rent_owed

        # 2. Electricity Arrears (if any)
        if elec_owed > 0:
            items.append({"description": "Electricity Arrears", "quantity": 1, "unit_price": float(elec_owed), "total": float(elec_owed), "drill_down": "Outstanding electricity balance."})
            subtotal += elec_owed

        # 3. Water Arrears (if any)
        if water_owed > 0:
            items.append({"description": "Water/Municipal Arrears", "quantity": 1, "unit_price": float(water_owed), "total": float(water_owed), "drill_down": "Outstanding water balance."})
            subtotal += water_owed

        # 4. Sanitation Charge (Property-level, calculated daily)
        if prop_id:
            cursor.execute("SELECT id, rate_flat, name FROM tariffs WHERE property_id = %s AND meter_type = 'SANITATION'", (prop_id,))
            sani_data = cursor.fetchone()
            if sani_data:
                sani_id, sani_rate, sani_name = sani_data
                # Calculate days in month for daily charge
                year, month = map(int, billing_period.split('-'))
                import calendar
                days_in_month = calendar.monthrange(year, month)[1]
                
                sani_charge = Decimal(str(sani_rate)) * Decimal(str(days_in_month))
                items.append({"description": f"{sani_name} ({days_in_month} days)", "quantity": days_in_month, "unit_price": float(sani_rate), "total": float(sani_charge), "drill_down": "Fixed daily availability charge."})
                subtotal += sani_charge

        if subtotal == 0:
            raise HTTPException(status_code=400, detail="Tenant has no outstanding arrears or property charges to invoice.")

        # Calculate VAT (using Company Settings)
        cursor.execute("SELECT vat_percent FROM company WHERE id = 1")
        comp_data = cursor.fetchone()
        vat_rate = Decimal(str(comp_data[0])) if comp_data and comp_data[0] else Decimal('15.0')
        
        vat_amount = (subtotal * vat_rate) / Decimal('100')
        total_due = subtotal + vat_amount

        # Save Invoice
        cursor.execute("""
            INSERT INTO invoices (tenant_id, billing_period, cycle_type, total, status, date, period)
            VALUES (%s, %s, %s, %s, 'UNPAID', CURRENT_DATE, %s) RETURNING id
        """, (tenant_id, billing_period, cycle_type, float(total_due), billing_period))
        inv_id = cursor.fetchone()[0]

        # Save Line Items (Assuming an invoice_items table exists, or saving as JSON)
        # For simplicity, we'll create the items table if it doesn't exist and insert them
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER REFERENCES invoices(id),
                description TEXT,
                quantity DECIMAL,
                unit_price DECIMAL,
                total DECIMAL,
                drill_down TEXT
            );
        """)
        
        for item in items:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (inv_id, item['description'], item['quantity'], item['unit_price'], item['total'], item.get('drill_down', '')))

        conn.commit()

        return {
            "status": "success", 
            "message": "Invoice generated successfully!", 
            "invoice_id": inv_id,
            "subtotal": float(subtotal),
            "vat": float(vat_amount),
            "total": float(total_due),
            "items": items
        }

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
        cursor.execute("SELECT i.id, t.first_name, t.last_name, i.billing_period, i.total, i.status FROM invoices i JOIN tenants t ON i.tenant_id = t.id ORDER BY i.id DESC")
        rows = cursor.fetchall()
        inv_list = []
        for r in rows:
            inv_list.append({
                "id": r[0], "tenant_name": f"{r[1]} {r[2]}", "period": r[3], "total": float(r[4]), "status": r[5]
            })
        return {"invoices": inv_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/invoice/{invoice_id}", dependencies=[Depends(verify_token)])
def api_get_invoice(invoice_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT i.id, i.tenant_id, i.billing_period, i.total, i.status, i.date FROM invoices i WHERE i.id = %s", (invoice_id,))
        inv_data = cursor.fetchone()
        if not inv_data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        inv_id, tenant_id, period, total, status, date = inv_data
        
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (tenant_id,))
        t_data = cursor.fetchone()
        
        cursor.execute("SELECT description, quantity, unit_price, total, drill_down FROM invoice_items WHERE invoice_id = %s", (inv_id,))
        items_rows = cursor.fetchall()
        
        items = []
        for r in items_rows:
            items.append({
                "item_id": r[0], # using description as id for frontend toggle
                "description": r[0], 
                "quantity": float(r[1]), 
                "unit_price": float(r[2]), 
                "total": float(r[3]), 
                "drill_down": r[4]
            })

        return {
            "id": inv_id,
            "tenant_name": f"{t_data[0]} {t_data[1]}",
            "email": t_data[2],
            "period": period,
            "total": float(total),
            "status": status,
            "date": date.strftime("%Y-%m-%d"),
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()