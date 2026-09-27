import re

print("Fixing syntax error from clear_forms.py...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix: Remove clearField/clearFields calls that were inserted INSIDE style attributes
# The broken pattern: color:green; <newline> clearField('...'); <newline> font-weight:bold;
# This happened because clear_forms.py found ";" inside a string, not at end of statement
before = c.count("clearField('")

c = re.sub(
    r"color:green;\s*\n(\s*(?:clearField\([^)]*\)|clearFields\([^)]*\));\s*\n)+\s*font-weight:bold;",
    "color:green;font-weight:bold;",
    c
)

after = c.count("clearField('")
removed = before - after

print(f"  Removed {removed} broken clearField calls from inside style attributes.")

# Also fix any other style attributes that might be broken
# Pattern: any style="...; clearField('...'); ..."
c = re.sub(
    r"(style=\"[^\"]*?);(\s*\n\s*(?:clearField\([^)]*\)|clearFields\([^)]*\));\s*\n)+",
    r"\1;",
    c
)

# Verify fix — check backtick count
script_start = c.find('<script>')
if script_start != -1:
    bt = c[script_start:].count('`')
    print(f"  Backtick count: {bt} ({'EVEN - OK' if bt % 2 == 0 else 'ODD - STILL BROKEN'})")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Now:")
print("  1. Restart server (Ctrl+C, then start)")
print("  2. Open dashboard in incognito (Ctrl+Shift+N)")
print("  3. Press Ctrl+F5")
print("  4. Login: admin / password123")
print("  5. Should work now!")