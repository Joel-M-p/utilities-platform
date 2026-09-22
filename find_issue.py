with open('dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_template = False
count = 0

print("Lines that change template literal state:")
print("=" * 60)

for i, line in enumerate(lines, 1):
    bt = line.count('`')
    if bt > 0:
        count += bt
        for char in line:
            if char == '`':
                in_template = not in_template
        
        if bt % 2 != 0:
            status = "OPENED" if in_template else "CLOSED"
            print(f"\nLine {i}: {status} ({bt} backticks)")
            print(f"  {line.rstrip()[:250]}")

print(f"\n{'=' * 60}")
print(f"Total backticks: {count}")
print(f"Template open at end: {in_template}")
if in_template:
    print("\nPROBLEM: A backtick was opened but never closed!")
    print("The last OPENED line above is where the problem starts.")