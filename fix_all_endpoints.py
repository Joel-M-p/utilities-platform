import shutil

print("Fixing all endpoint mismatches...")

# === FIX DASHBOARD.HTML ===
shutil.copy('dashboard.html', 'dashboard.html.bak_endpoints')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# --- Simple URL replacements ---
replacements = [
    ('/aging-report/', '/arrears-aging/'),
    ('/payment-recon/', '/payment-reconciliation/'),
    ('/stats-3month/', '/three-month-stats/'),
    ('/meter-event/', '/log-meter-event/'),
    ('/meter-history/', '/meter-audit-history/'),
]

for old, new in replacements:
    if old in c:
        c = c.replace(old, new)
        changes += 1
        print(f"  Fixed URL: {old} -> {new}")

# --- Helper: replace entire function by name ---
def replace_func(content, func_name, new_func):
    lines = content.split('\n')
    new_lines = []
    skip = False
    depth = 0
    replaced = False
    for line in lines:
        if not skip and f'function {func_name}' in line:
            skip = True
            depth = line.count('{') - line.count('}')
            new_lines.append(new_func)
            replaced = True
            if depth <= 0:
                skip = False
            continue
        if skip:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                skip = False
            continue
        new_lines.append(line)
    if replaced:
        return '\n'.join(new_lines), True
    return content, False

# --- Fix restrictWater ---
new_restrict = """    async function restrictWater() {
        const unit = document.getElementById("restrictUnitNumber").value;
        const resultDiv = document.getElementById("restrictResult");
        const tenantCheck = getTenantIdByUnit(unit);
        if(tenantCheck.error) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">${tenantCheck.error}</p>`;
            return;
        }
        const tenantId = tenantCheck.id;
        try {
            const url = `/restrict-water/${tenantId}`;
            const r = await fetch(url, { method: 'POST', headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:green;">${d.message}</p>`;
            loadAllMeters();
        } catch (e) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
        }
    }"""
c, ok = replace_func(c, 'restrictWater', new_restrict)
if ok: changes += 1; print("  Fixed restrictWater")

# --- Fix unrestrictWater ---
new_unrestrict = """    async function unrestrictWater() {
        const unit = document.getElementById("restrictUnitNumber").value;
        const resultDiv = document.getElementById("restrictResult");
        const tenantCheck = getTenantIdByUnit(unit);
        if(tenantCheck.error) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">${tenantCheck.error}</p>`;
            return;
        }
        const tenantId = tenantCheck.id;
        try {
            const url = `/unrestrict-water/${tenantId}`;
            const r = await fetch(url, { method: 'POST', headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:green;">${d.message}</p>`;
            loadAllMeters();
        } catch (e) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
        }
    }"""
c, ok = replace_func(c, 'unrestrictWater', new_unrestrict)
if ok: changes += 1; print("  Fixed unrestrictWater")

# --- Fix loadAging (response format: d.report -> d.aging) ---
new_aging = """    async function loadAging() {
        const tB = document.getElementById("agingTableBody");
        try {
            const url = `/arrears-aging/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            tB.innerHTML = "";
            (d.aging || d.report || []).forEach(t => {
                tB.innerHTML += `<tr>
                    <td>${t.tenant_name}</td>
                    <td>R${t.total_arrears.toFixed(2)}</td>
                    <td>R${(t.current || t.bucket_30 || 0).toFixed(2)}</td>
                    <td>R${(t.days_30 || t.bucket_60 || 0).toFixed(2)}</td>
                    <td>R${(t.days_60 || t.bucket_90 || 0).toFixed(2)}</td>
                    <td>R${(t.days_90 || t.bucket_over_90 || 0).toFixed(2)}</td>
                </tr>`;
            });
            document.getElementById("agingTable").style.display = "block";
        } catch (e) { alert("Error calling /arrears-aging: " + e.message); }
    }"""
c, ok = replace_func(c, 'loadAging', new_aging)
if ok: changes += 1; print("  Fixed loadAging")

# --- Fix loadPaymentRecon (response format + URL) ---
new_payment_recon = """    async function loadPaymentRecon() {
        const tB = document.getElementById("reconReportTableBody");
        try {
            const url = `/payment-reconciliation/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            tB.innerHTML = "";
            (d.reconciliation || d.report || []).forEach(t => {
                tB.innerHTML += `<tr>
                    <td>${t.tenant_name}</td>
                    <td>R${t.total_billed.toFixed(2)}</td>
                    <td>R${t.total_paid.toFixed(2)}</td>
                    <td>R${t.wallet_balance.toFixed(2)}</td>
                    <td>R${t.rent_arrears.toFixed(2)}</td>
                    <td>R${t.elec_arrears.toFixed(2)}</td>
                    <td>R${t.water_arrears.toFixed(2)}</td>
                    <td>R${t.balance_due.toFixed(2)}</td>
                </tr>`;
            });
            document.getElementById("reconReportTable").style.display = "block";
        } catch (e) { alert("Error calling /payment-reconciliation: " + e.message); }
    }"""
