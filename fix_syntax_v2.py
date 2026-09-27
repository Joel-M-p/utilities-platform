import re

print("Fixing syntax error (v2)...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# The broken text looks like:
# color:green;\n            clearFields(['ntvUnitNumber', 'ntvExitDate', 'ntvReason']);\n            clearField('unitNumberInput');font-weight:bold;
#
# The clearField calls were inserted INSIDE the style string
# "color:green;font-weight:bold;" was split apart
#
# Fix: Remove ALL clearField/clearFields calls between "color:green;" and "font-weight:bold;"

fixes = 0

# Loop to remove all clearField/clearFields calls after "color:green;"
while re.search(r"color:green;\s*(?:clearField|clearFields)\(", c):
    c = re.sub(
        r"(color:green;)\s*(?:clearField\([^)]*\)|clearFields\([^)]*\));?\s*",
        r"\1",
        c,
        count=1
    )
    fixes += 1

print(f"  Removed {fixes} broken clearField calls from inside style attributes.")

# Also check for any other broken style attributes
while re.search(r'style="[^"]*clearField', c):
    c = re.sub(
        r'(style="[^;]*;)\s*(?:clearField\([^)]*\)|clearFields\([^)]*\));?\s*',
        r'\1',
        c,
        count=1
    )
    fixes += 1
    print("  Fixed clearField inside another style attribute.")

# Verify backtick count
script_start = c.find('<script>')
if script_start != -1:
    bt = c[script_start:].count('`')
    status = "EVEN - OK" if bt % 2 == 0 else "ODD - STILL BROKEN"
    print(f"  Backtick count: {bt} ({status})")

# Show the fixed text to verify
idx = c.find("color:green;font-weight:bold;")
if idx != -1:
    print(f"\n  Fixed text: ...{c[idx:idx+50]}...")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\nDone! {fixes} fixes applied.")
print("\nNow:")
print("  1. Restart server (Ctrl+C, then start)")
print("  2. Open dashboard in incognito (Ctrl+Shift+N)")
print("  3. Press Ctrl+F5")
print("  4. Login: admin / password123")