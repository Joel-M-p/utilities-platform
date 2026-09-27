import os

print("Cleaning up backup files (*.bak, *.bak_*)...\n")

removed = 0
for filename in os.listdir('.'):
    if filename.endswith('.bak') or '.bak_' in filename:
        os.remove(filename)
        print(f"  Deleted: {filename}")
        removed += 1

# Also check subdirectories
for subdir in ['api', 'api/routers', 'api/services']:
    if os.path.exists(subdir):
        for filename in os.listdir(subdir):
            filepath = os.path.join(subdir, filename)
            if filename.endswith('.bak') or '.bak_' in filename:
                os.remove(filepath)
                print(f"  Deleted: {filepath}")
                removed += 1

print(f"\nRemoved {removed} backup files.")
print("These are safe to delete — your real files are intact.")