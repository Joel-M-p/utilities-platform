print("Fixing browser autocomplete on login fields...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# 1. Add autocomplete="off" to unit number input
if 'id="login_unit_number"' in c and 'autocomplete="off"' not in c.split('id="login_unit_number"')[0].split('<input')[-1]:
    c = c.replace(
        '<input type="text" id="login_unit_number"',
        '<input type="text" id="login_unit_number" autocomplete="off" autocorrect="off" autocapitalize="off"'
    )
    changes += 1
    print("  Added autocomplete=off to unit number field.")

# 2. Add autocomplete="off" to password input
if 'id="login_password"' in c and 'autocomplete="off"' not in c.split('id="login_password"')[0].split('<input')[-1]:
    c = c.replace(
        '<input type="password" id="login_password"',
        '<input type="password" id="login_password" autocomplete="new-password"'
    )
    changes += 1
    print("  Added autocomplete=off to password field.")

# 3. Add autocomplete="off" to forgot password inputs
if 'id="forgot_unit_number"' in c and 'autocomplete="off"' not in c.split('id="forgot_unit_number"')[0].split('<input')[-1]:
    c = c.replace(
        '<input type="text" id="forgot_unit_number"',
        '<input type="text" id="forgot_unit_number" autocomplete="off"'
    )
    changes += 1
    print("  Added autocomplete=off to forgot unit number.")

if 'id="forgot_email"' in c and 'autocomplete="off"' not in c.split('id="forgot_email"')[0].split('<input')[-1]:
    c = c.replace(
        '<input type="email" id="forgot_email"',
        '<input type="email" id="forgot_email" autocomplete="off"'
    )
    changes += 1
    print("  Added autocomplete=off to forgot email.")

# 4. Add JavaScript to CLEAR all login fields on page load
if "login_unit_number').value = ''" not in c:
    # Add before the tenantToken check
    c = c.replace(
        "if(tenantToken && currentTenantId)",
        "var lu = document.getElementById('login_unit_number'); if(lu) lu.value = '';\n    var lp = document.getElementById('login_password'); if(lp) lp.value = '';\n\n    if(tenantToken && currentTenantId)"
    )
    changes += 1
    print("  Added JavaScript to clear login fields on page load.")

# 5. Also clear forgot password fields
if "forgot_unit_number').value = ''" not in c:
    c = c.replace(
        "function tShowForgotPassword()",
        "function tClearForgotFields() { var fu = document.getElementById('forgot_unit_number'); if(fu) fu.value = ''; var fe = document.getElementById('forgot_email'); if(fe) fe.value = ''; document.getElementById('forgotSuccess').style.display = 'none'; document.getElementById('forgotError').style.display = 'none'; }\n    function tShowForgotPassword()"
    )
    # Call tClearForgotFields at the start of tShowForgotPassword
    c = c.replace(
        "function tShowForgotPassword() {\n        document.getElementById('screen-login')",
        "function tShowForgotPassword() {\n        tClearForgotFields();\n        document.getElementById('screen-login')"
    )
    changes += 1
    print("  Added clear for forgot password fields.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\nDone! {changes} fixes applied.")
print("\nTest (Ctrl+F5):")
print("  1. Open tenant portal")
print("  2. Unit Number field should be EMPTY (not 'Portia')")
print("  3. Password field should be EMPTY")
print("  4. Click 'Forgot Password?' -> fields should be empty there too")