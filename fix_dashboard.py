import shutil, re

shutil.copy('dashboard.html', 'dashboard.html.bak')
print("Backup created: dashboard.html.bak\n")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Show what we found
if 'resetTenantPassword' in content:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'resetTenantPassword' in line:
            print(f"Found on line {i}: {line.strip()[:150]}")
else:
    print("resetTenantPassword NOT found in file.")

# Check for broken template literals (backticks)
backticks = content.count('`')
print(f"\nBacktick count: {backticks}")
if backticks % 2 != 0:
    print("WARNING: Odd backticks - this is what's breaking your dashboard!")

# Fix 1: Remove the Reset Password button (any format)
content = re.sub(r'\s*<button[^>]*resetTenantPassword[^>]*>.*?</button>', '', content)

# Fix 2: Remove the resetTenantPassword function (any format)
lines = content.split('\n')
new_lines = []
skip = False
depth = 0
for line in lines:
    if not skip and 'function resetTenantPassword' in line:
        skip = True
        depth = line.count('{') - line.count('}')
        if depth <= 0:
            skip = False
        continue
    if skip:
        depth += line.count('{') - line.count('}')
        if depth <= 0:
            skip = False
        continue
    new_lines.append(line)
content = '\n'.join(new_lines)

# Fix 3: Check backticks again
backticks2 = content.count('`')
print(f"Backtick count after fix: {backticks2}")
if backticks2 % 2 != 0:
    print("WARNING: Still odd backticks! There may be another issue.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nFix applied. Now do this:")
print("  1. Go to http://127.0.0.1:8000/dashboard")
print("  2. Press Ctrl+F5 (hard refresh)")
print("  3. Login: admin / password123")