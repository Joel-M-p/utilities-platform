import shutil

print("Adding smart meter UI to dashboard.html...")
shutil.copy('dashboard.html', 'dashboard.html.bak_demo')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add CSS for smart meter cards
if 'smart-meter-card' not in c:
    css = """
        .smart-meter-card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #3498db; }
        .smart-meter-card h3 { color: #2c3e50; margin: 0 0 15px 0; font-size: 1.1em; }
        .meter-health-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
        .meter-health-item { background: #f8f9fa; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .meter-health-item .serial { font-weight: bold; color: #2c3e50; font-size: 0.9em; }
        .meter-health-item .battery { font-size: 1.1em; font-weight: bold; }
        .battery-good { color: #27ae60; }
        .battery-warn { color: #f39c12; }
        .battery-critical { color: #e74c3c; }
        .alarm-card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #e74c3c; }
        .alarm-item { padding: 12px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .alarm-item:last-child { border-bottom: none; }
        .alarm-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75em; font-weight: bold; color: white; }
        .alarm-high { background: #e74c3c; }
        .alarm-medium { background: #f39c12; }
        .alarm-low { background: #7f8c8d; }
        .demo-banner { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; font-size: 0.9em; }
        .demo-banner strong { font-size: 1.1em; }
    """
    c = c.replace('<style>', css + '\n<style>', 1)
    print("  Added CSS.")

# 2. Add Smart Meter Health card + Active Alarms card after KPI grid
if 'smartMeterHealth' not in c:
    html = """
        <!-- SMART METER HEALTH CARD -->
        <div class="smart-meter-card">
            <h3>🔋 Smart Meter Health Dashboard</h3>
            <div class="meter-health-grid" id="smartMeterHealth">
                <p style="color:#7f8c8d; font-size:0.9em;">Loading meter health data...</p>
            </div>
        </div>

        <!-- ACTIVE ALARMS CARD -->
        <div class="alarm-card">
            <h3>🚨 Active Meter Alarms</h3>
            <div id="activeAlarms">
                <p style="color:#7f8c8d; font-size:0.9em;">Loading alarms...</p>
            </div>
        </div>

        <!-- DEMO BANNER -->
        <div class="demo-banner">
            <strong>⚡ IoT Integration Ready</strong> — This system supports LoRaWAN smart meters with real-time data, automated valve control, and instant alarm notifications.
        </div>
"""
    # Insert after the trends container
    c = c.replace(
        '</div>\n\n        <!-- USER MANAGEMENT CARD',
        '</div>\n' + html + '\n        <!-- USER MANAGEMENT CARD'
    )
    print("  Added smart meter health + alarms cards.")

