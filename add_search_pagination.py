import shutil

print("Adding search + pagination to meters and audit tables...")

shutil.copy('dashboard.html', 'dashboard.html.bak_pag')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Add search + filter UI to meters section ===
if 'meterSearchInput' not in c:
    c = c.replace(
        '<button onclick="loadAllMeters()">Refresh Meters List</button>',
        '<button onclick="loadAllMeters()">Refresh Meters List</button>\n            <input type="text" id="meterSearchInput" placeholder="Search serial, unit, or tenant..." style="width: 250px; margin-bottom: 0;" oninput="filterMeters()">\n            <select id="meterTypeFilter" style="width: 150px; margin-bottom: 0;" onchange="filterMeters()">\n                <option value="">All Types</option>\n                <option value="ELECTRICITY">Electricity</option>\n                <option value="WATER_COLD">Cold Water</option>\n                <option value="WATER_HOT">Hot Water</option>\n            </select>\n            <span id="meterPageInfo" style="font-size: 0.85em; color: #7f8c8d; margin-left: 10px;"></span>'
    )
    print("  Added meters search + filter UI.")

# === 2. Add search UI to audit section ===
if 'auditSearchInput' not in c:
    c = c.replace(
        '<button onclick="loadAuditLog()">Load Audit Log</button>',
        '<button onclick="loadAuditLog()">Load Audit Log</button>\n            <input type="text" id="auditSearchInput" placeholder="Search user, action, or details..." style="width: 300px; margin-bottom: 0;" oninput="filterAudit()">\n            <span id="auditPageInfo" style="font-size: 0.85em; color: #7f8c8d; margin-left: 10px;"></span>'
    )
    print("  Added audit search UI.")

# === 3. Add pagination CSS ===
if '.page-btn' not in c:
    css = """
        .page-btn { background: #3498db; color: white; border: none; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em; margin: 0 2px; }
        .page-btn:hover { background: #2980b9; }
        .page-btn:disabled { background: #bdc3c7; cursor: not-allowed; }
        .pagination-bar { margin-top: 10px; display: flex; justify-content: space-between; align-items: center; }
    """
    c = c.replace('<style>', '<style>\n' + css, 1)

