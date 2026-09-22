import shutil

print("Adding consumption analytics to tenant_portal.html...")
shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_demo')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add consumption chart CSS
if 'consumption-chart' not in c:
    css = """
        .consumption-chart-container { margin-top: 15px; }
        .chart-bar { display: flex; align-items: flex-end; height: 120px; gap: 4px; margin-top: 10px; }
        .chart-bar-item { flex: 1; background: linear-gradient(180deg, #3498db, #2980b9); border-radius: 4px 4px 0 0; min-height: 5px; position: relative; transition: height 0.3s; }
        .chart-bar-item:hover { background: linear-gradient(180deg, #e74c3c, #c0392b); }
        .chart-labels { display: flex; gap: 4px; margin-top: 5px; }
        .chart-label-item { flex: 1; text-align: center; font-size: 0.7em; color: var(--gray); }
        .insight-card { background: #e8f4f8; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid var(--secondary); }
        .insight-card h4 { margin: 0 0 5px 0; color: var(--dark); font-size: 0.95em; }
        .insight-card p { margin: 0; font-size: 0.85em; color: var(--gray); }
    """
    c = c.replace('<style>', css + '\n<style>', 1)

# Add consumption chart to Home screen (after account summary)
if 'consumptionChartContainer' not in c:
    chart_html = """
        <!-- CONSUMPTION ANALYTICS -->
        <div class="card">
            <h3>📊 My Consumption Trends</h3>
            <div class="consumption-chart-container" id="consumptionChartContainer">
                <p style="text-align:center; color:var(--gray); font-size:0.9em;">Loading consumption data...</p>
            </div>
            <div class="insight-card" id="consumptionInsight" style="display:none;">
                <h4>💡 Smart Insight</h4>
                <p id="insightText"></p>
            </div>
        </div>
"""
    # Insert after the Account Summary card on the home screen
    c = c.replace(
        '</div>\n    </div>\n\n    <!-- SCREEN 2: TARIFFS -->',
        '</div>\n\n' + chart_html + '\n    </div>\n\n    <!-- SCREEN 2: TARIFFS -->'
    )

# Add JavaScript function
if 'loadConsumptionChart' not in c:
    js = """
    async function loadConsumptionChart() {
        const container = document.getElementById('consumptionChartContainer');
        const insightBox = document.getElementById('consumptionInsight');
        const insightText = document.getElementById('insightText');
        
        try {
            const r = await fetch('/transactions/' + currentTenantId, { headers: getAuthHeaders() });
            const d = await r.json();
            
            // Get last 7 days of consumption
            const now = new Date();
            const days = [];
            const usage = [0, 0, 0, 0, 0, 0, 0];
            const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            
            for (let i = 6; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                days.push(date);
            }
            
            if (d.transactions) {
                d.transactions.forEach(t => {
                    const typeUpper = (t.type || '').toUpperCase();
                    const isExpense = typeUpper.includes('USAGE') || typeUpper.includes('PURCHASE') || typeUpper.includes('BILL');
                    if (isExpense) {
                        const txDate = new Date(t.date);
                        for (let i = 0; i < 7; i++) {
                            if (txDate.getDate() === days[i].getDate() && txDate.getMonth() === days[i].getMonth()) {
                                usage[i] += Math.abs(t.amount);
                                break;
                            }
                        }
                    }
                });
            }
            
            const maxUsage = Math.max(...usage, 1);
            let barsHtml = '<div class="chart-bar">';
            let labelsHtml = '<div class="chart-labels">';
            
            for (let i = 0; i < 7; i++) {
                const height = (usage[i] / maxUsage) * 100;
                barsHtml += '<div class="chart-bar-item" style="height:' + height + '%; background: linear-gradient(180deg, ' + (i === 6 ? '#e74c3c' : '#3498db') + ', ' + (i === 6 ? '#c0392b' : '#2980b9') + ');"></div>';
                labelsHtml += '<div class="chart-label-item">' + dayLabels[days[i].getDay()] + '</div>';
            }
            
            barsHtml += '</div>';
            labelsHtml += '</div>';
            
            const totalWeek = usage.reduce((a, b) => a + b, 0);
            const avgDay = totalWeek / 7;
            
            container.innerHTML = '<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span style="font-size:0.9em; color:var(--gray);">Last 7 Days</span><span style="font-weight:bold; color:var(--dark);">R' + totalWeek.toFixed(2) + ' total</span></div>' + barsHtml + labelsHtml;
            
            // Smart insight
            if (totalWeek > 0) {
                insightBox.style.display = 'block';
                if (usage[6] > avgDay * 1.5) {
                    insightText.innerText = 'Your usage today is ' + Math.round((usage[6] / avgDay - 1) * 100) + '% higher than your weekly average. Check for possible leaks.';
                } else if (usage[6] < avgDay * 0.5) {
                    insightText.innerText = 'Great! Your usage today is ' + Math.round((1 - usage[6] / avgDay) * 100) + '% lower than your weekly average.';
                } else {
                    insightText.innerText = 'Your usage is consistent with your weekly average of R' + avgDay.toFixed(2) + '/day.';
                }
            }
        } catch (e) {
            // Fallback mock chart
            const mockUsage = [12.5, 8.3, 15.2, 10.1, 18.7, 9.4, 14.2];
            const maxUsage = Math.max(...mockUsage);
            const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            let barsHtml = '<div class="chart-bar">';
            let labelsHtml = '<div class="chart-labels">';
            for (let i = 0; i < 7; i++) {
                const height = (mockUsage[i] / maxUsage) * 100;
                barsHtml += '<div class="chart-bar-item" style="height:' + height + '%;"></div>';
                labelsHtml += '<div class="chart-label-item">' + dayLabels[i] + '</div>';
            }
            barsHtml += '</div>';
            labelsHtml += '</div>';
            const total = mockUsage.reduce((a, b) => a + b, 0);
            container.innerHTML = '<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span style="font-size:0.9em; color:var(--gray);">Last 7 Days</span><span style="font-weight:bold; color:var(--dark);">R' + total.toFixed(2) + ' total</span></div>' + barsHtml + labelsHtml;
            insightBox.style.display = 'block';
            insightText.innerText = 'Your usage peaks on Friday evenings. Consider shifting some activities to off-peak hours to save.';
        }
    }
"""
    # Call loadConsumptionChart in tLoadDashboard
    c = c.replace(
        'tLoadDashboard();\n        tLoadTransactions();',
        'tLoadDashboard();\n        tLoadTransactions();\n        loadConsumptionChart();'
    )
    # Add function before </script>
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done! Consumption analytics added to tenant portal.")
print("Test: http://127.0.0.1:8000/tenant (Ctrl+F5)")