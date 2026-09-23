print("Final fix for utilities section...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace entire utilities screen ===
start = c.find('<!-- SCREEN 5: UTILITIES')
end = c.find('<!-- Bottom Navigation')

if start != -1 and end != -1:
    new_screen = """<!-- SCREEN 5: UTILITIES -->
    <div id="screen-utilities" class="screen">
        <div class="card">
            <h3>Electricity History & Tokens</h3>
            <div id="elecUtilList">
                <p style="text-align:center; color:var(--gray);">Loading electricity history...</p>
            </div>
        </div>
        <div class="card">
            <h3>Cold Water History & Tokens</h3>
            <div id="coldWaterUtilList">
                <p style="text-align:center; color:var(--gray);">Loading cold water history...</p>
            </div>
        </div>
        <div class="card">
            <h3>Hot Water History & Tokens</h3>
            <div id="hotWaterUtilList">
                <p style="text-align:center; color:var(--gray);">Loading hot water history...</p>
            </div>
        </div>
    </div>

    """
    c = c[:start] + new_screen + c[end:]
    print("  Replaced utilities screen with 3 cards.")
else:
    print("  WARNING: Could not find utilities markers.")
    print("  start=" + str(start) + " end=" + str(end))

# === 2. Add overridden functions before last </script> ===
idx = c.rfind('</script>')
if idx != -1:
    # Use raw string so \n, \d, \s are preserved for JavaScript
    new_funcs = r"""
    // OVERRIDDEN: Handles electricity + cold water + hot water separately, with tokens for all
    async function tLoadUtilityHistory() {
        var elecList = document.getElementById("elecUtilList");
        var coldList = document.getElementById("coldWaterUtilList");
        var hotList = document.getElementById("hotWaterUtilList");
        if(!elecList) return;
        try {
            var r = await fetch("/tenant-utility-history/" + currentTenantId, { headers: getAuthHeaders() });
            if (!r.ok) throw new Error("Failed");
            var d = await r.json();

            function getToken(t) {
                if(t.token) return t.token;
                if(t.reference) {
                    var m = t.reference.match(/token[:\s]*(\d{15,25})/i);
                    if(m) return m[1];
                    m = t.reference.match(/(\d{20})/);
                    if(m) return m[1];
                }
                return "";
            }

            function makeBtn(t) {
                var tk = getToken(t);
                if(!tk) return "";
                return '<span class="token-link" data-token="' + tk + '" data-units="' + (t.units || "") + '" style="color:#3498db;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;">View Token</span>';
            }

            function makeItem(t, label) {
                return '<div class="txn-item"><div><div style="font-weight:600;">' + (t.units || label) + '</div><div class="txn-date">' + t.date + ' ' + makeBtn(t) + '</div></div><div class="txn-amount text-danger">- R ' + Math.abs(t.amount).toFixed(2) + '</div></div>';
            }

            // Electricity
            if(!d.electricity || d.electricity.length === 0) {
                elecList.innerHTML = '<p style="text-align:center; color:#7f8c8d;">No electricity purchases yet.</p>';
            } else {
                var html = "";
                d.electricity.forEach(function(t) { html += makeItem(t, "Electricity Purchase"); });
                elecList.innerHTML = html;
            }

            // Split water into cold and hot
            var allWater = d.water || [];
            var coldArr = [];
            var hotArr = [];
            allWater.forEach(function(t) {
                var type = (t.type || "").toUpperCase();
                var ref = (t.reference || t.units || "").toUpperCase();
                if(type.indexOf("HOT") >= 0 || ref.indexOf("HOT") >= 0) {
                    hotArr.push(t);
                } else {
                    coldArr.push(t);
                }
            });

            // Cold Water
            if(coldArr.length === 0) {
                if(coldList) coldList.innerHTML = '<p style="text-align:center; color:#7f8c8d;">No cold water purchases yet.</p>';
            } else {
                var cHtml = "";
                coldArr.forEach(function(t) { cHtml += makeItem(t, "Cold Water Purchase"); });
                if(coldList) coldList.innerHTML = cHtml;
            }

            // Hot Water
            if(hotArr.length === 0) {
                if(hotList) hotList.innerHTML = '<p style="text-align:center; color:#7f8c8d;">No hot water purchases yet.</p>';
            } else {
                var hHtml = "";
                hotArr.forEach(function(t) { hHtml += makeItem(t, "Hot Water Purchase"); });
                if(hotList) hotList.innerHTML = hHtml;
            }

            // Attach click handlers for token links
            var links = document.querySelectorAll(".token-link");
            for(var i = 0; i < links.length; i++) {
                links[i].onclick = function() {
                    tShowToken(this.getAttribute("data-token"), this.getAttribute("data-units"));
                };
            }
        } catch(e) {
            if(elecList) elecList.innerHTML = '<p style="text-align:center; color:#e74c3c;">Error: ' + e.message + '</p>';
            if(coldList) coldList.innerHTML = "";
            if(hotList) hotList.innerHTML = "";
        }
    }

    // OVERRIDDEN: Works for electricity AND water tokens
    function tShowToken(token, units) {
        alert("UTILITY TOKEN\n\nUnits: " + (units || "N/A") + "\nToken: " + token + "\n\nPlease enter this token into your meter.");
    }
"""
    c = c[:idx] + new_funcs + '\n' + c[idx:]
    print("  Added overridden functions (tLoadUtilityHistory + tShowToken).")
else:
    print("  WARNING: No </script> found!")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Press Ctrl+F5 and test.")
print("  1. Login as tenant")
print("  2. Go to Utilities tab")
print("  3. Should see 3 cards: Electricity, Cold Water, Hot Water")
print("  4. Each purchase should show 'View Token' link")
print("  5. Click 'View Token' -> shows token popup")