# === 4. Add overridden functions ===
idx = c.rfind('</script>')
if idx != -1:
    new_funcs = r"""
    // OVERRIDDEN: Meters with search, filter, and pagination
    var allMetersCache = [];
    var metersPage = 1;
    var metersPerPage = 25;

    async function loadAllMeters() {
        var tB = document.getElementById("metersTableBody");
        var url = '/all-meters/' + getPropertyFilter();
        try {
            var r = await fetch(url, { headers: getAuthHeaders() });
            var d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            allMetersCache = d.meters || [];
            metersPage = 1;
            filterMeters();
        } catch (e) { console.error("Error: " + e.message); }
    }

    function filterMeters() {
        var tB = document.getElementById("metersTableBody");
        var search = (document.getElementById('meterSearchInput') || {}).value || '';
        var typeFilter = (document.getElementById('meterTypeFilter') || {}).value || '';
        var searchLower = search.toLowerCase();

        var filtered = allMetersCache.filter(function(m) {
            var matchSearch = !searchLower ||
                (m.serial_number || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (m.unit_number || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (m.tenant_name || '').toLowerCase().indexOf(searchLower) >= 0;
            var matchType = !typeFilter || m.meter_type === typeFilter;
            return matchSearch && matchType;
        });

        var totalPages = Math.ceil(filtered.length / metersPerPage);
        if (metersPage > totalPages) metersPage = 1;
        if (metersPage < 1) metersPage = totalPages;

        var start = (metersPage - 1) * metersPerPage;
        var end = start + metersPerPage;
        var pageItems = filtered.slice(start, end);

        tB.innerHTML = "";
        pageItems.forEach(function(m) {
            var mId = m.meter_id || m.id;
            tB.innerHTML += '<tr><td>' + mId + '</td><td>' + (m.unit_number || 'N/A') + '</td><td>' + (m.property_name || 'N/A') + '</td><td>' + (m.tenant_name || 'Vacant') + '</td><td>' + m.meter_type + '</td><td>' + m.billing_type + '</td><td>' + m.serial_number + '</td><td>' + (m.valve_status || 'N/A') + '</td><td>' + (m.is_active ? 'Yes' : 'No') + '</td><td><button onclick="logMeterEvent(' + mId + ')" class="btn-event">Log Event</button> <button onclick="viewMeterHistory(' + mId + ')" class="btn-history">History</button>' + (m.is_active ? ' <button onclick="deactivateMeter(' + mId + ')" class="btn-danger">Deactivate</button>' : '') + '</td></tr>';
        });

        document.getElementById("metersTable").style.display = "block";

        var info = document.getElementById("meterPageInfo");
        if (info) {
            info.innerHTML = 'Showing ' + (start + 1) + '-' + Math.min(end, filtered.length) + ' of ' + filtered.length + ' meters';
        }

        var pagBar = document.getElementById("meterPaginationBar");
        if (!pagBar) {
            pagBar = document.createElement('div');
            pagBar.id = "meterPaginationBar";
            pagBar.className = "pagination-bar";
            document.getElementById("metersTable").parentNode.insertBefore(pagBar, document.getElementById("metersTable").nextSibling);
        }
        pagBar.innerHTML = '<div><button class="page-btn" onclick="changeMeterPage(-1)" ' + (metersPage <= 1 ? 'disabled' : '') + '>Previous</button> <span style="font-size:0.85em;">Page ' + metersPage + ' of ' + (totalPages || 1) + '</span> <button class="page-btn" onclick="changeMeterPage(1)" ' + (metersPage >= totalPages ? 'disabled' : '') + '>Next</button></div><div style="font-size:0.8em; color:#7f8c8d;">25 per page</div>';
    }

    function changeMeterPage(dir) {
        metersPage += dir;
        filterMeters();
    }

    // OVERRIDDEN: Audit with search and pagination
    var allAuditCache = [];
    var auditPage = 1;
    var auditPerPage = 50;

    async function loadAuditLog() {
        var tB = document.getElementById("auditTableBody");
        try {
            var r = await fetch('/audit-log/', { headers: getAuthHeaders() });
            var d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            allAuditCache = d.logs || [];
            auditPage = 1;
            filterAudit();
        } catch(e) { console.error("Error: " + e.message); }
    }

    function filterAudit() {
        var tB = document.getElementById("auditTableBody");
        var search = (document.getElementById('auditSearchInput') || {}).value || '';
        var searchLower = search.toLowerCase();

        var filtered = allAuditCache.filter(function(l) {
            if (!searchLower) return true;
            return (l.username || '').toLowerCase().indexOf(searchLower) >= 0 ||
                   (l.action || '').toLowerCase().indexOf(searchLower) >= 0 ||
                   (l.details || '').toLowerCase().indexOf(searchLower) >= 0;
        });

        var totalPages = Math.ceil(filtered.length / auditPerPage);
        if (auditPage > totalPages) auditPage = 1;
        if (auditPage < 1) auditPage = totalPages;

        var start = (auditPage - 1) * auditPerPage;
        var end = start + auditPerPage;
        var pageItems = filtered.slice(start, end);

        tB.innerHTML = "";
        pageItems.forEach(function(l) {
            tB.innerHTML += '<tr><td>' + l.timestamp + '</td><td>' + l.username + '</td><td>' + l.action + '</td><td>' + l.details + '</td></tr>';
        });

        document.getElementById("auditTable").style.display = "block";

        var info = document.getElementById("auditPageInfo");
        if (info) {
            info.innerHTML = 'Showing ' + (start + 1) + '-' + Math.min(end, filtered.length) + ' of ' + filtered.length;
        }

        var pagBar = document.getElementById("auditPaginationBar");
        if (!pagBar) {
            pagBar = document.createElement('div');
            pagBar.id = "auditPaginationBar";
            pagBar.className = "pagination-bar";
            document.getElementById("auditTable").parentNode.insertBefore(pagBar, document.getElementById("auditTable").nextSibling);
        }
        pagBar.innerHTML = '<div><button class="page-btn" onclick="changeAuditPage(-1)" ' + (auditPage <= 1 ? 'disabled' : '') + '>Previous</button> <span style="font-size:0.85em;">Page ' + auditPage + ' of ' + (totalPages || 1) + '</span> <button class="page-btn" onclick="changeAuditPage(1)" ' + (auditPage >= totalPages ? 'disabled' : '') + '>Next</button></div><div style="font-size:0.8em; color:#7f8c8d;">50 per page</div>';
    }

    function changeAuditPage(dir) {
        auditPage += dir;
        filterAudit();
    }
"""
    c = c[:idx] + new_funcs + '\n' + c[idx:]
    print("  Added overridden functions (meters + audit with pagination).")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart server and test (Ctrl+F5).")