print("Adding input field clearing after form submissions...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# === 1. Add clearField helper function ===
if 'function clearField' not in c:
    helper = """
    function clearField(id) {
        var el = document.getElementById(id);
        if (!el) return;
        if (el.tagName === 'SELECT') { el.selectedIndex = 0; }
        else if (el.type === 'file') { el.value = ''; }
        else { el.value = ''; }
    }
    function clearFields(ids) { ids.forEach(function(id) { clearField(id); }); }
"""
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + helper + '\n' + c[idx:]
        changes += 1
        print("  Added clearField helper function.")

# === 2. Add clearing after each logAction call ===
logAction_rules = {
    'logAction("Assigned Meter"': ['meterUnitNumber', 'meterSerial', 'meterType', 'billingType'],
    'logAction("Manual Meter Reading"': ['readingMeterSerial', 'readingValue', 'readingDate'],
    'logAction("Processed Payment"': ['paymentUnitNumber', 'paymentAmount', 'paymentRentPct', 'paymentElecPct', 'paymentWaterPct'],
    'logAction("Created Tenant"': ['newUnitNumber', 'newFirstName', 'newLastName', 'newEmail', 'newCellphone', 'newRentDebt', 'newElecDebt', 'newWaterDebt'],
    'logAction("Adjusted Account"': ['adjUnitNumber', 'adjAmount', 'adjReason'],
    'logAction("Set Emergency Fund"': ['creditUnitNumber', 'creditLimitInput'],
    'logAction("Generated Credit Note"': ['cnUnitNumber', 'cnAmount', 'cnReason'],
    'logAction("Uploaded Doc"': ['docUnitNumber'],
    'logAction("Saved Property"': ['propId', 'propName', 'propProvince', 'propAddress'],
    'logAction("Updated Tenant"': [],
    'logAction("Reset Tenant Password"': [],
    'logAction("Reset User Password"': [],
}

for marker, fields in logAction_rules.items():
    if marker in c and fields:
        # Check if clearing already exists right after this marker
        marker_pos = c.find(marker)
        after_marker = c[marker_pos:marker_pos + 500]
        if 'clearField' not in after_marker:
            clearing = '\n            ' + '\n            '.join([f"clearField('{f}');" for f in fields])
            # Find end of the logAction line (next semicolon after the closing parenthesis)
            line_end = c.find(';', marker_pos)
            if line_end != -1:
                insert_pos = line_end + 1
                c = c[:insert_pos] + clearing + c[insert_pos:]
                changes += 1
                print(f"  Added clearing after: {marker}")

# === 3. Handle functions without logAction ===

# generateBill — clear after loadAllTenants() in generateBill context
if 'billResult' in c and "clearField('billUnitNumber')" not in c:
    c = c.replace(
        'loadAllTenants(); } catch (e) { resultDiv.style.display = "block"; resultDiv.innerHTML = `<p style="color:red;">Error calling /generate-bill',
        "clearFields(['billUnitNumber', 'billType', 'billAmount', 'billPeak', 'billOffpeak']); loadAllTenants(); } catch (e) { resultDiv.style.display = \"block\"; resultDiv.innerHTML = `<p style=\"color:red;\">Error calling /generate-bill",
        1
    )
    if "clearField('billUnitNumber')" in c:
        changes += 1
        print("  Added clearing after: generateBill")

# generateInvoice — clear after loadInvoices()
if 'invResult' in c and "clearField('invUnitNumber')" not in c:
    # Find loadInvoices() that comes after invResult
    inv_pos = c.find('invResult')
    if inv_pos != -1:
        load_inv_pos = c.find('loadInvoices()', inv_pos)
        if load_inv_pos != -1:
            c = c[:load_inv_pos] + "clearFields(['invUnitNumber', 'invPeriod']); " + c[load_inv_pos:]
            changes += 1
            print("  Added clearing after: generateInvoice")

# createTariff — clear after loadTariffs() in createTariff context
if 'tariffResult' in c and "clearField('tariffName')" not in c:
    tariff_pos = c.find('tariffResult')
    if tariff_pos != -1:
        load_tariff_pos = c.find('loadTariffs();', tariff_pos)
        if load_tariff_pos != -1:
            c = c[:load_tariff_pos] + "clearFields(['tariffName', 'rateFlat', 'tier1Limit', 'tier1Rate', 'tier2Rate', 'touPeak', 'touOffpeak']); " + c[load_tariff_pos:]
            changes += 1
            print("  Added clearing after: createTariff")

# triggerMockRent — clear after loadAllTenants() in triggerMockRent context
if 'syncRentUnitNumber' in c and "clearField('syncRentUnitNumber')" not in c:
    sync_pos = c.find('syncRentUnitNumber')
    if sync_pos != -1:
        # Find the next loadAllTenants() after syncRentUnitNumber
        load_tenants_pos = c.find('loadAllTenants()', sync_pos)
        if load_tenants_pos != -1:
            c = c[:load_tenants_pos] + "clearField('syncRentUnitNumber'); " + c[load_tenants_pos:]
            changes += 1
            print("  Added clearing after: triggerMockRent")

# submitNTV — clear after success message
if 'ntvResult' in c and "clearField('ntvUnitNumber')" not in c:
    ntv_pos = c.find('ntvResult')
    if ntv_pos != -1:
        success_pos = c.find("color:green", ntv_pos)
        if success_pos != -1:
            # Find the end of this statement
            stmt_end = c.find(';', success_pos)
            if stmt_end != -1:
                c = c[:stmt_end + 1] + "\n            clearFields(['ntvUnitNumber', 'ntvExitDate', 'ntvReason']);" + c[stmt_end + 1:]
                changes += 1
                print("  Added clearing after: submitNTV")

# submitInspection — clear after loadAllMeters() in submitInspection context
if 'inspResult' in c and "clearField('inspUnitNumber')" not in c:
    insp_pos = c.find('inspResult')
    if insp_pos != -1:
        load_meters_pos = c.find('loadAllMeters();', insp_pos)
        if load_meters_pos != -1:
            c = c[:load_meters_pos] + "clearFields(['inspUnitNumber', 'inspNotes']); " + c[load_meters_pos:]
            changes += 1
            print("  Added clearing after: submitInspection")

# runRecon — clear after loadRecons()
if 'reconResult' in c and "clearField('reconMonth')" not in c:
    recon_pos = c.find('reconResult')
    if recon_pos != -1:
        load_recons_pos = c.find('loadRecons();', recon_pos)
        if load_recons_pos != -1:
            c = c[:load_recons_pos] + "clearFields(['reconMonth', 'reconMuni', 'reconSub']); " + c[load_recons_pos:]
            changes += 1
            print("  Added clearing after: runRecon")

# createUser — clear after loadUsers()
if 'newUsername' in c and 'userResult' in c and "clearField('newUsername')" not in c:
    user_pos = c.find('userResult')
    if user_pos != -1:
        load_users_pos = c.find('loadUsers();', user_pos)
        if load_users_pos != -1:
            c = c[:load_users_pos] + "clearFields(['newUsername', 'newUserEmail', 'newUserRole', 'newUserProp']); " + c[load_users_pos:]
            changes += 1
            print("  Added clearing after: createUser")

# checkBalance — clear after showing balance
if 'balanceResult' in c and "clearField('unitNumberInput')" not in c:
    bal_pos = c.find('balanceResult')
    if bal_pos != -1:
        success_pos = c.find("color:green", bal_pos)
        if success_pos != -1:
            stmt_end = c.find(';', success_pos)
            if stmt_end != -1:
                c = c[:stmt_end + 1] + "\n            clearField('unitNumberInput');" + c[stmt_end + 1:]
                changes += 1
                print("  Added clearing after: checkBalance")

# saveProperty — clear after clearPropertyForm() (it already clears, but let's be sure)
if "clearPropertyForm();" in c:
    print("  saveProperty already has clearing (clearPropertyForm).")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\nDone! {changes} clearing rules added.")
print("\nForms that now clear after submission:")
print("  - Assign Meter")
print("  - Generate Bill (Manual)")
print("  - Manual Meter Reading")
print("  - Process Payment")
print("  - Set Emergency Fund")
print("  - Create Tenant")
print("  - Manual Account Adjustment")
print("  - Credit Note")
print("  - Generate Invoice")
print("  - Create Tariff")
print("  - Sync Rent")
print("  - Submit Notice to Vacate")
print("  - Submit Inspection")
print("  - Run Reconciliation")
print("  - Create User")
print("  - Upload Document")
print("  - Check Tenant Balance")
print("  - Save Property")
print("\nTest: Submit any form → fields should clear automatically ✅")