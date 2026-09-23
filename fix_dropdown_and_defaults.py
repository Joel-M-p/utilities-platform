import re, shutil

print("Fixing dropdown default + removing input defaults...")

# === FIX TENANT PORTAL: Property dropdown ===
print("\n1. Fixing tenant portal property dropdown...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add autocomplete="off" to the property dropdown
if 'id="login_property"' in c and 'autocomplete' not in c.split('id="login_property"')[0].split('<select')[-1]:
    c = c.replace('<select id="login_property">', '<select id="login_property" autocomplete="off">')
    print("  Added autocomplete=off to login property dropdown.")

# After properties load, reset to "Select Property..."
old_fetch_end = "}).catch(e => console.error"
if "dd.value = '';" not in c and "dd.value = \"\";" not in c:
    # Add dd.value = '' after the forEach loop
    c = c.replace(
        "});\n    }).catch",
        "});\n        dd.value = '';\n    }).catch"
    )
    print("  Added dropdown reset after properties load.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

# === FIX DASHBOARD: Remove ALL default values from input fields ===
print("\n2. Removing ALL default values from dashboard.html...")

shutil.copy('dashboard.html', 'dashboard.html.bak_defaults')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
removed = 0

for i, line in enumerate(lines, 1):
    modified = False
    
    # Check if line has an input with value="something" (not empty)
    if '<input' in line and 'value=' in line:
        # Skip hidden, checkbox, radio
        if 'type="hidden"' in line or 'type="checkbox"' in line or 'type="radio"' in line:
            new_lines.append(line)
            continue
        # Skip empty values
        if 'value=""' in line:
            new_lines.append(line)
            continue
        
        # Remove value="..." 
        new_line = re.sub(r'\s+value="[^"]*"', '', line)
        new_line = re.sub(r"\s+value='[^']*'", '', new_line)
        
        if new_line != line:
            removed += 1
            print(f"  Line {i}: Removed default -> {line.strip()[:80]}")
            new_lines.append(new_line)
            modified = True
    
    if not modified:
        new_lines.append(line)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n  Total defaults removed: {removed}")

# === ALSO fix tenant portal input defaults ===
print("\n3. Removing defaults from tenant_portal.html...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    tlines = f.readlines()

new_tlines = []
tremoved = 0

for i, line in enumerate(tlines, 1):
    modified = False
    
    if '<input' in line and 'value=' in line:
        if 'type="hidden"' in line or 'type="checkbox"' in line or 'type="radio"' in line:
            new_tlines.append(line)
            continue
        if 'value=""' in line:
            new_tlines.append(line)
            continue
        
        new_line = re.sub(r'\s+value="[^"]*"', '', line)
        new_line = re.sub(r"\s+value='[^']*'", '', new_line)
        
        if new_line != line:
            tremoved += 1
            print(f"  Line {i}: Removed -> {line.strip()[:80]}")
            new_tlines.append(new_line)
            modified = True
    
    if not modified:
        new_tlines.append(line)

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.writelines(new_tlines)

print(f"\n  Total defaults removed: {tremoved}")

# === ALSO fix dashboard property filter dropdown ===
print("\n4. Fixing dashboard property filter...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

if 'id="propertyFilter"' in c and 'autocomplete' not in c.split('id="propertyFilter"')[0].split('<select')[-1]:
    c = c.replace('<select id="propertyFilter"', '<select id="propertyFilter" autocomplete="off"')
    print("  Added autocomplete=off to property filter.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\n" + "=" * 50)
print("DONE!")
print("=" * 50)
print("\nTest (Ctrl+F5):")
print("  1. Tenant portal: Property dropdown should show 'Select Property...' (not Portia)")
print("  2. Dashboard: Input fields should be empty (no pre-filled values)")
print("  3. Dashboard: Property filter should show 'All Properties' (not remembered)")