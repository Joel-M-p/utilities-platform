import re

print("Scanning dashboard.html for default values in input fields...\n")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = 0
for i, line in enumerate(lines, 1):
    if '<input' in line and 'value=' in line:
        if 'type="hidden"' in line or 'type="checkbox"' in line or 'type="radio"' in line:
            continue
        if 'value=""' in line:
            continue
        found += 1
        print(f"Line {i}: {line.strip()[:120]}")

print(f"\nFound {found} input fields with default values.")

# Now remove them
print("\nRemoving defaults...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

removed = 0
lines = c.split('\n')
new_lines = []

for line in lines:
    if '<input' in line and 'value=' in line:
        if 'type="hidden"' in line or 'type="checkbox"' in line or 'type="radio"' in line:
            new_lines.append(line)
            continue
        if 'value=""' in line:
            new_lines.append(line)
            continue
        # Remove value="..." and value='...'
        new_line = re.sub(r'\s+value="[^"]*"', '', line)
        new_line = re.sub(r"\s+value='[^']*'", '', new_line)
        if new_line != line:
            removed += 1
            print(f"  Removed: {line.strip()[:80]}")
        new_lines.append(new_line)
    else:
        new_lines.append(line)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\nRemoved {removed} default values.")