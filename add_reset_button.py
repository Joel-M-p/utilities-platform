with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Reset Password button after Vacate button
old_text = '<button onclick="vacateTenant(${tId})" class="btn-danger">Vacate</button></td></tr>'
new_text = '<button onclick="vacateTenant(${tId})" class="btn-danger">Vacate</button> <button onclick="resetTenantPassword(${tId})" class="btn-credit">Reset Password</button></td></tr>'

if old_text in content:
    content = content.replace(old_text, new_text)
    print("Added Reset Password button.")
elif 'resetTenantPassword' in content:
    print("Button already added.")
else:
    print("WARNING: Could not find Vacate button. Check your file.")

# 2. Add the function before </script>
if 'function resetTenantPassword' not in content:
    func = """
    async function resetTenantPassword(id) {
        if (!confirm("Generate a new temporary password for this tenant? They will be required to set their own password on next login.")) return;
        try {
            const r = await fetch(`/admin-reset-tenant-password/${id}/`, {
                method: 'POST',
                headers: getAuthHeaders()
            });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            alert("TEMPORARY PASSWORD GENERATED\\n\\nTenant: " + (d.tenant_name || "") + "\\nUnit: " + (d.unit_number || "") + "\\n\\nTemporary Password: " + d.temp_password + "\\n\\nIMPORTANT: Share this password with the tenant securely.\\nThey will be required to set their own password on first login.");
            logAction("Reset Tenant Password", `Tenant ID: ${id}`);
        } catch (e) {
            alert("Error calling /admin-reset-tenant-password: " + e.message);
        }
    }
</script>"""
    content = content.replace('</script>', func)
    print("Added resetTenantPassword function.")
else:
    print("Function already exists.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! Dashboard is ready.")
print("Test: http://127.0.0.1:8000/dashboard (Ctrl+F5)")
print("Login: admin / password123")
print("Tenants tab -> Refresh -> Reset Password button")