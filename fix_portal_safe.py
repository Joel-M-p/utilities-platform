import shutil, os, re

print("SAFELY fixing tenant portal...")

# === STEP 1: Restore from backup (where property dropdown worked) ===
backups = ['tenant_portal.html.bak_utils', 'tenant_portal.html.bak_demo', 'tenant_portal.html.bak_fix2']
restored = False

for bak in backups:
    if os.path.exists(bak):
        shutil.copy(bak, 'tenant_portal.html')
        print("  Restored from: " + bak)
        restored = True
        break

if not restored:
    print("  No backup found. Working with current file.")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === STEP 2: Split water card into Cold + Hot (simple string replace) ===
# DO NOT touch any other code — especially the property dropdown

if 'coldWaterUtilList' not in c:
    # Replace water card with cold + hot cards
    old_water = '<h3>Water / Municipal History</h3>'
    new_cards = '<h3>Cold Water History</h3>'
    
    if old_water in c:
        c = c.replace(old_water, new_cards)
        c = c.replace('id="waterUtilList"', 'id="coldWaterUtilList"')
        c = c.replace('Loading water history...', 'Loading cold water history...')
        
        # Add hot water card after the closing of cold water card
        # Find the closing </div> of the utilities screen
        c = c.replace(
            '</div>\n    </div>\n\n    <!-- Bottom Navigation -->',
            '</div>\n        </div>\n        <div class="card">\n            <h3>Hot Water History</h3>\n            <div id="hotWaterUtilList">\n                <p style="text-align:center; color:var(--gray);">Loading hot water history...</p>\n            </div>\n        </div>\n    </div>\n\n    <!-- Bottom Navigation -->'
        )
        print("  Split water into Cold + Hot cards.")
    else:
        print("  WARNING: Water card not found. May already be split.")

# === STEP 3: Replace tLoadUtilityHistory function (brace counting) ===
if 'coldWaterUtilList' in c and 'function tLoadUtilityHistory' in c:
    lines = c.split('\n')
    new_lines = []
    skip = False
    depth = 0
    replaced = False

    new_func = """    async function tLoadUtilityHistory() {
        var elecList = document.getElementById('elecUtilList');
        var coldWaterList = document.getElementById('coldWaterUtilList');
        var hotWaterList = document.getElementById('hotWaterUtilList');
        if(!elecList) return;
        
        try {
            var r = await fetch('/tenant-utility-history/' + currentTenantId, { headers: getAuthHeaders() });
            if (!r.ok) throw new Error("Failed");
            var d = await r.json();
            
            function extractToken(t) {
                if(t.token) return t.token;
                if(t.reference) {
                    var m = t.reference.match(/token[:\\s]*(\\d{15,25})/i);
                    if(m) return m[1];
                    m = t.reference.match(/(\\d{20})/);
                    if(m) return m[1];
                }
                return "";
            }
            
            function tokenBtn(t) {
                var tk = extractToken(t);
                return tk ? "<button class='btn-token' onclick=\\"tShowToken('" + tk + "', '" + (t.units || '') + "')\\">View Token</button>" : "";
            }
            
            function renderItem(t, label) {
                return "<div class='txn-item'>" +
                    "<div><div style='font-weight:600;'>" + (t.units || label) + "</div>" +
                    "<div class='txn-date'>" + t.date + " " + tokenBtn(t) + "</div></div>" +
                    "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                    "</div>";
            }
            
            if (!d.electricity || d.electricity.length === 0) {
                elecList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No electricity purchases yet.</p>";
            } else {
                var html = "";
                d.electricity.forEach(function(t) { html += renderItem(t, 'Electricity Purchase'); });
                elecList.innerHTML = html;
            }
            
            var allWater = d.water || [];
            var coldWater = [];
            var hotWater = [];
            
            allWater.forEach(function(t) {
                var type = (t.type || '').toUpperCase();
                var ref = (t.reference || t.units || '').toUpperCase();
                if(type.indexOf('HOT') >= 0 || ref.indexOf('HOT') >= 0) {
                    hotWater.push(t);
                } else {
                    coldWater.push(t);
                }
            });
            
            if(coldWater.length === 0) {
                if(coldWaterList) coldWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No cold water purchases yet.</p>";
            } else {
                var cHtml = "";
                coldWater.forEach(function(t) { cHtml += renderItem(t, 'Cold Water Purchase'); });
                if(coldWaterList) coldWaterList.innerHTML = cHtml;
            }
            
            if(hotWater.length === 0) {
                if(hotWaterList) hotWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No hot water purchases yet.</p>";
            } else {
                var hHtml = "";
                hotWater.forEach(function(t) { hHtml += renderItem(t, 'Hot Water Purchase'); });
                if(hotWaterList) hotWaterList.innerHTML = hHtml;
            }
            
        } catch (e) {
            if(elecList) elecList.innerHTML = "<p style='text-align:center; color:var(--danger);'>Error: " + e.message + "</p>";
            if(coldWaterList) coldWaterList.innerHTML = "";
            if(hotWaterList) hotWaterList.innerHTML = "";
        }
    }"""

    for line in lines:
        if not skip and 'function tLoadUtilityHistory' in line:
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
        print("  Replaced tLoadUtilityHistory with token support.")
    else:
        print("  WARNING: Could not replace function.")
else:
    print("  Skipping function replacement (prerequisites not met).")

# === STEP 4: Update tShowToken to say "UTILITY TOKEN" ===
if 'ELECTRICITY TOKEN' in c:
    c = c.replace('ELECTRICITY TOKEN', 'UTILITY TOKEN')
    print("  Updated tShowToken label.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

# === STEP 5: Remove defaults from dashboard.html ===
print("\nRemoving defaults from dashboard.html...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    dc = f.read()

removed = 0
dl = dc.split('\n')
new_dl = []

for line in dl:
    if '<input' in line and 'value=' in line:
        # Skip hidden, checkbox, radio inputs
        if 'type="hidden"' in line or 'type="checkbox"' in line or 'type="radio"' in line:
            new_dl.append(line)
            continue
        # Remove value="..." and value='...'
        new_line = re.sub(r'\s+value="[^"]*"', '', line)
        new_line = re.sub(r"\s+value='[^']*'", '', new_line)
        if new_line != line:
            removed += 1
            print("  Removed default from: " + line.strip()[:80])
        new_dl.append(new_line)
    else:
        new_dl.append(line)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_dl))

print("\n  Total defaults removed: " + str(removed))

print("\n" + "=" * 50)
print("DONE!")
print("=" * 50)
print("\nTest (Ctrl+F5):")
print("  1. Tenant portal: Property dropdown should populate again")
print("  2. Tenant portal: Utilities tab should show 3 cards (Elec, Cold Water, Hot Water)")
print("  3. Tenant portal: Water purchases should show 'View Token' button")
print("  4. Dashboard: Input fields should not have default values")