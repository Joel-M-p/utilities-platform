import shutil

print("Fixing credit note function...")

shutil.copy('dashboard.html', 'dashboard.html.bak_cn')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Check if the function exists
has_func = 'function submitCreditNote' in c
print(f"  Function exists: {has_func}")

# Check if the button exists
has_button = 'submitCreditNote()' in c and 'Submit Credit Note' in c
print(f"  Button exists: {has_button}")

# Known-good version of submitCreditNote (uses string concat, no backticks)
new_func = '''    async function submitCreditNote() {
        var unit = document.getElementById("cnUnitNumber").value;
        var resultDiv = document.getElementById("cnResult");
        if(!unit) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>Please enter a Unit Number.</p>";
            return;
        }
        var tenantCheck = getTenantIdByUnit(unit);
        if(tenantCheck.error) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>" + tenantCheck.error + "</p>";
            return;
        }
        var tenantId = tenantCheck.id;
        var amount = document.getElementById("cnAmount").value;
        var reason = document.getElementById("cnReason").value;
        if(!amount || !reason) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>Please enter an amount and a reason.</p>";
            return;
        }
        var url = "/generate-credit-note/";
        try {
            var r = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": "Bearer " + authToken },
                body: JSON.stringify({ tenant_id: tenantId, amount: parseFloat(amount), reason: reason })
            });
            var d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:green;'>" + d.message + " (" + (d.note_no || "") + ")</p>";
            logAction("Generated Credit Note", "Unit: " + unit + ", Amount: " + amount);
            document.getElementById("cnAmount").value = "";
            document.getElementById("cnReason").value = "";
            loadAllTenants();
        } catch (e) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML = "<p style='color:red;'>Error: " + e.message + "</p>";
        }
    }'''

if has_func:
    # Replace existing function using brace counting
    lines = c.split('\n')
    new_lines = []
    skip = False
    depth = 0
    replaced = False
    
    for line in lines:
        if not skip and 'function submitCreditNote' in line:
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
        print("  Replaced submitCreditNote function.")
    else:
        print("  WARNING: Could not replace. Adding at end instead.")
        idx = c.rfind('</script>')
        if idx != -1:
            c = c[:idx] + '\n' + new_func + '\n' + c[idx:]
            print("  Added submitCreditNote function.")
else:
    # Function doesn't exist - add it
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + '\n' + new_func + '\n' + c[idx:]
        print("  Added submitCreditNote function (was missing!).")
    else:
        print("  ERROR: No </script> tag found!")

# Also make sure the button HTML is correct
if 'submitCreditNote()' not in c:
    # Add the button if missing
    c = c.replace(
        '<div id="cnResult"',
        '<button onclick="submitCreditNote()">Submit Credit Note</button>\n                    <div id="cnResult"'
    )
    print("  Added Submit Credit Note button.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone!")
print("Test: Reports tab -> Generate Credit Note")
print("  1. Enter a Unit Number (e.g., 101)")
print("  2. Enter an Amount (e.g., 50)")
print("  3. Enter a Reason (e.g., Overcharge)")
print("  4. Click Submit Credit Note")
print("  5. Should see green success message")