c, ok = replace_func(c, 'loadPaymentRecon', new_payment_recon)
if ok: changes += 1; print("  Fixed loadPaymentRecon")

# --- Fix load3MonthStats ---
new_stats = """    async function load3MonthStats() {
        const tB = document.getElementById("statsTableBody");
        try {
            const url = `/three-month-stats/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            tB.innerHTML = "";
            d.stats.forEach(s => {
                tB.innerHTML += `<tr>
                    <td>${s.month}</td>
                    <td>R${s.elec.toFixed(2)}</td>
                    <td>R${s.water.toFixed(2)}</td>
                </tr>`;
            });
            document.getElementById("statsTable").style.display = "block";
        } catch (e) { alert("Error calling /three-month-stats: " + e.message); }
    }"""
c, ok = replace_func(c, 'load3MonthStats', new_stats)
if ok: changes += 1; print("  Fixed load3MonthStats")

# --- Fix loadBankRecon (replace mock with real) ---
new_bank_recon = """    async function loadBankRecon() {
        const div = document.getElementById("bankResult");
        div.style.display = "block";
        div.innerHTML = "<p>Generating Bank Recon...</p>";
        try {
            const url = `/bank-reconciliation/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            div.innerHTML = `<p><strong>Total Collected:</strong> R${d.total_collected.toFixed(2)}<br>
                <strong>Total Disbursed:</strong> R${d.total_disbursed.toFixed(2)}<br>
                <strong>Net Balance:</strong> R${d.net_balance.toFixed(2)}</p>`;
        } catch (e) { div.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`; }
    }"""
c, ok = replace_func(c, 'loadBankRecon', new_bank_recon)
if ok: changes += 1; print("  Fixed loadBankRecon (real endpoint)")

# --- Fix loadMgmtInvoice (replace mock with real) ---
new_mgmt = """    async function loadMgmtInvoice() {
        const div = document.getElementById("mgmtResult");
        div.style.display = "block";
        div.innerHTML = "<p>Generating Management Fee Invoice...</p>";
        try {
            const url = `/management-fee-invoice/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            let rows = (d.items || []).map(i => `<li>${i.desc}: R${i.amount.toFixed(2)}</li>`).join("");
            div.innerHTML = `<p><strong>Total Collections:</strong> R${d.total_collections.toFixed(2)}</p>
                <ul>${rows}</ul>
                <p><strong>Subtotal:</strong> R${d.subtotal.toFixed(2)}<br>
                <strong>VAT:</strong> R${d.vat.toFixed(2)}<br>
                <strong>Total:</strong> R${d.total.toFixed(2)}</p>`;
        } catch (e) { div.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`; }
    }"""
c, ok = replace_func(c, 'loadMgmtInvoice', new_mgmt)
if ok: changes += 1; print("  Fixed loadMgmtInvoice (real endpoint)")

# --- Fix generateFinancialReport (format nicely instead of raw JSON) ---
new_fin_report = """    async function generateFinancialReport() {
        try {
            const url = `/financial-report/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            let monthlyRows = (d.revenue.monthly || []).map(m =>
                `<tr><td>${m.month}</td><td>R${m.revenue.toFixed(2)}</td><td>R${m.billed.toFixed(2)}</td></tr>`
            ).join("");
            let consumptionRows = (d.consumption || []).map(c =>
                `<tr><td>${c.tenant}</td><td>R${c.value.toFixed(2)}</td></tr>`
            ).join("") || '<tr><td colspan="2" style="color:#7f8c8d;">No consumption data yet.</td></tr>';
            document.getElementById("reportContent").innerHTML = `
                <h2>Financial Report</h2>
                <div class="kpi-grid">
                    <div class="kpi-card green"><h3>Total Collected</h3><div class="value">R${d.revenue.total_revenue.toFixed(2)}</div></div>
                    <div class="kpi-card orange"><h3>Total Billed</h3><div class="value">R${d.revenue.total_billed.toFixed(2)}</div></div>
                    <div class="kpi-card"><h3>Collection Rate</h3><div class="value">${d.revenue.collection_rate.toFixed(1)}%</div></div>
                    <div class="kpi-card red"><h3>Total Arrears</h3><div class="value">R${d.arrears.total.toFixed(2)}</div></div>
                </div>
                <h3>Arrears Breakdown</h3>
                <p>Rent: R${d.arrears.rent.toFixed(2)} | Electricity: R${d.arrears.electricity.toFixed(2)} | Water: R${d.arrears.water.toFixed(2)}</p>
                <h3>Monthly Trend</h3>
                <table><thead><tr><th>Month</th><th>Collected</th><th>Billed</th></tr></thead><tbody>${monthlyRows || '<tr><td colspan="3" style="color:#7f8c8d;">No monthly data yet.</td></tr>'}</tbody></table>
                <h3>Top Consumers</h3>
                <table><thead><tr><th>Tenant</th><th>Consumption (R)</th></tr></thead><tbody>${consumptionRows}</tbody></table>
            `;
            document.getElementById("reportModal").style.display = "block";
        } catch (e) { alert("Error calling /financial-report: " + e.message); }
    }"""
