import shutil

print("Adding bulk invoice generation...")

# === 1. ADD BACKEND ENDPOINT TO invoices.py ===
print("\n1. Adding bulk endpoint to invoices.py...")

shutil.copy('api/routers/invoices.py', 'api/routers/invoices.py.bak')

with open('api/routers/invoices.py', 'r', encoding='utf-8') as f:
    inv = f.read()

if 'generate-invoices-bulk' not in inv:
    endpoint = '''

@router.post("/generate-invoices-bulk/", dependencies=[Depends(verify_token)])
def api_generate_bulk_invoices(payload: dict):
    """Generate invoices for ALL active tenants in a property."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        property_id = payload.get("property_id")
        billing_period = payload.get("billing_period")
        cycle_type = payload.get("cycle_type", "MONTHLY")
        
        if not property_id or not billing_period:
            raise HTTPException(status_code=400, detail="Property ID and billing period are required.")
        
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
        
        # Check for existing invoices in this period (prevent duplicates)
        cursor.execute("""
            SELECT DISTINCT i.tenant_id FROM invoices i 
            JOIN tenants t ON i.tenant_id = t.id 
            WHERE t.property_id = %s AND i.billing_period = %s
        """, (property_id, billing_period))
        existing = set(row[0] for row in cursor.fetchall())
        
        # Get all active tenants in this property with arrears
        cursor.execute("""
            SELECT id, first_name, last_name, rent_outstanding, electricity_outstanding, water_outstanding
            FROM tenants 
            WHERE property_id = %s AND status = 'ACTIVE'
            ORDER BY unit_number
        """, (property_id,))
        tenants = cursor.fetchall()
        
        if not tenants:
            raise HTTPException(status_code=404, detail="No active tenants found for this property.")
        
        generated = 0
        skipped = 0
        no_arrears = 0
        total_amount = Decimal('0')
        errors = []
        
        for t in tenants:
            tenant_id = t[0]
            first_name = t[1] or ""
            last_name = t[2] or ""
            rent_due = Decimal(str(t[3] or 0))
            elec_due = Decimal(str(t[4] or 0))
            water_due = Decimal(str(t[5] or 0))
            tenant_total = rent_due + elec_due + water_due
            
            # Skip if already invoiced this period
            if tenant_id in existing:
                skipped += 1
                continue
            
            # Skip if no arrears
            if tenant_total <= 0:
                no_arrears += 1
                continue
            
            try:
                # Create invoice header
                cursor.execute("""
                    INSERT INTO invoices (tenant_id, billing_period, total, status, date) 
                    VALUES (%s, %s, %s, 'DUE', CURRENT_DATE) RETURNING id
                """, (tenant_id, billing_period, tenant_total))
                invoice_id = cursor.fetchone()[0]
                
                # Create line items
                if rent_due > 0:
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (invoice_id, f"Rent ({cycle_type})", 1, rent_due, rent_due, 
                          f"Property rent for period {billing_period}"))
                
                if elec_due > 0:
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (invoice_id, "Electricity Charges", 1, elec_due, elec_due,
                          f"Total electricity usage for period {billing_period}"))
                
                if water_due > 0:
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, drill_down) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (invoice_id, "Water Charges", 1, water_due, water_due,
                          f"Total water usage for period {billing_period}"))
                
                generated += 1
                total_amount += tenant_total
                
            except Exception as e:
                errors.append(f"Unit {first_name} {last_name}: {str(e)}")
                conn.rollback()
                continue
        
        conn.commit()
        
        return {
            "status": "success",
            "message": f"Generated {generated} invoices for {billing_period}.",
            "summary": {
                "total_tenants": len(tenants),
                "invoices_generated": generated,
                "already_invoiced": skipped,
                "no_arrears": no_arrears,
                "errors": len(errors),
                "total_amount": float(total_amount)
            },
            "errors": errors[:10]
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()
'''
    inv = inv + endpoint
    with open('api/routers/invoices.py', 'w', encoding='utf-8') as f:
        f.write(inv)
    print("  Added /generate-invoices-bulk/ endpoint.")
else:
    print("  Bulk endpoint already exists.")

