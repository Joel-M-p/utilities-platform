print("Finding syntax error in dashboard.html...\n")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show lines around 186
print("=== Lines 180-195 ===")
for i in range(max(0, 179), min(195, len(lines))):
    marker = " <<< ERROR HERE" if i == 185 else ""
    print(f"Line {i+1}: {lines[i].rstrip()[:150]}{marker}")

# Count backticks in script section
script_start = None
for i, line in enumerate(lines):
    if '<script>' in line:
        script_start = i
        break

if script_start:
    script_content = ''.join(lines[script_start:])
    backticks = script_content.count('`')
    print(f"\n=== Backtick count in script: {backticks}")
    if backticks % 2 != 0:
        print("  *** ODD NUMBER OF BACKTICKS — unclosed template literal! ***")
    
    # Find lines with odd backtick counts
    print("\n=== Lines with unbalanced backticks ===")
    bt_count = 0
    for i, line in enumerate(lines[script_start:], script_start + 1):
        bt_count += line.count('`')
        if bt_count % 2 != 0 and line.count('`') > 0:
            print(f"  Line {i}: backtick opened but not closed: {line.rstrip()[:120]}")
    
    # Check for clearField insertions that might be in wrong place
    print("\n=== Checking clearField insertions ===")
    for i, line in enumerate(lines, 1):
        if 'clearField' in line and 'function' not in line and 'clearFields' not in line:
            prev_line = lines[i-2].rstrip()[:100] if i >= 2 else ""
            print(f"  Line {i}: {line.rstrip()[:120]}")
            print(f"    (after: {prev_line})")

print("\nPaste this output here and I'll fix the exact line!")