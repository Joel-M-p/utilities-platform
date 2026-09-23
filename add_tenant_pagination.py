import shutil

print("Adding search + pagination to tenants table...")

shutil.copy('dashboard.html', 'dashboard.html.bak_tenants')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add search box to tenants section
if 'tenantSearchInput' not in c:
    c = c.replace(
        '<button onclick="triggerMockRent()" class="btn-restrict">Sync Rent</button>',
        '<button onclick="triggerMockRent()" class="btn-restrict">Sync Rent</button>\n            <input type="text" id="tenantSearchInput" placeholder="Search unit, name, email..." style="width: 250px; margin-bottom: 0; margin-left: 10px;" oninput="filterTenants()">\n            <select id="tenantStatusFilter" style="width: 120px; margin-bottom: 0;" onchange="filterTenants()">\n                <option value="">All Status</option>\n                <option value="ACTIVE">Active</option>\n                <option value="SUSPENDED">Suspended</option>\n                <option value="VACATED">Vacated</option>\n                <option value="ARREARS">In Arrears</option>\n            </select>\n            <span id="tenantPageInfo" style="font-size: 0.85em; color: #7f8c8d; margin-left: 10px;"></span>'
    )
    print("  Added tenants search + status filter UI.")

# 2. Add overridden loadAllTenants + filterTenants functions
idx = c.rfind('</script>')
if idx != -1:
    new_funcs = r"""
    // OVERRIDDEN: Tenants with search, filter, and pagination
    async function loadAllTenants() {
        var tB = document.getElementById("tenantsTableBody");
        try {
            var url = '/all-tenants/' + getPropertyFilter();
            var r = await fetch(url, { headers: getAuthHeaders() });
            var d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            allTenantsCache = d.tenants || [];
            tenantsPage = 1;
            filterTenants();
        } catch (e) { console.error("Error calling /all-tenants: " + e.message); }
    }

    var tenantsPage = 1;
    var tenantsPerPage = 25;

    function filterTenants() {
        var tB = document.getElementById("tenantsTableBody");
        if (!tB) return;
        var search = (document.getElementById('tenantSearchInput') || {}).value || '';
        var statusFilter = (document.getElementById('tenantStatusFilter') || {}).value || '';
        var searchLower = search.toLowerCase();

        var filtered = allTenantsCache.filter(function(t) {
            // Search filter
            var matchSearch = !searchLower ||
                (t.unit_number || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (t.first_name || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (t.last_name || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (t.email || '').toLowerCase().indexOf(searchLower) >= 0 ||
                (t.cellphone || '').toLowerCase().indexOf(searchLower) >= 0;

            // Status filter
            var matchStatus = true;
            if (statusFilter === 'ARREARS') {
                matchStatus = (t.rent_outstanding > 0 || t.electricity_outstanding > 0 || t.water_outstanding > 0);
            } else if (statusFilter) {
                matchStatus = (t.status || '').toUpperCase() === statusFilter;
            }

            return matchSearch && matchStatus;
        });

        var totalPages = Math.ceil(filtered.length / tenantsPerPage);
        if (tenantsPage > totalPages) tenantsPage = 1;
        if (tenantsPage < 1) tenantsPage = totalPages || 1;

        var start = (tenantsPage - 1) * tenantsPerPage;
        var end = start + tenantsPerPage;
        var pageItems = filtered.slice(start, end);

        tB.innerHTML = "";
        pageItems.forEach(function(t) {
            var tId = t.tenant_id || t.id;
            var upperStatus = (t.status || 'ACTIVE').toUpperCase();
            var statusClass = upperStatus === 'ACTIVE' ? 'status-active' : (upperStatus === 'VACATED' ? 'status-vacated' : 'status-suspended');
            var payStatus = (t.rent_outstanding > 0 || t.electricity_outstanding > 0 || t.water_outstanding > 0) ? '<span style="color:red;font-weight:bold;">IN ARREARS</span>' : '<span style="color:green;font-weight:bold;">CLEAR</span>';

            tB.innerHTML += '<tr><td>' + (t.unit_number || 'N/A') + '</td><td>' + (t.first_name || '') + ' ' + (t.last_name || '') + '</td><td>' + (t.email || 'N/A') + '</td><td>' + (t.cellphone || 'N/A') + '</td><td>' + payStatus + '</td><td>R' + (t.rent_outstanding || 0).toFixed(2) + '</td><td>R' + (t.electricity_outstanding || 0).toFixed(2) + '</td><td>R' + (t.water_outstanding || 0).toFixed(2) + '</td><td>R' + (t.wallet_balance || 0).toFixed(2) + '</td><td class="' + statusClass + '">' + upperStatus + '</td><td>' + (t.credit_status || 'N/A') + '</td><td><button onclick="editTenant(' + tId + ')" class="btn-edit">Edit</button> <button onclick="viewStatement(' + tId + ')" class="btn-statement">Statement</button> <button onclick="openDocs(' + tId + ')" class="btn-docs">Docs</button> <button onclick="grantConsent(' + tId + ')" class="btn-popia">Consent</button> <button onclick="anonymize(' + tId + ')" class="btn-anonymize">Anonymize</button> <button onclick="runCreditCheck(' + tId + ')" class="btn-credit">Credit</button> <button onclick="suspendTenant(' + tId + ')" class="btn-suspend">Suspend</button> <button onclick="vacateTenant(' + tId + ')" class="btn-danger">Vacate</button></td></tr>';
        });

        document.getElementById("tenantsTable").style.display = "block";

        var info = document.getElementById("tenantPageInfo");
        if (info) {
            info.innerHTML = 'Showing ' + (start + 1) + '-' + Math.min(end, filtered.length) + ' of ' + filtered.length + ' tenants';
        }

        // Pagination bar
        var pagBar = document.getElementById("tenantPaginationBar");
        if (!pagBar) {
            pagBar = document.createElement('div');
            pagBar.id = "tenantPaginationBar";
            pagBar.className = "pagination-bar";
            var table = document.getElementById("tenantsTable");
            table.parentNode.insertBefore(pagBar, table.nextSibling);
        }
        pagBar.innerHTML = '<div><button class="page-btn" onclick="changeTenantPage(-1)" ' + (tenantsPage <= 1 ? 'disabled' : '') + '>Previous</button> <span style="font-size:0.85em;">Page ' + tenantsPage + ' of ' + (totalPages || 1) + '</span> <button class="page-btn" onclick="changeTenantPage(1)" ' + (tenantsPage >= totalPages ? 'disabled' : '') + '>Next</button></div><div style="font-size:0.8em; color:#7f8c8d;">25 per page</div>';
    }

    function changeTenantPage(dir) {
        tenantsPage += dir;
        filterTenants();
    }
"""
    c = c[:idx] + new_funcs + '\n' + c[idx:]
    print("  Added overridden loadAllTenants + filterTenants functions.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart server and test (Ctrl+F5).")