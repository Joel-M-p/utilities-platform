import shutil

print("Fixing erp.py — Sync Rent to filter by property...")

shutil.copy('api/routers/erp.py', 'api/routers/erp.py.bak')

with open('api/routers/erp.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and replace the "SYNC ALL TENANTS" query
old = 'cursor.execute("SELECT id FROM tenants WHERE UPPER(status) = \'ACTIVE\'")'
new = '''property_id = payload.get("property_id")
            if property_id:
                cursor.execute("SELECT id FROM tenants WHERE UPPER(status) = 'ACTIVE' AND property_id = %s", (property_id,))
            else:
                cursor.execute("SELECT id FROM tenants WHERE UPPER(status) = 'ACTIVE'")'''

if old in c:
    c = c.replace(old, new, 1)
    print("  Added property_id filtering to sync-rent.")
else:
    print("  WARNING: Could not find exact text. Trying flexible match...")
    # Try to find the line and replace it
    lines = c.split('\n')
    new_lines = []
    for line in lines:
        if "SELECT id FROM tenants WHERE UPPER(status) = 'ACTIVE'" in line and "AND property_id" not in line:
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'property_id = payload.get("property_id")')
            new_lines.append(' ' * indent + 'if property_id:')
            new_lines.append(' ' * indent + '    cursor.execute("SELECT id FROM tenants WHERE UPPER(status) = \'ACTIVE\' AND property_id = %s", (property_id,))')
            new_lines.append(' ' * indent + 'else:')
            new_lines.append(' ' * indent + '    cursor.execute("SELECT id FROM tenants WHERE UPPER(status) = \'ACTIVE\'")')
            print("  Fixed (flexible match).")
        else:
            new_lines.append(line)
    c = '\n'.join(new_lines)

with open('api/routers/erp.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart your server and test.")
print("  1. Select Little Manhattan from the dropdown")
print("  2. Click Sync Rent (leave Unit Number blank)")
print("  3. Should say '2 active tenants' — not 5")