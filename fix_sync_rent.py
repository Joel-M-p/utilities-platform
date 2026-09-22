import shutil

print("Fixing Sync Rent to filter by property...")

shutil.copy('dashboard.html', 'dashboard.html.bak_rent')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace triggerMockRent function
lines = c.split('\n')
new_lines = []
skip = False
depth = 0
replaced = False

new_func = '''    async function triggerMockRent() {
        var unitNumber = document.getElementById("syncRentUnitNumber").value.trim();
        var propId = document.getElementById("propertyFilter").value;
        var payload = {};
        if (propId) payload.property_id = parseInt(propId);
        if (unitNumber) payload.unit_number = unitNumber;
        
        if(!propId) {
            alert("Please select a property first (top right dropdown).");
            return;
        }
        
        try {
            var r = await fetch("/sync-rent", { 
                method: "POST", 
                headers: { "Content-Type": "application/json", "Authorization": "Bearer " + authToken }, 
                body: JSON.stringify(payload) 
            });
            var d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            alert(d.message || "Rent sync triggered for selected property.");
            loadAllTenants();
        } catch (e) { 
            alert("Error calling /sync-rent: " + e.message); 
        }
    }'''

for line in lines:
    if not skip and 'function triggerMockRent' in line:
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
    print("  Fixed triggerMockRent — now sends property_id.")
else:
    print("  WARNING: Function not found!")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone!")
print("\nNow when you click Sync Rent:")
print("  - It reads the selected property from the dropdown")
print("  - Only syncs rent for tenants in THAT property")
print("  - If no property selected, shows a warning")