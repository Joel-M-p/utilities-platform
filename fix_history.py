print("Fixing History tab — separating Purchases from Consumption...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Add CSS for consumption bar chart (if not already present) ===
if '.consumption-bar' not in c:
    css = """
        .consumption-bar { display: flex; align-items: flex-end; height: 100px; gap: 3px; margin-top: 10px; }
        .consumption-bar-item { flex: 1; background: linear-gradient(180deg, #e74c3c, #c0392b); border-radius: 3px 3px 0 0; min-height: 3px; }
        .consumption-labels { display: flex; gap: 3px; margin-top: 5px; }
        .consumption-label-item { flex: 1; text-align: center; font-size: 0.65em; color: #7f8c8d; }
    """
    c = c.replace('<style>', '<style>\n' + css, 1)
    print("  Added consumption chart CSS.")

# === 2. Replace the History screen ===
start = c.find('<!-- SCREEN 4: HISTORY')
if start == -1:
    start = c.find('id="screen-history"')

# Find end marker
end = c.find('<!-- SCREEN 5:', start)
if end == -1:
    end = c.find('id="screen-utilities"', start)
if end == -1:
    end = c.find('<!-- Bottom Navigation', start)

if start != -1 and end != -1:
    new_history = """<!-- SCREEN 4: HISTORY -->
    <div id="screen-history" class="screen">

        <div class="card">
            <h3>Monthly Spending Summary</h3>
            <div id="summaryChartContainer" class="summary-chart-container">
                <div class="pie-chart" id="monthPieChart"></div>
                <div class="summary-legend" id="monthLegend">
                    <p style="color:#7f8c8d; margin:0; font-size:0.9em; text-align:center;">No spending data for this month yet.</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Daily Consumption (Usage)</h3>
            <div id="consumptionBarChart">
                <p style="text-align:center; color:#7f8c8d; font-size:0.9em;">Loading consumption data...</p>
            </div>
        </div>

        <div class="card">
            <h3>Purchases & Top-ups</h3>
            <p style="font-size:0.8em; color:#7f8c8d; margin:0 0 10px 0;">Wallet top-ups and utility token purchases</p>
            <div id="incomeTxnList">
                <p style="text-align:center; color:#7f8c8d;">Loading transactions...</p>
            </div>
        </div>

        <div class="card">
            <h3>Consumption & Bills</h3>
            <p style="font-size:0.8em; color:#7f8c8d; margin:0 0 10px 0;">Actual usage deductions, bills, and rent charges</p>
            <div id="expenseTxnList">
                <p style="text-align:center; color:#7f8c8d;">Loading transactions...</p>
            </div>
        </div>
    </div>

    """
    c = c[:start] + new_history + c[end:]
    print("  Replaced History screen with 4 cards.")
else:
    print("  WARNING: Could not find History screen markers.")

# === 3. Add overridden tLoadTransactions function ===
idx = c.rfind('</script>')
if idx != -1:
    new_func = r"""
    // OVERRIDDEN: Separates Purchases from Consumption + adds daily chart
    async function tLoadTransactions() {
        var incomeList = document.getElementById('incomeTxnList');
        var expenseList = document.getElementById('expenseTxnList');
        var pieChart = document.getElementById('monthPieChart');
        var legendDiv = document.getElementById('monthLegend');
        var consumptionChart = document.getElementById('consumptionBarChart');

        try {
            var r = await fetch('/transactions/' + currentTenantId, { headers: getAuthHeaders() });
            if (!r.ok) throw new Error("Failed");
            var d = await r.json();

            if (!d.transactions || d.transactions.length === 0) {
                incomeList.innerHTML = '<p style="text-align:center; color:#7f8c8d;">No transactions yet.</p>';
                expenseList.innerHTML = '';
                pieChart.style.background = '#eee';
                legendDiv.innerHTML = '<p style="color:#7f8c8d; margin:0; font-size:0.9em; text-align:center;">No data yet.</p>';
                if(consumptionChart) consumptionChart.innerHTML = '<p style="color:#7f8c8d; text-align:center; font-size:0.9em;">No consumption data yet.</p>';
                return;
            }

            var now = new Date();
            var monthElec = 0, monthWater = 0, monthRent = 0, totalSpend = 0;
            var dailyUsage = {};
            var purchasesHtml = '';
            var consumptionHtml = '';

            d.transactions.slice(0, 50).forEach(function(t) {
                var typeUpper = (t.type || '').toUpperCase();
                var isTopup = typeUpper.indexOf('TOPUP') >= 0 || typeUpper.indexOf('PAYMENT') >= 0;
                var isPurchase = typeUpper.indexOf('PURCHASE') >= 0;
                var isUsage = typeUpper.indexOf('USAGE') >= 0 || typeUpper.indexOf('BILL') >= 0;
                var isRent = typeUpper.indexOf('RENT') >= 0;
                var isExpense = isPurchase || isUsage || isRent;

                var sign = isExpense ? '- R ' : '+ R ';
                var colorClass = isExpense ? 'text-danger' : 'text-success';
                var typeText = (t.type || '').replace(/_/g, ' ');

                var txDate = new Date(t.date);
                var inThisMonth = (txDate.getMonth() === now.getMonth() && txDate.getFullYear() === now.getFullYear());

                if (inThisMonth && isExpense) {
                    totalSpend += Math.abs(t.amount);
                    if (typeUpper.indexOf('ELEC') >= 0) monthElec += Math.abs(t.amount);
                    else if (typeUpper.indexOf('WATER') >= 0) monthWater += Math.abs(t.amount);
                    else if (isRent) monthRent += Math.abs(t.amount);

                    if (isUsage) {
                        var dayKey = String(txDate.getDate());
                        if (!dailyUsage[dayKey]) dailyUsage[dayKey] = 0;
                        dailyUsage[dayKey] += Math.abs(t.amount);
                    }
                }

                var itemHtml = '<div class="txn-item"><div><div style="font-weight:600;">' + typeText + '</div><div class="txn-date">' + t.date + '</div></div><div class="txn-amount ' + colorClass + '">' + sign + Math.abs(t.amount).toFixed(2) + '</div></div>';

                if (isTopup || isPurchase) {
                    purchasesHtml += itemHtml;
                }
                if (isUsage || isRent) {
                    consumptionHtml += itemHtml;
                }
            });

            incomeList.innerHTML = purchasesHtml || '<p style="text-align:center; color:#7f8c8d;">No purchases or top-ups yet.</p>';
            expenseList.innerHTML = consumptionHtml || '<p style="text-align:center; color:#7f8c8d;">No consumption or bills yet.</p>';

            // Pie chart (spending by category)
            if (totalSpend > 0) {
                var elecPct = (monthElec / totalSpend) * 100;
                var waterPct = (monthWater / totalSpend) * 100;
                pieChart.style.background = 'conic-gradient(#f39c12 0% ' + elecPct + '%, #3498db ' + elecPct + '% ' + (elecPct + waterPct) + '%, #2c3e50 ' + (elecPct + waterPct) + '% 100%)';
                legendDiv.innerHTML = '<div class="legend-item"><div class="legend-dot" style="background:#f39c12;"></div>Electricity: R ' + monthElec.toFixed(2) + '</div><div class="legend-item"><div class="legend-dot" style="background:#3498db;"></div>Water: R ' + monthWater.toFixed(2) + '</div><div class="legend-item"><div class="legend-dot" style="background:#2c3e50;"></div>Rent: R ' + monthRent.toFixed(2) + '</div><div class="legend-item" style="font-weight:bold; margin-top:5px; border-top:1px solid #eee; padding-top:5px;"><div class="legend-dot" style="background:transparent;"></div>Total: R ' + totalSpend.toFixed(2) + '</div>';
            } else {
                pieChart.style.background = '#eee';
                legendDiv.innerHTML = '<p style="color:#7f8c8d; margin:0; font-size:0.9em; text-align:center;">No spending this month.</p>';
            }

            // Daily consumption bar chart
            if (consumptionChart) {
                var days = Object.keys(dailyUsage).sort(function(a, b) { return parseInt(a) - parseInt(b); });
                if (days.length > 0) {
                    var maxVal = 0;
                    days.forEach(function(d) { if(dailyUsage[d] > maxVal) maxVal = dailyUsage[d]; });
                    var chartHtml = '<div class="consumption-bar">';
                    days.forEach(function(day) {
                        var h = maxVal > 0 ? (dailyUsage[day] / maxVal) * 100 : 0;
                        chartHtml += '<div class="consumption-bar-item" style="height:' + h + '%;" title="Day ' + day + ': R' + dailyUsage[day].toFixed(2) + '"></div>';
                    });
                    chartHtml += '</div><div class="consumption-labels">';
                    days.forEach(function(day) {
                        chartHtml += '<div class="consumption-label-item">' + day + '</div>';
                    });
                    chartHtml += '</div>';
                    var totalUsage = 0;
                    days.forEach(function(d) { totalUsage += dailyUsage[d]; });
                    consumptionChart.innerHTML = '<div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span style="font-size:0.85em; color:#7f8c8d;">Usage this month</span><span style="font-weight:bold; color:#e74c3c;">R ' + totalUsage.toFixed(2) + '</span></div>' + chartHtml;
                } else {
                    consumptionChart.innerHTML = '<p style="color:#7f8c8d; text-align:center; font-size:0.9em;">No consumption recorded this month.</p>';
                }
            }
        } catch (e) {
            incomeList.innerHTML = '<p style="text-align:center; color:#e74c3c;">Error loading transactions.</p>';
            expenseList.innerHTML = '';
        }
    }
"""
    c = c[:idx] + new_func + '\n' + c[idx:]
    print("  Added overridden tLoadTransactions function.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Press Ctrl+F5 and test.")
print("  History tab now shows 4 cards:")
print("  1. Monthly Spending Summary (pie chart)")
print("  2. Daily Consumption (bar chart — actual usage per day)")
print("  3. Purchases & Top-ups (token purchases + wallet top-ups)")
print("  4. Consumption & Bills (usage deductions + rent)")