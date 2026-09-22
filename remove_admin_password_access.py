import shutil, re

# === 1. REMOVE FROM dashboard.html ===
print("Updating dashboard.html...")
shutil.copy('dashboard.html', 'dashboard.html.bak2')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the Reset Password button from tenant table
content = re.sub(r'\s*<button[^>]*resetTenantPassword[^>]*>Reset Password</button>', '', content)
print("  Removed Reset Password button.")

# Remove the resetTenantPassword function
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
print("  Removed resetTenantPassword function.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

# === 2. REMOVE ENDPOINT FROM auth.py ===
print("\nUpdating auth.py...")
shutil.copy('api/routers/auth.py', 'api/routers/auth.py.bak2')

with open('api/routers/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the admin-reset-tenant-password endpoint entirely
lines = content.split('\n')
new_lines = []
skip = False
depth = 0
removed = False
for line in lines:
    if not skip and 'admin-reset-tenant-password' in line and ('@router' in line or 'def ' in line):
        skip = True
        depth = line.count('{') - line.count('}')
        removed = True
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

if removed:
    print("  Removed /admin-reset-tenant-password endpoint.")
else:
    print("  Endpoint not found (may already be removed).")

with open('api/routers/auth.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 55)
print("DONE! Admin password reset completely removed.")
print("=" * 55)
print("\nWhat was removed:")
print("  1. Reset Password button (dashboard.html)")
print("  2. resetTenantPassword function (dashboard.html)")
print("  3. /admin-reset-tenant-password endpoint (auth.py)")
print("\nTenant password flow is now 100% self-service:")
print("  - Forgot Password? (on login screen)")
print("  - Change Password (in tenant portal header)")
print("\nAdmins have ZERO access to tenant passwords.")