print("Adding Monthly Management Report generator...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add CSS
if '.report-print-btn' not in c:
    css = """
        .report-print-btn { background:#2c3e50; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; margin:20px 0; font-size:14px; }
        .report-mock-banner { background:#fff3cd; color:#856404; padding:5px 10px; border-radius:4px; font-size:0.85em; display:inline-block; margin-bottom:10px; }
    """
    c = c.replace('<style>', '<style>\n' + css, 1)
    print("  Added CSS.")

# 2. Add report button in Reports tab (before Excel Export)
if 'generateMonthlyReport()' not in c:
    button_html = """
        <!-- MONTHLY MANAGEMENT REPORT -->
        <div class="container">
            <h2>Monthly Management Report</h2>
            <p style="color: #7f8c8d; font-size: 0.9rem;">Generates a comprehensive monthly report covering: executive summary, financial waterfall, municipal reconciliation, consumption, alarms, meter health, financial summary, vacancies, tariffs, and recommendations.</p>
            <button onclick="generateMonthlyReport()" class="btn-download">Generate Monthly Report</button>
        </div>

    """
    insert_before = '<div class="container">\n            <h2>Excel Export'
    if insert_before in c:
        c = c.replace(insert_before, button_html + '        ' + insert_before, 1)
        print("  Added report button in Reports tab.")
    else:
        # Try alternative
        insert_before2 = 'Excel Export (Monthly Report)'
        if insert_before2 in c:
            idx = c.find(insert_before2)
            container_start = c.rfind('<div class="container">', 0, idx)
            c = c[:container_start] + button_html + '\n        ' + c[container_start:]
            print("  Added report button (alternative insertion).")
        else:
            print("  WARNING: Could not find Excel Export section. Adding at end of Reports tab.")
            insert_end = '<!-- Existing Standard Reports -->'
            if insert_end in c:
                c = c.replace(insert_end, button_html + '\n        ' + insert_end, 1)

# 3. Add JavaScript functions
js = r"""
    async function generateMonthlyReport() {
        var reportContent = document.getElementById('reportContent');
        var reportModal = document.getElementById('reportModal');
        
        reportContent.innerHTML = '<p style="text-align:center; padding:50px; color:#7f8c8d;">Generating monthly report... Fetching data from multiple sources...</p>';
        reportModal.style.display = 'block';
        
        var propFilter = getPropertyFilter();
        var headers = getAuthHeaders();
        var monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        var now = new Date();
        var reportPeriod = monthNames[now.getMonth()] + ' ' + now.getFullYear();
        var reportDate = now.getDate() + ' ' + monthNames[now.getMonth()] + ' ' + now.getFullYear();
        var propName = 'All Properties';
        var propDD = document.getElementById('propertyFilter');
        if (propDD && propDD.value) { var opt = propDD.options[propDD.selectedIndex]; if (opt) propName = opt.text.split(' (')[0]; }
        
        // Fetch all data in parallel
        var results = await Promise.allSettled([
            fetch('/dashboard-stats/' + propFilter, {headers: headers}).then(function(r){return r.json()}),
            fetch('/recons', {headers: headers}).then(function(r){return r.json()}),
            fetch('/arrears-aging/' + propFilter, {headers: headers}).then(function(r){return r.json()}),
            fetch('/all-tenants/' + propFilter, {headers: headers}).then(function(r){return r.json()}),
            fetch('/all-meters/' + propFilter, {headers: headers}).then(function(r){return r.json()}),
            fetch('/tariffs/' + propFilter, {headers: headers}).then(function(r){return r.json()}),
            fetch('/financial-report/' + propFilter, {headers: headers}).then(function(r){return r.json()})
        ]);
        
        var stats = results[0].status === 'fulfilled' ? results[0].value : null;
        var recons = results[1].status === 'fulfilled' ? results[1].value : null;
        var aging = results[2].status === 'fulfilled' ? results[2].value : null;
        var tenants = results[3].status === 'fulfilled' ? results[3].value : null;
        var meters = results[4].status === 'fulfilled' ? results[4].value : null;
        var tariffs = results[5].status === 'fulfilled' ? results[5].value : null;
        var financial = results[6].status === 'fulfilled' ? results[6].value : null;
        
        // Parse data
        var tenantList = tenants ? (tenants.tenants || []) : [];
        var meterList = meters ? (meters.meters || []) : [];
        var reconList = recons ? (recons.recons || []) : [];
        var agingList = aging ? (aging.aging || aging.report || []) : [];
        var tariffList = tariffs ? (tariffs.tariffs || []) : [];
        var consumptionData = financial ? (financial.consumption || []) : [];
        
        var totalUnits = tenantList.length;
        var activeTenants = tenantList.filter(function(t){return (t.status||'ACTIVE').toUpperCase()==='ACTIVE'}).length;
        var vacantUnits = totalUnits - activeTenants;
        var totalMeters = meterList.length;
        var metersOnline = meterList.filter(function(m){return m.is_active}).length;
        var metersOffline = totalMeters - metersOnline;
        
        var grossSales = (stats && stats.revenue) ? (stats.revenue.total_revenue || 0) : 0;
        var collectionRate = (stats && stats.revenue) ? (stats.revenue.collection_rate || 0) : 0;
        var totalArrears = (stats && stats.arrears) ? (stats.arrears.total_arrears || 0) : 0;
        
        var vendingFeePct = 0.10;
        var debtService = 120552.50;
        var vendingFee = grossSales * vendingFeePct;
        var netToEscrow = grossSales - vendingFee;
        var remittance = netToEscrow - debtService;
        
        var latestRecon = reconList.length > 0 ? reconList[0] : null;
        
        var totalAging = agingList.reduce(function(s,t){return s + (t.total_arrears||0)}, 0);
        var agingCurrent = agingList.reduce(function(s,t){return s + (t.current||t.bucket_30||0)}, 0);
        var aging30 = agingList.reduce(function(s,t){return s + (t.days_30||t.bucket_60||0)}, 0);
        var aging60 = agingList.reduce(function(s,t){return s + (t.days_60||t.bucket_90||0)}, 0);
        var aging90 = agingList.reduce(function(s,t){return s + (t.days_90||t.bucket_over_90||0)}, 0);
        
        var sortedConsumption = consumptionData.slice().sort(function(a,b){return (b.value||0) - (a.value||0)});
        var top5 = sortedConsumption.slice(0, 5);
        var bottom5 = sortedConsumption.slice(-5).reverse();
        var totalConsumption = consumptionData.reduce(function(s,c){return s + (c.value||0)}, 0);
        var avgConsumption = activeTenants > 0 ? totalConsumption / activeTenants : 0;
        
        var valveOpen = meterList.filter(function(m){return (m.valve_status||'OPEN')==='OPEN'}).length;
        var valveTrickle = meterList.filter(function(m){return m.valve_status==='TRICKLE'}).length;
        var valveClosed = meterList.filter(function(m){return m.valve_status==='CLOSED'}).length;
        
        var vacantTenants = tenantList.filter(function(t){return (t.status||'').toUpperCase()==='VACATED'});
        
        // Build report
        var html = '';
        
        // Helper functions
        function esc(s) { return String(s||'').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
        function fmt(v) { return parseFloat(v||0).toFixed(2); }
        function sec(title) { return '<h3 style="background:#2c3e50;color:white;padding:10px;margin:20px 0 10px 0;border-radius:4px;">' + title + '</h3>'; }
        function mock() { return '<div class="report-mock-banner">Pending LoRaWAN Integration — Sample Data Shown</div>'; }
        function kv(l,v) { return '<td style="border:1px solid #ddd;padding:8px;"><strong>'+l+'</strong></td><td style="border:1px solid #ddd;padding:8px;">'+v+'</td>'; }
        
        // Header
        html += '<div style="text-align:center;margin-bottom:20px;border-bottom:3px solid #2c3e50;padding-bottom:15px;">';
        html += '<h1 style="margin:0;color:#2c3e50;font-size:1.5em;">ELUP SERVICES (PTY) LTD</h1>';
        html += '<h2 style="margin:5px 0;color:#7f8c8d;font-size:1.2em;">MONTHLY METERING MANAGEMENT REPORT</h2>';
        html += '</div>';
        
        // Metadata
        html += '<div style="margin-bottom:20px;font-size:0.9em;line-height:1.8;">';
        html += '<strong>Property:</strong> ' + esc(propName) + '<br>';
        html += '<strong>Report Period:</strong> ' + reportPeriod + '<br>';
        html += '<strong>Report Date:</strong> ' + reportDate + '<br>';
        html += '<strong>Prepared for:</strong> Instratin Property Developers<br>';
        html += '<strong>Prepared by:</strong> ELUP Services (Pty) Ltd';
        html += '</div>';
        
        // 1. Executive Summary
        html += sec('EXECUTIVE SUMMARY');
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
        html += '<tr>' + kv('Total Units', totalUnits) + kv('Active Tenants', activeTenants + ' (' + (totalUnits>0?(activeTenants/totalUnits*100).toFixed(1):0) + '%)') + '</tr>';
        html += '<tr>' + kv('Vacant Units', vacantUnits + ' (' + (totalUnits>0?(vacantUnits/totalUnits*100).toFixed(1):0) + '%)') + kv('Total Meters', totalMeters) + '</tr>';
        html += '<tr>' + kv('Meters Online', metersOnline + ' (' + (totalMeters>0?(metersOnline/totalMeters*100).toFixed(1):0) + '%)') + kv('Meters Offline', metersOffline) + '</tr>';
        html += '<tr>' + kv('Gross Water Sales', 'R ' + fmt(grossSales)) + kv('Vending Fees (10%)', 'R ' + fmt(vendingFee)) + '</tr>';
        html += '<tr>' + kv('Net Collections', 'R ' + fmt(netToEscrow)) + kv('ELUP Debt Service', 'R ' + fmt(debtService)) + '</tr>';
        html += '<tr>' + kv('Remittance to Instratin', 'R ' + fmt(remittance)) + kv('Collection Rate', collectionRate.toFixed(1) + '%') + '</tr>';
        html += '</table>';
        
        // 2. Financial Waterfall
        html += sec('FINANCIAL WATERFALL SUMMARY');
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
        html += '<tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Item</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">Amount</th></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">Gross Tenant Purchases</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">R ' + fmt(grossSales) + '</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">Less: Vending Fee (10% at POS)</td><td style="border:1px solid #ddd;padding:8px;text-align:right;color:red;">(R ' + fmt(vendingFee) + ')</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;"><strong>Net to Escrow Account</strong></td><td style="border:1px solid #ddd;padding:8px;text-align:right;"><strong>R ' + fmt(netToEscrow) + '</strong></td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">Less: ELUP Debt Service (1st Priority)</td><td style="border:1px solid #ddd;padding:8px;text-align:right;color:red;">(R ' + fmt(debtService) + ')</td></tr>';
        if (remittance >= 0) {
            html += '<tr><td style="border:1px solid #ddd;padding:8px;"><strong>Remittance to Instratin (2nd Priority)</strong></td><td style="border:1px solid #ddd;padding:8px;text-align:right;color:green;"><strong>R ' + fmt(remittance) + '</strong></td></tr>';
        } else {
            html += '<tr><td style="border:1px solid #ddd;padding:8px;color:red;"><strong>SHORTFALL (Instratin to fund)</strong></td><td style="border:1px solid #ddd;padding:8px;text-align:right;color:red;"><strong>R ' + fmt(Math.abs(remittance)) + '</strong></td></tr>';
        }
        html += '</table>';
        html += '<p style="font-size:0.85em;color:#7f8c8d;">Debt service amount: R' + fmt(debtService) + ' (5-year option). Vending fee: 10% at point of sale. Instratin guarantees the monthly debt service regardless of collection levels.</p>';
        
        // 3. Municipal Reconciliation
        html += sec('MUNICIPAL RECONCILIATION');
        if (latestRecon) {
            html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
            html += '<tr>' + kv('Billing Period', esc(latestRecon.month||'N/A')) + kv('Utility Type', esc(latestRecon.utility_type||'N/A')) + '</tr>';
            html += '<tr>' + kv('Municipal Bulk Units', latestRecon.municipal_units||latestRecon.muni_units||'N/A') + kv('Sub-Meter Total', latestRecon.submeter_units||latestRecon.sub_units||'N/A') + '</tr>';
            html += '<tr>' + kv('Variance', latestRecon.variance||'N/A') + kv('Status', '<span style="color:' + (latestRecon.status==='LOSS'?'red':(latestRecon.status==='GAIN'?'orange':'green')) + ';font-weight:bold;">' + esc(latestRecon.status||'N/A') + '</span>') + '</tr>';
            html += '</table>';
        } else {
            html += '<p style="color:#7f8c8d;">No reconciliation records available. Generate a reconciliation from the Reconciliation report section.</p>';
        }
        
        // 4. Consumption Summary
        html += sec('CONSUMPTION SUMMARY');
        if (consumptionData.length > 0) {
            html += '<p><strong>Total Consumption:</strong> R ' + fmt(totalConsumption) + ' | <strong>Average per Unit:</strong> R ' + fmt(avgConsumption) + '</p>';
            html += '<h4 style="color:#2c3e50;">Top 5 Consumers:</h4>';
            html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Tenant</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">Consumption (R)</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">% of Average</th></tr>';
            top5.forEach(function(c) {
                var pct = avgConsumption > 0 ? Math.round((c.value / avgConsumption) * 100) : 0;
                var flag = pct > 150 ? ' <span style="color:red;font-size:0.85em;">Flag: above normal</span>' : '';
                html += '<tr><td style="border:1px solid #ddd;padding:8px;">' + esc(c.tenant) + '</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">R ' + fmt(c.value) + '</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">' + pct + '%' + flag + '</td></tr>';
            });
            html += '</table>';
            html += '<h4 style="color:#2c3e50;">Bottom 5 Consumers:</h4>';
            html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Tenant</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">Consumption (R)</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">% of Average</th></tr>';
            bottom5.forEach(function(c) {
                var pct = avgConsumption > 0 ? Math.round((c.value / avgConsumption) * 100) : 0;
                var flag = pct < 25 ? ' <span style="color:orange;font-size:0.85em;">Flag: below normal</span>' : '';
                html += '<tr><td style="border:1px solid #ddd;padding:8px;">' + esc(c.tenant) + '</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">R ' + fmt(c.value) + '</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">' + pct + '%' + flag + '</td></tr>';
            });
            html += '</table>';
        } else {
            html += '<p style="color:#7f8c8d;">No consumption data available for this period.</p>';
        }
        
        // 5. Alarm Summary (mock)
        html += sec('ALARM SUMMARY');
        html += mock();
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Unit</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Alarm Type</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Details</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Severity</th></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">405</td><td style="border:1px solid #ddd;padding:8px;">Water Leakage</td><td style="border:1px solid #ddd;padding:8px;">Continuous flow 36h, 0.3 kL/h</td><td style="border:1px solid #ddd;padding:8px;color:red;font-weight:bold;">HIGH</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">218</td><td style="border:1px solid #ddd;padding:8px;">Water Leakage</td><td style="border:1px solid #ddd;padding:8px;">Continuous flow 28h, 0.2 kL/h</td><td style="border:1px solid #ddd;padding:8px;color:red;font-weight:bold;">HIGH</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">315</td><td style="border:1px solid #ddd;padding:8px;">Low Battery</td><td style="border:1px solid #ddd;padding:8px;">Battery at 3.1V</td><td style="border:1px solid #ddd;padding:8px;color:orange;font-weight:bold;">MEDIUM</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">812</td><td style="border:1px solid #ddd;padding:8px;">Tamper Detection</td><td style="border:1px solid #ddd;padding:8px;">Magnetic interference, valve auto-closed</td><td style="border:1px solid #ddd;padding:8px;color:red;font-weight:bold;">HIGH</td></tr>';
        html += '</table>';
        html += '<p style="font-size:0.85em;color:#7f8c8d;">Active alarms: 4 | Resolved this month: 0 | Outstanding actions: 3 (plumber dispatch for Units 405, 218; physical inspection for Unit 812)</p>';
        
        // 6. Meter Health
        html += sec('METER HEALTH DASHBOARD');
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
        html += '<tr>' + kv('Total Meters', totalMeters) + kv('Online', metersOnline + ' (' + (totalMeters>0?(metersOnline/totalMeters*100).toFixed(1):0) + '%)') + '</tr>';
        html += '<tr>' + kv('Offline', metersOffline) + kv('Valve Open', valveOpen) + '</tr>';
        html += '<tr>' + kv('Valve Trickle (arrears)', valveTrickle) + kv('Valve Closed (vacant)', valveClosed) + '</tr>';
        html += '</table>';
        html += mock();
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr>' + kv('Battery Normal (>3.4V)', Math.round(totalMeters*0.98)) + kv('Battery Warning (3.2-3.4V)', Math.round(totalMeters*0.015)) + '</tr>';
        html += '<tr>' + kv('Battery Low (3.0-3.2V)', Math.round(totalMeters*0.005)) + kv('Battery Critical (<3.0V)', 0) + '</tr></table>';
        if (metersOffline > 0) {
            html += '<p style="color:#e74c3c;font-size:0.9em;"><strong>Offline Meters:</strong> ' + metersOffline + ' meters not communicating. Investigation required.</p>';
        }
        
        // 7. Financial Summary
        html += sec('FINANCIAL SUMMARY');
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
        html += '<tr>' + kv('Gross Sales', 'R ' + fmt(grossSales)) + kv('Collection Rate', collectionRate.toFixed(1) + '%') + '</tr>';
        html += '<tr>' + kv('Net Collections', 'R ' + fmt(netToEscrow)) + kv('Total Arrears', 'R ' + fmt(totalAging)) + '</tr>';
        html += '</table>';
        html += '<h4 style="color:#2c3e50;">Arrears Aging (FIFO):</h4>';
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;">Bucket</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;">Tenants</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;">Amount</th></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">Current (0-30 days)</td><td style="border:1px solid #ddd;padding:8px;">' + agingList.length + '</td><td style="border:1px solid #ddd;padding:8px;">R ' + fmt(agingCurrent) + '</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">31-60 days</td><td style="border:1px solid #ddd;padding:8px;">—</td><td style="border:1px solid #ddd;padding:8px;">R ' + fmt(aging30) + '</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">61-90 days</td><td style="border:1px solid #ddd;padding:8px;">—</td><td style="border:1px solid #ddd;padding:8px;">R ' + fmt(aging60) + '</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;">Over 90 days</td><td style="border:1px solid #ddd;padding:8px;">—</td><td style="border:1px solid #ddd;padding:8px;">R ' + fmt(aging90) + '</td></tr>';
        html += '<tr><td style="border:1px solid #ddd;padding:8px;"><strong>Total</strong></td><td style="border:1px solid #ddd;padding:8px;"><strong>' + agingList.length + '</strong></td><td style="border:1px solid #ddd;padding:8px;"><strong>R ' + fmt(totalAging) + '</strong></td></tr>';
        html += '</table>';
        
        // 8. Vacancy Report
        html += sec('VACANCY REPORT');
        html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;">';
        html += '<tr>' + kv('Total Units', totalUnits) + kv('Occupied', activeTenants) + '</tr>';
        html += '<tr>' + kv('Vacant', vacantUnits) + kv('Occupancy Rate', (totalUnits>0?(activeTenants/totalUnits*100).toFixed(1):0) + '%') + '</tr>';
        html += '</table>';
        if (vacantTenants.length > 0 && vacantTenants.length <= 20) {
            html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Unit</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Tenant Name</th></tr>';
            vacantTenants.forEach(function(t) {
                html += '<tr><td style="border:1px solid #ddd;padding:8px;">' + esc(t.unit_number||'N/A') + '</td><td style="border:1px solid #ddd;padding:8px;">' + esc((t.first_name||'') + ' ' + (t.last_name||'')) + '</td></tr>';
            });
            html += '</table>';
        }
        var infraLevy = vacantUnits * 103.21;
        html += '<p style="font-size:0.9em;">Infrastructure charges for vacant units: <strong>R ' + fmt(infraLevy) + '</strong> (' + vacantUnits + ' units x R103.21) — for Instratin\'s account</p>';
        
        // 9. Tariff Summary
        html += sec('TARIFF SUMMARY');
        if (tariffList.length > 0) {
            html += '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;"><tr><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Name</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Type</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:left;">Structure</th><th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;text-align:right;">Rate</th></tr>';
            tariffList.forEach(function(t) {
                var rate = t.rate_flat || t.flat_rate || 0;
                var structure = t.structure || t.structure_type || 'FLAT';
                html += '<tr><td style="border:1px solid #ddd;padding:8px;">' + esc(t.name) + '</td><td style="border:1px solid #ddd;padding:8px;">' + esc(t.meter_type) + '</td><td style="border:1px solid #ddd;padding:8px;">' + esc(structure) + '</td><td style="border:1px solid #ddd;padding:8px;text-align:right;">R ' + fmt(rate) + '</td></tr>';
            });
            html += '</table>';
        } else {
            html += '<p style="color:#7f8c8d;">No tariffs configured.</p>';
        }
        
        // 10. Recommendations
        html += sec('SUMMARY OF RECOMMENDATIONS');
        var recs = [];
        if (latestRecon && latestRecon.status === 'LOSS') recs.push('Investigate water loss — variance of ' + (latestRecon.variance||'N/A') + ' units identified. Dispatch plumber for leak investigation.');
        if (vacantUnits > totalUnits * 0.05) recs.push('Occupancy campaign recommended — ' + vacantUnits + ' vacant units (' + (totalUnits>0?(vacantUnits/totalUnits*100).toFixed(1):0) + '% vacancy rate).');
        if (totalAging > 50000) recs.push('Follow up on arrears — R' + fmt(totalAging) + ' outstanding across ' + agingList.length + ' tenants.');
        if (metersOffline > 0) recs.push('Investigate ' + metersOffline + ' offline meter(s) — technician dispatch recommended.');
        if (collectionRate < 80) recs.push('Improve collection rate — currently at ' + collectionRate.toFixed(1) + '%.');
        recs.push('Replace CIU batteries showing low battery warning (mock data — pending LoRaWAN integration).');
        recs.push('Review arrears follow-up for tenants in 31-60 day bucket.');
        
        html += '<ol style="line-height:2;">';
        recs.forEach(function(r) { html += '<li>' + r + '</li>'; });
        html += '</ol>';
        
        // Footer
        html += '<div style="margin-top:30px;padding-top:15px;border-top:2px solid #2c3e50;font-size:0.85em;color:#7f8c8d;">';
        html += '<p><strong>Report prepared by:</strong> ELUP Services (Pty) Ltd<br>';
        html += '<strong>Contact:</strong> Joel Mpshe, Director<br>';
        html += 'This report is generated automatically by the ELUP Utilities Management Platform.</p>';
        html += '</div>';
        
        // Print button
        html += '<button class="report-print-btn" onclick="printMonthlyReport()">Print Report</button>';
        
        reportContent.innerHTML = html;
    }
    
    function printMonthlyReport() {
        var content = document.getElementById('reportContent').innerHTML;
        var win = window.open('', '_blank');
        win.document.write('<html><head><title>Monthly Management Report</title>');
        win.document.write('<style>body{font-family:Arial,sans-serif;padding:30px;color:#2c3e50;}');
        win.document.write('table{width:100%;border-collapse:collapse;}');
        win.document.write('th,td{border:1px solid #ddd;padding:8px;text-align:left;}');
        win.document.write('th{background:#f8f9fa;}');
        win.document.write('h3{background:#2c3e50;color:white;padding:10px;border-radius:4px;}');
        win.document.write('.report-mock-banner{background:#fff3cd;color:#856404;padding:5px 10px;border-radius:4px;font-size:0.85em;display:inline-block;}');
        win.document.write('.report-print-btn{display:none;}');
        win.document.write('</style></head><body>' + content + '</body></html>');
        win.document.close();
        win.focus();
        setTimeout(function() { win.print(); }, 500);
    }
"""

idx = c.rfind('</script>')
if idx != -1 and 'function generateMonthlyReport' not in c:
    c = c[:idx] + js + '\n' + c[idx:]
    print("  Added generateMonthlyReport and printMonthlyReport functions.")
else:
    print("  Functions already exist or could not find script end.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Press Ctrl+F5 and test.")
print("Go to Reports tab -> click 'Generate Monthly Report'")
print("Report displays in modal with all 10 sections.")
print("Click 'Print Report' to print or save as PDF.")
print("\nSections with REAL data:")
print("  - Executive Summary (from dashboard stats)")
print("  - Financial Waterfall (calculated from revenue)")
print("  - Municipal Reconciliation (from reconciliation records)")
print("  - Consumption Summary (from financial report)")
print("  - Financial Summary + Arrears Aging (from aging data)")
print("  - Vacancy Report (from tenant status)")
print("  - Tariff Summary (from tariff config)")
print("  - Recommendations (auto-generated)")
print("\nSections with MOCK data (pending LoRaWAN):")
print("  - Alarm Summary (4 mock alarms)")
print("  - Meter Health (battery + communication mock)")