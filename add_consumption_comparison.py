import shutil

print("Adding Complex vs Unit Average comparison...")

# === 1. ADD BACKEND ENDPOINT TO stats.py ===
print("\n1. Adding backend endpoint...")

shutil.copy('api/routers/stats.py', 'api/routers/stats.py.bak')

with open('api/routers/stats.py', 'r', encoding='utf-8') as f:
    stats = f.read()

if 'consumption-comparison' not in stats:
    endpoint = '''

@router.get("/consumption-comparison/{tenant_id}", dependencies=[Depends(verify_token)])
def get_consumption_comparison(tenant_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT property_id FROM tenants WHERE id = %s", (tenant_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")
        property_id = result[0]
        
        # Unit average (last 30 days)
        cursor.execute("""
            SELECT DATE(t.created_at) as day, SUM(ABS(t.amount)) as daily_total
            FROM transactions t
            JOIN wallets w ON t.wallet_id = w.id
            WHERE w.tenant_id = %s AND t.transaction_type LIKE 'USAGE%%'
            AND t.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY day
        """, (tenant_id,))
        unit_daily = [float(r[1]) for r in cursor.fetchall()]
        unit_avg = sum(unit_daily) / len(unit_daily) if unit_daily else 0
        
        # Complex average (all active tenants in property, last 30 days)
        cursor.execute("""
            SELECT DATE(t.created_at) as day, tn.id, SUM(ABS(t.amount)) as daily_total
            FROM transactions t
            JOIN wallets w ON t.wallet_id = w.id
            JOIN tenants tn ON w.tenant_id = tn.id
            WHERE tn.property_id = %s AND tn.status = 'ACTIVE'
            AND t.transaction_type LIKE 'USAGE%%'
            AND t.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY day, tn.id
        """, (property_id,))
        all_daily = [float(r[2]) for r in cursor.fetchall()]
        complex_avg = sum(all_daily) / len(all_daily) if all_daily else 0
        
        if complex_avg > 0:
            pct_diff = ((unit_avg - complex_avg) / complex_avg) * 100
        else:
            pct_diff = 0
        
        direction = "above" if pct_diff > 0 else ("below" if pct_diff < 0 else "at")
        
        return {
            "unit_average": round(unit_avg, 2),
            "complex_average": round(complex_avg, 2),
            "percentage_difference": round(abs(pct_diff), 1),
            "direction": direction,
            "days_with_data": len(unit_daily)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()
'''
    stats = stats + endpoint
    with open('api/routers/stats.py', 'w', encoding='utf-8') as f:
        f.write(stats)
    print("  Added /consumption-comparison endpoint to stats.py")
else:
    print("  Endpoint already exists.")

# === 2. ADD UI TO TENANT PORTAL ===
print("\n2. Adding comparison card to tenant portal...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_comparison')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add comparison card after the home header
if 'comparisonCard' not in c:
    card_html = """
        <!-- CONSUMPTION COMPARISON CARD -->
        <div class="card" id="comparisonCard" style="display:none;">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <h4 style="font-size: 0.75em; color: var(--gray); text-transform: uppercase; margin: 0 0 5px 0;">Complex Avg</h4>
                    <div style="font-size: 1.4em; font-weight: bold; color: var(--text);">R <span id="complexAvgVal">--</span></div>
                    <div style="font-size: 0.7em; color: var(--gray);">per day</div>
                </div>
                <div style="border-left: 1px solid var(--card-border); padding-left: 15px;">
                    <h4 style="font-size: 0.75em; color: var(--gray); text-transform: uppercase; margin: 0 0 5px 0;">Your Avg</h4>
                    <div style="font-size: 1.4em; font-weight: bold; color: var(--accent);">R <span id="unitAvgVal">--</span></div>
                    <div style="font-size: 0.7em; color: var(--gray);">per day</div>
                </div>
                <div style="border-left: 1px solid var(--card-border); padding-left: 15px;">
                    <h4 style="font-size: 0.75em; color: var(--gray); text-transform: uppercase; margin: 0 0 5px 0;">Comparison</h4>
                    <div style="font-size: 1.4em; font-weight: bold;" id="comparisonVal">--</div>
                    <div style="font-size: 0.7em; color: var(--gray);" id="comparisonLabel">--</div>
                </div>
            </div>
        </div>
"""
    # Insert after home header div
    insert_after = '</div>\n\n        <div id="rentAlertBox"'
    if insert_after in c:
        c = c.replace(insert_after, '</div>\n\n' + card_html + '\n        <div id="rentAlertBox"', 1)
        print("  Added comparison card after home header.")
    else:
        # Try alternative insertion point
        insert_after2 = '</div>\n\n        <div id="walletView"'
        if insert_after2 in c:
            c = c.replace(insert_after2, '</div>\n\n' + card_html + '\n        <div id="walletView"', 1)
            print("  Added comparison card before wallet view.")
        else:
            print("  WARNING: Could not find insertion point.")

# Add CSS for comparison colors
if 'comparison-above' not in c:
    css = """
        .comparison-above { color: #e74c3c; }
        .comparison-below { color: #27ae60; }
        .comparison-at { color: var(--accent); }
    """
    c = c.replace('<style>', '<style>\n' + css, 1)

# Add JavaScript function
if 'loadConsumptionComparison' not in c:
    js = """
    async function loadConsumptionComparison() {
        var card = document.getElementById('comparisonCard');
        if (!card || !currentTenantId) return;
        try {
            var r = await fetch('/consumption-comparison/' + currentTenantId, { headers: getAuthHeaders() });
            if (!r.ok) return;
            var d = await r.json();
            
            if (d.days_with_data === 0) {
                card.style.display = 'none';
                return;
            }
            
            card.style.display = 'block';
            document.getElementById('complexAvgVal').innerText = d.complex_average.toFixed(2);
            document.getElementById('unitAvgVal').innerText = d.unit_average.toFixed(2);
            
            var compVal = document.getElementById('comparisonVal');
            var compLabel = document.getElementById('comparisonLabel');
            
            if (d.direction === 'above') {
                compVal.innerText = '+' + d.percentage_difference + '%';
                compVal.className = 'comparison-above';
                compLabel.innerText = 'above complex average';
            } else if (d.direction === 'below') {
                compVal.innerText = '-' + d.percentage_difference + '%';
                compVal.className = 'comparison-below';
                compLabel.innerText = 'below complex average';
            } else {
                compVal.innerText = '0%';
                compVal.className = 'comparison-at';
                compLabel.innerText = 'at complex average';
            }
        } catch (e) {
            card.style.display = 'none';
        }
    }
"""
    # Add function before </script>
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]
        print("  Added loadConsumptionComparison function.")
    
    # Add call to loadConsumptionComparison in tLoadDashboard
    if 'loadConsumptionComparison()' not in c:
        c = c.replace(
            'tLoadDashboard();\n        tLoadTransactions();',
            'tLoadDashboard();\n        tLoadTransactions();\n        loadConsumptionComparison();'
        )
        print("  Added function call to tLoadDashboard.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\n" + "=" * 50)
print("DONE! Complex vs Unit Average added.")
print("=" * 50)
print("\nTest:")
print("  1. Restart server")
print("  2. Open tenant portal (Ctrl+F5)")
print("  3. Login as tenant")
print("  4. Home screen should show:")
print("     Complex Avg: R XX.XX/day")
print("     Your Avg:    R XX.XX/day")
print("     Comparison:  +X.X% above/below average")