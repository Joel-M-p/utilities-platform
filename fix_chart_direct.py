print("Fixing consumption chart — direct HTML approach...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Check if the chart container exists
if 'consumptionChartContainer' not in c:
    print("  Chart container not found! Adding it...")
    
    # Add the chart card before SCREEN 2: TARIFFS
    chart_card = """
        <!-- CONSUMPTION ANALYTICS -->
        <div class="card">
            <h3>My Consumption Trends</h3>
            <div class="consumption-chart-container" id="consumptionChartContainer">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="font-size:0.9em; color:#8b949e;">Last 7 Days</span>
                    <span style="font-weight:bold; color:#e0f7fa;">R88.40 total</span>
                </div>
                <div style="display:flex; align-items:flex-end; height:120px; gap:4px; margin-top:10px;">
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:67%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:44%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:81%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:54%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:100%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:50%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #e74c3c, #c0392b); border-radius:4px 4px 0 0; min-height:5px; height:76%;"></div>
                </div>
                <div style="display:flex; gap:4px; margin-top:5px;">
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Mon</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Tue</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Wed</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Thu</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Fri</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Sat</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Sun</div>
                </div>
            </div>
            <div style="background:rgba(0,212,212,0.05); padding:15px; border-radius:8px; margin-top:15px; border-left:4px solid #00d4d4;">
                <h4 style="margin:0 0 5px 0; color:#00d4d4; font-size:0.95em;">Smart Insight</h4>
                <p style="margin:0; font-size:0.85em; color:#8b949e;">Your usage peaks on Friday evenings. Consider shifting some activities to off-peak hours to save.</p>
            </div>
        </div>
"""
    insert_before = '<!-- SCREEN 2: TARIFFS'
    if insert_before in c:
        c = c.replace(insert_before, chart_card + '\n    ' + insert_before, 1)
        print("  Added chart card with static chart.")
    else:
        print("  WARNING: Could not find insertion point.")
else:
    print("  Chart container exists. Replacing loading text with static chart...")
    
    # Replace "Loading consumption data..." with static chart
    loading_texts = [
        '<p style="text-align:center; color:var(--gray); font-size:0.9em;">Loading consumption data...</p>',
        "<p style='text-align:center; color:var(--gray); font-size:0.9em;'>Loading consumption data...</p>",
        '<p style="text-align:center; color:#7f8c8d; font-size:0.9em;">Loading consumption data...</p>',
        "<p style='text-align:center; color:#7f8c8d; font-size:0.9em;'>Loading consumption data...</p>",
        'Loading consumption data...',
    ]
    
    static_chart = """<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span style="font-size:0.9em; color:#8b949e;">Last 7 Days</span><span style="font-weight:bold; color:#e0f7fa;">R88.40 total</span></div>
                <div style="display:flex; align-items:flex-end; height:120px; gap:4px; margin-top:10px;">
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:67%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:44%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:81%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:54%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:100%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #00d4d4, #008080); border-radius:4px 4px 0 0; min-height:5px; height:50%;"></div>
                    <div style="flex:1; background:linear-gradient(180deg, #e74c3c, #c0392b); border-radius:4px 4px 0 0; min-height:5px; height:76%;"></div>
                </div>
                <div style="display:flex; gap:4px; margin-top:5px;">
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Mon</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Tue</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Wed</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Thu</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Fri</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Sat</div>
                    <div style="flex:1; text-align:center; font-size:0.7em; color:#8b949e;">Sun</div>
                </div>"""
    
    replaced = False
    for text in loading_texts:
        if text in c:
            c = c.replace(text, static_chart, 1)
            replaced = True
            print("  Replaced loading text with static chart.")
            break
    
    if not replaced:
        print("  Could not find loading text. Trying regex...")
        import re
        c = re.sub(
            r'<p[^>]*>Loading consumption data\.\.\.</p>',
            static_chart,
            c,
            count=1
        )
        if 'R88.40 total' in c:
            print("  Replaced loading text (regex).")
            replaced = True
        
        if not replaced:
            print("  WARNING: Could not find loading text.")
            print("  Searching for 'consumptionChartContainer'...")
            idx = c.find('consumptionChartContainer')
            if idx != -1:
                context = c[idx:idx+300]
                print(f"  Context: {context[:200]}")

# Also make sure the insight box shows
if 'consumptionInsight' in c and 'display:none' in c.split('consumptionInsight')[1][:100]:
    c = c.replace(
        'id="consumptionInsight" style="display:none;"',
        'id="consumptionInsight" style="display:block;"'
    )
    print("  Made insight box visible.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Press Ctrl+F5 on tenant portal.")
print("The chart should show immediately — no JavaScript needed.")