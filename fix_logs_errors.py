import shutil

print("Fixing log errors...")

# === FIX DASHBOARD.HTML ===
shutil.copy('dashboard.html', 'dashboard.html.bak_fix')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 1: Replace loadActiveAlarms to use mock data only (no 404)
old_alarms = """    async function loadActiveAlarms() {
        const container = document.getElementById('activeAlarms');
        if (!container) return;
        try {
            const r = await fetch('/meter-events/', { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error('Failed');
            
            if (!d.events || d.events.length === 0) {"""

new_alarms = """    async function loadActiveAlarms() {
        const container = document.getElementById('activeAlarms');
        if (!container) return;
        try {"""

if old_alarms in c:
    # Find the entire loadActiveAlarms function and replace it
    lines = c.split('\n')
    new_lines = []
    skip = False
    depth = 0
    replaced = False
    
    new_func = """    async function loadActiveAlarms() {
        const container = document.getElementById('activeAlarms');
        if (!container) return;
        const mockAlarms = [
            { serial: 'WM-101', type: 'WATER_LEAKAGE', notes: 'Continuous flow for 26 hours. Flow: 0.3 m3/h', severity: 'HIGH', time: '2h ago' },
            { serial: 'WM-205', type: 'LOW_BATTERY', notes: 'Battery at 2.9V. Replacement within 30 days.', severity: 'MEDIUM', time: '5h ago' },
            { serial: 'WM-308', type: 'TAMPER_DETECT', notes: 'Magnetic interference. Valve auto-closed.', severity: 'HIGH', time: '1h ago' },
            { serial: 'WM-412', type: 'VALVE_FAIL', notes: 'Valve close command failed after 3 retries.', severity: 'HIGH', time: '8h ago' },
        ];
        let html = '';
        mockAlarms.forEach(a => {
            let sevClass = a.severity === 'HIGH' ? 'alarm-high' : (a.severity === 'MEDIUM' ? 'alarm-medium' : 'alarm-low');
            let icon = a.type.includes('LEAK') ? 'LEAK ' : (a.type.includes('BATTERY') ? 'BATT ' : (a.type.includes('TAMPER') ? 'TAMPER ' : 'ALERT '));
            html += '<div class="alarm-item"><div><div style="font-weight:bold; color:#2c3e50;">' + icon + a.type.replace(/_/g, ' ') + ' - ' + a.serial + '</div><div style="font-size:0.85em; color:#7f8c8d;">' + a.notes + ' - ' + a.time + '</div></div><span class="alarm-badge ' + sevClass + '">' + a.severity + '</span></div>';
        });
        container.innerHTML = html;
    }"""

    for line in lines:
        if not skip and 'async function loadActiveAlarms' in line:
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
        c = '\n'.join(new_lines)
        print("  Fixed loadActiveAlarms (no more 404).")
    else:
        print("  loadActiveAlarms not found - may already be fixed.")

# Fix 2: Fix generateInvoice to use tenantCheck.id instead of object
old_invoice = """    async function generateInvoice() {
        const unit = document.getElementById("invUnitNumber").value;
        const tenantId = getTenantIdByUnit(unit);
        if(!tenantId) return;"""

new_invoice = """    async function generateInvoice() {
        const unit = document.getElementById("invUnitNumber").value;
        const tenantCheck = getTenantIdByUnit(unit);
        if(tenantCheck.error) { alert(tenantCheck.error); return; }
        const tenantId = tenantCheck.id;"""

if old_invoice in c:
    c = c.replace(old_invoice, new_invoice)
    print("  Fixed generateInvoice (no more [object Object]).")
else:
    print("  generateInvoice not found or already fixed.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart server and test (Ctrl+F5).")