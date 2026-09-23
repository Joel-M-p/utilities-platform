print("Fixing reconciliation display...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix property names in loadRecons function
if 'r.muni_units' in c:
    c = c.replace('r.muni_units', 'r.municipal_units')
    print("  Fixed: muni_units -> municipal_units")

if 'r.sub_units' in c:
    c = c.replace('r.sub_units', 'r.submeter_units')
    print("  Fixed: sub_units -> submeter_units")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Press Ctrl+F5 and check the reconciliation table.")
print("Muni and Sub columns should now show actual numbers instead of 'undefined'.")