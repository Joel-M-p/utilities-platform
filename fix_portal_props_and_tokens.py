import shutil

print("Fixing tenant portal: property dropdown + water tokens...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_fix2')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# 1. Fix property dropdown — make sure the fetch is correct and runs on load
if 'public-properties' in c:
    # Check if it's using the right URL format
    c = c.replace("fetch('/public-properties/')", "fetch('/public-properties/')")
    c = c.replace('fetch("/public-properties/")', "fetch('/public-properties/')")
    # Also try without trailing slash as fallback
    old_fetch = "fetch('/public-properties/').then(r => r.json()).then(d => {"
    new_fetch = """fetch('/public-properties/').then(r => r.json()).then(d => {
        if(!d || !d.properties) { console.error('No properties returned'); return; }
        const dd = document.getElementById('login_property');
        if(!dd) { console.error('Property dropdown not found'); return; }
        dd.innerHTML = '<option value="">Select Property...</option>';
        d.properties.forEach(p => {
            dd.innerHTML += '<option value="' + p.id + '">' + p.name + '</option>';
        });
    }).catch(e => console.error('Failed to load properties:', e));"""
    
    if old_fetch in c:
        c = c.replace(old_fetch, new_fetch)
        changes += 1
        print("  Fixed property dropdown fetch.")
    else:
        # Try to find and replace the whole block
        import re
        # Find the fetch block for public-properties
        pattern = r"fetch\(['\"]/public-properties/?['\"]\).*?(?=if\(tenantToken)"
        match = re.search(pattern, c, re.DOTALL)
        if match:
            c = c[:match.start()] + new_fetch + '\n\n    ' + c[match.end():]
            changes += 1
            print("  Fixed property dropdown fetch (regex).")
        else:
            print("  WARNING: Could not find property fetch block.")
            print("  Trying simple approach...")
            # Just make sure there's a console error message
            if "console.error('Failed to load properties" not in c:
                c = c.replace(
                    ".catch(e => console.error(\"Failed to load properties for login\"));",
                    ".catch(e => console.error('Failed to load properties:', e));"
                )

# 2. Fix water token display — add "View Token" button to both cold and hot water
# Replace the tLoadUtilityHistory function to show tokens for water too
old_func_start = 'async function tLoadUtilityHistory()'
if old_func_start in c:
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
            
            // Helper function to extract token from transaction
            function extractToken(t) {
                if(t.token) return t.token;
                if(t.reference) {
                    var match = t.reference.match(/token[:\\s]*(\\d{15,25})/i);
                    if(match) return match[1];
                    match = t.reference.match(/(\\d{20})/);
                    if(match) return match[1];
                }
                return "";
            }
            
            function makeTokenBtn(t) {
                var token = extractToken(t);
                return token ? "<button class='btn-token' onclick=\"tShowToken('" + token + "', '" + (t.units || '') + "')\">View Token</button>" : "";
            }
            
            // ELECTRICITY
            if (!d.electricity || d.electricity.length === 0) {
                elecList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No electricity purchases yet.</p>";
            } else {
                var html = "";
                d.electricity.forEach(function(t) {
                    html += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Electricity Purchase') + "</div>" +
                        "<div class='txn-date'>" + t.date + " " + makeTokenBtn(t) + "</div></div>" +
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
                if(coldWaterList) coldWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No cold water purchases yet.</p>";
            } else {
                var coldHtml = "";
                coldWater.forEach(function(t) {
                    coldHtml += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Cold Water Purchase') + "</div>" +
                        "<div class='txn-date'>" + t.date + " " + makeTokenBtn(t) + "</div></div>" +
                        "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                        "</div>";
                });
                if(coldWaterList) coldWaterList.innerHTML = coldHtml;
            }
            
            // HOT WATER
            if(hotWater.length === 0) {
                if(hotWaterList) hotWaterList.innerHTML = "<p style='text-align:center; color:var(--gray);'>No hot water purchases yet.</p>";
            } else {
                var hotHtml = "";
                hotWater.forEach(function(t) {
                    hotHtml += "<div class='txn-item'>" +
                        "<div><div style='font-weight:600;'>" + (t.units || 'Hot Water Purchase') + "</div>" +
                        "<div class='txn-date'>" + t.date + " " + makeTokenBtn(t) + "</div></div>" +
                        "<div class='txn-amount text-danger'>- R " + Math.abs(t.amount).toFixed(2) + "</div>" +
                        "</div>";
                });
                if(hotWaterList) hotWaterList.innerHTML = hotHtml;
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
        changes += 1
        print("  Replaced tLoadUtilityHistory with token support for water.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print(f"Done! {changes} fixes applied.")
print(f"{'='*50}")
print("\nTest (Ctrl+F5):")
print("  1. Open tenant portal — property dropdown should populate")
print("  2. Login as tenant")
print("  3. Go to Utilities tab")
print("  4. Cold Water purchases should show 'View Token' button")
print("  5. Hot Water purchases should show 'View Token' button")
print("  6. Electricity purchases should show 'View Token' button")