c, ok = replace_func(c, 'generateFinancialReport', new_fin_report)
if ok: changes += 1; print("  Fixed generateFinancialReport (nice formatting)")

# --- Fix loadPropertyReport (URL + response format) ---
new_prop_report = """    async function loadPropertyReport() {
        const tB = document.getElementById("propTableBody");
        try {
            const r = await fetch(`/property-report/${getPropertyFilter()}`, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            tB.innerHTML = "";
            (d.properties || d.report || []).forEach(p => {
                tB.innerHTML += `<tr>
                    <td>${p.name || p.property_name}</td>
                    <td>${p.tenant_count}</td>
                    <td>R${p.total_arrears.toFixed(2)}</td>
                    <td>R${(p.wallet_balance || p.wallet_balances || 0).toFixed(2)}</td>
                </tr>`;
            });
            document.getElementById("propTable").style.display = "block";
        } catch (e) { alert("Error calling /property-report: " + e.message); }
    }"""
c, ok = replace_func(c, 'loadPropertyReport', new_prop_report)
if ok: changes += 1; print("  Fixed loadPropertyReport")

# --- Fix generateInvoice (tenant_id in body, not URL) ---
new_invoice = """    async function generateInvoice() {
        const unit = document.getElementById("invUnitNumber").value;
        const resultDiv = document.getElementById("invResult");
        const tenantCheck = getTenantIdByUnit(unit);
        if(tenantCheck.error) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">${tenantCheck.error}</p>`;
            return;
        }
        const tenantId = tenantCheck.id;
        const payload = {
            tenant_id: tenantId,
            period: document.getElementById("invPeriod").value,
            cycle: document.getElementById("invCycle").value
        };
        try {
            const url = `/generate-invoice/`;
            const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` }, body: JSON.stringify(payload) });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:green;">${d.message}</p>`;
            loadInvoices();
        } catch (e) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
        }
    }"""
c, ok = replace_func(c, 'generateInvoice', new_invoice)
if ok: changes += 1; print("  Fixed generateInvoice (tenant_id in body)")

# --- Fix loadInvoices (response format) ---
new_load_inv = """    async function loadInvoices() {
        const tB = document.getElementById("invoicesTableBody");
        try {
            const url = `/invoices/${getPropertyFilter()}`;
            const r = await fetch(url, { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            tB.innerHTML = "";
            d.invoices.forEach(inv => {
                tB.innerHTML += `<tr>
                    <td>${inv.id}</td>
                    <td>${inv.tenant_name}</td>
                    <td>${inv.period}</td>
                    <td>R${inv.total_amount.toFixed(2)}</td>
                    <td>${inv.status}</td>
                    <td><button onclick="viewInvoice(${inv.id})" class="btn-invoice">View</button></td>
                </tr>`;
            });
            document.getElementById("invoicesTable").style.display = "block";
        } catch (e) { console.error("Error calling /invoices: " + e.message); }
    }"""
c, ok = replace_func(c, 'loadInvoices', new_load_inv)
if ok: changes += 1; print("  Fixed loadInvoices")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print(f"DONE! {changes} fixes applied.")
print(f"{'='*55}")
print("\nRestart server and test (Ctrl+F5):")
print("  1. Reports -> Generate Aging Report -> should work")
print("  2. Reports -> Generate Payment Reconciliation -> should work")
print("  3. Reports -> Generate Stats (3-month) -> should work")
print("  4. Reports -> Generate Bank Recon -> should show real data")
print("  5. Reports -> Generate Fee Invoice -> should show real data")
print("  6. Reports -> Generate Full Financial Report -> should show nice format")
print("  7. Reports -> Generate Property Report -> should work")
print("  8. Invoices -> Generate Invoice -> should work")
print("  9. Billing -> Restrict/Restore Water -> should work")
print(" 10. Meters -> Log Event / History -> should work")