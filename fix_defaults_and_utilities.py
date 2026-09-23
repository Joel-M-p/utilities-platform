import shutil

print("Fixing defaults and utilities...")

# === 1. REMOVE DEFAULTS FROM DASHBOARD ===
print("\n1. Removing defaults from dashboard.html...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

defaults_removed = 0

# Remove value="15" from VAT rate
if 'id="compVatRate"' in c and 'value="15"' in c:
    c = c.replace('value="15"', '', 1)
    defaults_removed += 1
    print("  Removed default VAT rate (15)")

# Remove value="227.26" from hot water surcharge
if 'id="hwSurcharge"' in c and 'value="227.26"' in c:
    c = c.replace('value="227.26"', '', 1)
    defaults_removed += 1
    print("  Removed default hot water surcharge (227.26)")

# Remove any other value="" on visible inputs (not hidden, not checkboxes)
import re
# Find all input tags with value attribute (except hidden and submit/button)
def remove_defaults(match):
    global defaults_removed
    tag = match.group(0)
    if 'type="hidden"' in tag or 'type="checkbox"' in tag or 'type="submit"' in tag:
        return tag
    if 'value=""' in tag:
        return tag  # Already empty
    # Remove value="..." from text/number inputs
    new_tag = re.sub(r'\s+value="[^"]*"', '', tag)
    if new_tag != tag:
        defaults_removed += 1
    return new_tag

# Only apply to specific known inputs to be safe
# Already handled compVatRate and hwSurcharge above

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)
print(f"  Total defaults removed: {defaults_removed}")

# === 2. FIX TENANT PORTAL UTILITIES ===
print("\n2. Fixing tenant portal utilities...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_utils')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# 2a. Replace the Utilities screen HTML — split water into cold and hot
old_utilities = """    <!-- SCREEN 5: UTILITIES -->
    <div id="screen-utilities" class="screen">
        <div class="card">
            <h3>Electricity History & Tokens</h3>
            <div id="elecUtilList">
                <p style="text-align:center; color:var(--gray);">Loading electricity history...</p>
            </div>
        </div>
        <div class="card">
            <h3>Water / Municipal History</h3>
            <div id="waterUtilList">
                <p style="text-align:center; color:var(--gray);">Loading water history...</p>
            </div>
        </div>
    </div>"""

new_utilities = """    <!-- SCREEN 5: UTILITIES -->
    <div id="screen-utilities" class="screen">
        <div class="card">
            <h3>Electricity History & Tokens</h3>
            <div id="elecUtilList">
                <p style="text-align:center; color:var(--gray);">Loading electricity history...</p>
            </div>
        </div>
        <div class="card">
            <h3>Cold Water History</h3>
            <div id="coldWaterUtilList">
                <p style="text-align:center; color:var(--gray);">Loading cold water history...</p>
            </div>
        </div>
        <div class="card">
            <h3>Hot Water History</h3>
            <div id="hotWaterUtilList">
                <p style="text-align:center; color:var(--gray);">Loading hot water history...</p>
            </div>
        </div>
    </div>"""

if old_utilities in c:
    c = c.replace(old_utilities, new_utilities)
    changes += 1
    print("  Split water into Cold Water and Hot Water cards.")
else:
    # Try to find and replace just the water card
    if '<h3>Water / Municipal History</h3>' in c:
        c = c.replace(
            '<h3>Water / Municipal History</h3>\n            <div id="waterUtilList">',
            '<h3>Cold Water History</h3>\n            <div id="coldWaterUtilList">'
        )
        # Add hot water card after
        c = c.replace(
            '</div>\n        </div>\n    </div>\n\n    <!-- Bottom Navigation -->',
            '</div>\n        </div>\n        <div class="card">\n            <h3>Hot Water History</h3>\n            <div id="hotWaterUtilList">\n                <p style="text-align:center; color:var(--gray);">Loading hot water history...</p>\n            </div>\n        </div>\n    </div>\n\n    <!-- Bottom Navigation -->'
        )
        changes += 1
        print("  Split water cards (alternative method).")
    else:
        print("  WARNING: Could not find utilities section.")

# 2b. Replace the tLoadUtilityHistory function
old_func_name = 'async function tLoadUtilityHistory()'
if old_func_name in c:
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
            
            // ELECTRICITY
            if (!d.electricity || d.electricity.length === 0) {
                elecList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No electricity purchases yet.</p>";
            } else {
                var html = "";
                d.electricity.forEach(function(t) {
                    var token = t.token || "";
                    if(!token && t.reference) {
                        var match = t.reference.match(/token[:\\s]*(\\d{15,20})/i);
                        if(match) token = match[1];
                    }
                    var tokenBtn = token ? "<button class='btn-token' onclick=\"tShowToken('" + token + "', '" + (t.units || '') + "')\">View Token</button>" : '';
                    html += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Electricity Purchase') + "</div>" +
                        "<div class='txn-date'>" + t.date + " " + tokenBtn + "</div></div>" +
                        "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                        "</div>";
                });
                elecList.innerHTML = html;
            }

            // Split water into cold and hot
            var allWater = d.water || [];
            var coldWater = [];
            var hotWater = [];
            
            allWater.forEach(function(t) {
                var type = (t.type || '').toUpperCase();
                var ref = (t.reference || t.units || '').toUpperCase();
                if(type.indexOf('HOT') >= 0 || ref.indexOf('HOT') >= 0) {
                    hotWater.push(t);
                } else if(type.indexOf('COLD') >= 0 || ref.indexOf('COLD') >= 0) {
                    coldWater.push(t);
                } else {
                    coldWater.push(t);
                }
            });
            
            // COLD WATER
            if(coldWater.length === 0) {
                if(coldWaterList) coldWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No cold water charges yet.</p>";
            } else {
                var coldHtml = "";
                coldWater.forEach(function(t) {
                    coldHtml += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Cold Water') + "</div>" +
                        "<div class='txn-date'>" + t.date + "</div></div>" +
                        "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                        "</div>";
                });
                if(coldWaterList) coldWaterList.innerHTML = coldHtml;
            }
            
            // HOT WATER
            if(hotWater.length === 0) {
                if(hotWaterList) hotWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No hot water charges yet.</p>";
            } else {
                var hotHtml = "";
                hotWater.forEach(function(t) {
                    hotHtml += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Hot Water') + "</div>" +
                        "<div class='txn-date'>" + t.date + "</div></div>" +
                        "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                        "</div>";
                });
                if(hotWaterList) hotWaterList.innerHTML = hotHtml;
            }
            
        } catch (e) {
            if(elecList) elecList.innerHTML = "<p style='text-align:center; color:var(--danger);'>Error loading history.</p>";
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
        changes += 1
        print("  Replaced tLoadUtilityHistory function.")
    else:
        print("  WARNING: Could not replace function.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print(f"Done! {changes} changes to tenant portal.")
print(f"{'='*50}")
print("\nTest tenant portal (Ctrl+F5):")
print("  1. Login as tenant")
print("  2. Go to Utilities tab")
print("  3. Should see 3 cards: Electricity, Cold Water, Hot Water")
print("  4. Electricity purchases should show 'View Token' button")
print("\nTest dashboard (Ctrl+F5):")
print("  1. Input fields should not have default values")
print("  2. VAT Rate field should be empty (not 15)")
print("  3. Hot Water Surcharge field should be empty (not 227.26)")