# === 2. ADD BULK UI TO DASHBOARD ===
print("\n2. Adding bulk invoice UI to dashboard.html...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add bulk section before the single invoice form
if 'bulkInvoiceSection' not in c:
    bulk_html = """
        <!-- BULK INVOICE GENERATION -->
        <div id="bulkInvoiceSection" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #27ae60;">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Generate Invoices for Entire Property</h3>
            <p style="font-size: 0.85em; color: #7f8c8d; margin: 0 0 10px 0;">Generates invoices for ALL active tenants in the selected property. Skips tenants with no arrears or who already have an invoice for this period.</p>
            <input type="text" id="bulkInvPeriod" placeholder="Period (e.g., 2026-09)" style="width: 200px;">
            <select id="bulkInvCycle" style="width: 150px;">
                <option value="MONTHLY">Monthly</option>
                <option value="BI_MONTHLY">Bi-Monthly</option>
                <option value="QUARTERLY">Quarterly</option>
            </select>
            <button onclick="generateBulkInvoices()" style="background: #27ae60;">Generate All Invoices</button>
            <button type="button" style="background:#7f8c8d; padding:5px 10px; font-size:12px; width:auto; margin-left:5px;" onclick="document.getElementById('bulkInvPeriod').value=''; document.getElementById('bulkInvCycle').selectedIndex=0;">Clear</button>
            <div id="bulkInvResult" class="result" style="display:none; margin-top: 15px;"></div>
        </div>
        
        <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">

        <h3>Generate Single Invoice</h3>
"""
    # Insert before the single invoice section
    insert_before = '<h2>Billing & Interactive Invoices'
    if insert_before in c:
        c = c.replace(insert_before, insert_before + '\n' + bulk_html, 1)
    else:
        # Try to find the invoice input section
        insert_before2 = '<input type="text" id="invUnitNumber"'
        if insert_before2 in c:
            c = c.replace(insert_before2, bulk_html + '\n            ' + insert_before2, 1)
    print("  Added bulk invoice section.")

# Add JavaScript function
if 'function generateBulkInvoices' not in c:
    js = """
    async function generateBulkInvoices() {
        var propId = document.getElementById("propertyFilter").value;
        var period = document.getElementById("bulkInvPeriod").value;
        var cycle = document.getElementById("bulkInvCycle").value;
        var resultDiv = document.getElementById("bulkInvResult");
        
        if(!propId) { 
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>Please select a property first.</p>";
            return;
        }
        if(!period) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>Please enter a billing period (e.g., 2026-09).</p>";
            return;
        }
        
        resultDiv.style.display = "block";
        resultDiv.innerHTML = "<p style='color:#7f8c8d;'>Generating invoices for all active tenants...</p>";
        
        try {
            var r = await fetch('/generate-invoices-bulk/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({ property_id: parseInt(propId), billing_period: period, cycle_type: cycle })
            });
            var d = await r.json();
            if (!r.ok) throw new Error(d.detail || "Failed");
            
            var s = d.summary;
            var html = "<p style='color:green; font-weight:bold; font-size:1.1em;'>" + d.message + "</p>";
            html += "<div style='margin-top:10px; font-size:0.9em; color:#2c3e50;'>";
            html += "<strong>Summary:</strong><br>";
            html += "Total tenants: " + s.total_tenants + "<br>";
            html += "Invoices generated: <strong style='color:green;'>" + s.invoices_generated + "</strong><br>";
            html += "Already invoiced (skipped): " + s.already_invoiced + "<br>";
            html += "No arrears (skipped): " + s.no_arrears + "<br>";
            html += "Errors: " + s.errors + "<br>";
            html += "Total invoiced amount: <strong>R" + s.total_amount.toFixed(2) + "</strong>";
            html += "</div>";
            
            if (d.errors && d.errors.length > 0) {
                html += "<div style='margin-top:10px; color:#e74c3c; font-size:0.85em;'>";
                html += "<strong>Errors:</strong><br>";
                d.errors.forEach(function(err) { html += err + "<br>"; });
                html += "</div>";
            }
            
            resultDiv.innerHTML = html;
            logAction("Bulk Invoice Generation", "Property: " + propId + ", Period: " + period + ", Generated: " + s.invoices_generated);
            loadInvoices();
        } catch (e) {
            resultDiv.innerHTML = "<p style='color:red;'>Error: " + e.message + "</p>";
        }
    }
"""
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]
        print("  Added generateBulkInvoices function.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\n" + "=" * 50)
print("DONE! Bulk invoice generation added.")
print("=" * 50)
print("\nThe Invoices tab now has TWO sections:")
print("  1. Generate Invoices for Entire Property (green box)")
print("     - Select property from dropdown")
print("     - Enter period (e.g., 2026-09)")
print("     - Select cycle (Monthly/Bi-Monthly/Quarterly)")
print("     - Click 'Generate All Invoices'")
print("     - Shows summary: generated, skipped, total amount")
print("     - Prevents duplicates (skips already-invoiced tenants)")
print("     - Skips tenants with no arrears")
print()
print("  2. Generate Single Invoice (existing)")
print("     - For individual tenants")
print()
print("Restart server and test (Ctrl+F5).")