# 3. Add JavaScript functions to load mock data
if 'loadSmartMeterHealth' not in c:
    js = """
    // --- SMART METER DEMO FUNCTIONS ---
    async function loadSmartMeterHealth() {
        const container = document.getElementById('smartMeterHealth');
        try {
            const r = await fetch('/all-meters/' + getPropertyFilter(), { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error('Failed');
            
            let html = '';
            d.meters.slice(0, 12).forEach(m => {
                // Mock battery voltage for demo
                const mockBattery = (3.2 + Math.random() * 0.4).toFixed(2);
                let battClass = 'battery-good';
                let battIcon = '🔋';
                if (parseFloat(mockBattery) < 3.0) { battClass = 'battery-critical'; battIcon = '🪫'; }
                else if (parseFloat(mockBattery) < 3.2) { battClass = 'battery-warn'; battIcon = '⚠️'; }
                
                // Mock last comms time
                const minsAgo = Math.floor(Math.random() * 30) + 1;
                let statusColor = minsAgo < 5 ? '#27ae60' : (minsAgo < 15 ? '#f39c12' : '#e74c3c');
                
                html += '<div class="meter-health-item">' +
                    '<div><div class="serial">' + (m.serial_number || 'N/A') + '</div>' +
                    '<div style="font-size:0.75em; color:#7f8c8d;">' + (m.unit_number || 'N/A') + ' • ' + minsAgo + 'm ago</div></div>' +
                    '<div class="battery ' + battClass + '">' + battIcon + ' ' + mockBattery + 'V</div>' +
                    '</div>';
            });
            container.innerHTML = html || '<p style="color:#7f8c8d;">No active meters.</p>';
        } catch (e) { container.innerHTML = '<p style="color:#e74c3c;">Error: ' + e.message + '</p>'; }
    }

    async function loadActiveAlarms() {
        const container = document.getElementById('activeAlarms');
        try {
            const r = await fetch('/meter-events/', { headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error('Failed');
            
            if (!d.events || d.events.length === 0) {
                // Show mock alarms for demo
                const mockAlarms = [
                    { serial: 'WM-101', type: 'WATER_LEAKAGE', notes: 'Continuous flow for 26 hours. Flow: 0.3 m³/h', severity: 'HIGH', time: '2h ago' },
                    { serial: 'WM-205', type: 'LOW_BATTERY', notes: 'Battery at 2.9V. Replacement within 30 days.', severity: 'MEDIUM', time: '5h ago' },
                    { serial: 'WM-308', type: 'TAMPER_DETECT', notes: 'Magnetic interference. Valve auto-closed.', severity: 'HIGH', time: '1h ago' },
                    { serial: 'WM-412', type: 'VALVE_FAIL', notes: 'Valve close command failed after 3 retries.', severity: 'HIGH', time: '8h ago' },
                ];
                
                let html = '';
                mockAlarms.forEach(a => {
                    let sevClass = a.severity === 'HIGH' ? 'alarm-high' : (a.severity === 'MEDIUM' ? 'alarm-medium' : 'alarm-low');
                    let icon = a.type.includes('LEAK') ? '💧' : (a.type.includes('BATTERY') ? '🪫' : (a.type.includes('TAMPER') ? '🧲' : '⚠️'));
                    html += '<div class="alarm-item">' +
                        '<div><div style="font-weight:bold; color:#2c3e50;">' + icon + ' ' + a.type.replace(/_/g, ' ') + ' — ' + a.serial + '</div>' +
                        '<div style="font-size:0.85em; color:#7f8c8d;">' + a.notes + ' • ' + a.time + '</div></div>' +
                        '<span class="alarm-badge ' + sevClass + '">' + a.severity + '</span>' +
                        '</div>';
                });
                container.innerHTML = html;
            } else {
                let html = '';
                d.events.slice(0, 5).forEach(a => {
                    let sevClass = 'alarm-high';
                    let icon = '⚠️';
                    html += '<div class="alarm-item">' +
                        '<div><div style="font-weight:bold;">' + icon + ' ' + a.event_type + ' — ' + (a.serial_number || 'N/A') + '</div>' +
                        '<div style="font-size:0.85em; color:#7f8c8d;">' + (a.event_notes || '') + '</div></div>' +
                        '<span class="alarm-badge ' + sevClass + '">ACTIVE</span>' +
                        '</div>';
                });
                container.innerHTML = html;
            }
        } catch (e) {
            // Fallback to mock alarms
            const mockAlarms = [
                { serial: 'WM-101', type: 'WATER_LEAKAGE', notes: 'Continuous flow for 26 hours', severity: 'HIGH', time: '2h ago' },
                { serial: 'WM-205', type: 'LOW_BATTERY', notes: 'Battery at 2.9V', severity: 'MEDIUM', time: '5h ago' },
                { serial: 'WM-308', type: 'TAMPER_DETECT', notes: 'Magnetic interference detected', severity: 'HIGH', time: '1h ago' },
            ];
            let html = '';
            mockAlarms.forEach(a => {
                let sevClass = a.severity === 'HIGH' ? 'alarm-high' : 'alarm-medium';
                let icon = a.type.includes('LEAK') ? '💧' : (a.type.includes('BATTERY') ? '🪫' : '🧲');
                html += '<div class="alarm-item"><div><div style="font-weight:bold;">' + icon + ' ' + a.type.replace(/_/g, ' ') + ' — ' + a.serial + '</div><div style="font-size:0.85em; color:#7f8c8d;">' + a.notes + ' • ' + a.time + '</div></div><span class="alarm-badge ' + sevClass + '">' + a.severity + '</span></div>';
            });
            container.innerHTML = html;
        }
    }
"""
    # Add to loadAllData
    c = c.replace(
        'loadCompanySettings(); loadDashboardStats();',
        'loadCompanySettings(); loadDashboardStats(); loadSmartMeterHealth(); loadActiveAlarms();'
    )
    # Add functions before </script>
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]
    print("  Added JavaScript functions.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Smart meter UI added to dashboard.")
print("Test: http://127.0.0.1:8000/dashboard (Ctrl+F5)")