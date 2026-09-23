import os

print("Removing ALTER TABLE statements from router files...")
print("(These belong in models.py only — not in API endpoints)\n")

routers_dir = 'api/routers'
total_removed = 0

for filename in sorted(os.listdir(routers_dir)):
    if filename.endswith('.py') and not filename.startswith('__'):
        filepath = os.path.join(routers_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        removed = 0
        
        for line in lines:
            if 'ALTER TABLE' in line:
                removed += 1
                continue
            new_lines.append(line)
        
        if removed > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  {filename}: Removed {removed} ALTER TABLE statement(s)")
            total_removed += removed

print(f"\nTotal removed: {total_removed}")
print("\nThese ALTER TABLE statements belong in models.py (init_db function)")
print("where they run ONCE on startup — not on every API request.")
print("\nRestart your server to apply changes.")