import shutil

print("Updating dashboard.html for user password management...")
shutil.copy('dashboard.html', 'dashboard.html.bak3')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# 1. Add CSS for new screens
if '.force-change-screen' not in c:
    css = """<style>
        .force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: #2c3e50; color: white; padding: 20px; box-sizing: border-box; }
        .force-change-screen .login-card { background: white; padding: 30px; border-radius: 10px; width: 100%; max-width: 400px; box-shadow: 0px 0px 10px #ccc; }
        .force-change-screen .login-card h1 { color: #2c3e50; }
        .force-change-screen .login-card input { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; }
        .force-change-screen .login-card button { width: 100%; margin: 0; }
        .change-pw-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 300; }
        .change-pw-content { background: white; margin: 20px; border-radius: 10px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; }
        .change-pw-content h2 { color: #2c3e50; margin-top: 0; }
        .change-pw-content input { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; }
        .change-pw-content button { width: 100%; margin: 0 0 10px 0; }
        .btn-change-pw { background-color: #2980b9; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 0.9em; margin-right: 5px; }
        .btn-change-pw:hover { background-color: #3498db; }
        .btn-reset-user { background-color: #2980b9; padding: 5px 10px; font-size: 12px; }
        .btn-reset-user:hover { background-color: #3498db; }
    """
    c = c.replace('<style>', css + '\n<style>', 1)
    changes += 1
    print("  Added CSS.")

# 2. Replace password field with email field in Create User form
if 'newPassword' in c and 'newUserEmail' not in c:
    c = c.replace(
        '<input type="password" id="newPassword" placeholder="Password" title="Enter a secure password.">',
        '<input type="email" id="newUserEmail" placeholder="Email Address" title="Enter the user email. A temp password will be auto-generated.">'
    )
    changes += 1
    print("  Replaced password field with email field in Create User form.")

# 3. Add Forgot Password link on login screen
if 'showUserForgotPassword' not in c:
    c = c.replace(
        '<div id="loginError" style="color: red; margin-top: 10px;"></div>\n</div>',
        '<div id="loginError" style="color: red; margin-top: 10px;"></div>\n        <p style="text-align:center; margin-top:15px;"><a href="#" onclick="showUserForgotPassword()" style="color:#3498db; text-decoration:none; font-size:0.9em;">Forgot Password?</a></p>\n</div>'
    )
    changes += 1
    print("  Added Forgot Password link.")

# 4. Add Change Password button in header
if 'showChangePassword' not in c:
    c = c.replace(
        '<button onclick="logout()">Logout</button>',
        '<button class="btn-change-pw" onclick="showChangePassword()">Change Password</button> <button onclick="logout()">Logout</button>'
    )
    changes += 1
    print("  Added Change Password button in header.")

# 5. Add Reset Password button in users table
if 'resetUserPassword' not in c:
    c = c.replace(
        '<th>Assigned Property</th></tr></thead>',
        '<th>Assigned Property</th><th>Actions</th></tr></thead>'
    )
    c = c.replace(
        "users_list.append({\n                \"id\": u[0],\n                \"username\": u[1],\n                \"role\": u[2],\n                \"property_id\": u[3],\n                \"property_name\": u[4] if u[4] else \"All Properties (Admin)\"\n            })",
        "users_list.append({\n                \"id\": u[0],\n                \"username\": u[1],\n                \"role\": u[2],\n                \"property_id\": u[3],\n                \"property_name\": u[4] if u[4] else \"All Properties (Admin)\",\n                \"email\": u[5] or \"\"\n            })"
    )
    c = c.replace(
        '<td>${u.property_name || \'All\'}</td></tr>',
        '<td>${u.property_name || \'All\'}</td><td><button onclick="resetUserPassword(${u.id})" class="btn-reset-user">Reset Password</button></td></tr>'
    )
    changes += 1
    print("  Added Reset Password button in users table.")

# 6. Add Forgot Password screen before main dashboard
if 'screen-user-forgot' not in c:
    forgot_screen = """<!-- USER FORGOT PASSWORD SCREEN -->
<div id="screen-user-forgot" class="force-change-screen">
    <div class="login-card">
        <h1>Forgot Password</h1>
        <p style="color:#7f8c8d; font-size:0.9em; text-align:center; margin-bottom:15px;">Enter your username and email. A temp password will be generated.</p>
        <input type="text" id="forgotUsername" placeholder="Username">
        <input type="email" id="forgotEmail" placeholder="Email Address">
        <button onclick="submitUserForgotPassword()">Send Reset</button>
        <button style="background:#7f8c8d;" onclick="backToUserLogin()">Back to Login</button>
        <div id="userForgotError" style="color:red; margin-top:10px; display:none;"></div>
        <div id="userForgotSuccess" style="display:none; background:#e8f8f5; padding:15px; border-radius:5px; margin-top:15px;">
            <p style="color:#27ae60; font-weight:bold; margin:0 0 10px 0;">Temp password generated!</p>
            <p style="margin:0 0 5px 0;">Your temporary password is:</p>
            <p style="font-size:1.2em; font-weight:bold; text-align:center; color:#2c3e50; margin:10px 0;" id="userForgotTempPw"></p>
            <p style="font-size:0.8em; color:#7f8c8d; margin:10px 0 0 0;">Use this to log in. You will be asked to set your own password.</p>
            <button onclick="backToUserLogin()" style="margin-top:10px;">Go to Login</button>
        </div>
    </div>
</div>
"""
    c = c.replace('<div id="mainDashboard"', forgot_screen + '\n<div id="mainDashboard"', 1)
    changes += 1
    print("  Added Forgot Password screen.")

# 7. Add Change Password modal before </body>
if 'changePwModal' not in c:
    modal = """<!-- CHANGE PASSWORD MODAL -->
<div id="changePwModal" class="change-pw-modal">
    <div class="change-pw-content">
        <h2>Change Password</h2>
        <input type="password" id="changeCurPw" placeholder="Current Password">
        <input type="password" id="changeNewPw" placeholder="New Password (min 8 chars)">
        <input type="password" id="changeConfirmPw" placeholder="Confirm New Password">
        <button style="background:#3498db;" onclick="submitChangePassword()">Change Password</button>
        <button style="background:#7f8c8d;" onclick="closeChangePwModal()">Cancel</button>
        <div id="changePwError" style="color:red; margin-top:10px; display:none;"></div>
    </div>
</div>
"""
    c = c.replace('</body>', modal + '\n</body>', 1)
    changes += 1
    print("  Added Change Password modal.")

# 8. Add Force Change Password screen
if 'screen-force-change-pw' not in c:
    force_screen = """<!-- FORCE CHANGE PASSWORD SCREEN -->
<div id="screen-force-change-pw" class="force-change-screen">
    <div class="login-card">
        <h1>Set Your Password</h1>
        <p style="color:#7f8c8d; font-size:0.9em; text-align:center; margin-bottom:15px;">Please set a new password to secure your account.</p>
        <input type="password" id="forceCurPw" placeholder="Temporary Password">
        <input type="password" id="forceNewPw" placeholder="New Password (min 8 chars)">
        <input type="password" id="forceConfirmPw" placeholder="Confirm New Password">
        <button onclick="submitForceChangePw()">Set Password</button>
        <div id="forceChangePwError" style="color:red; margin-top:10px; display:none;"></div>
    </div>
</div>
"""
    c = c.replace('<div id="mainDashboard"', force_screen + '\n<div id="mainDashboard"', 1)
    changes += 1
    print("  Added Force Change Password screen.")

# 9. Add JavaScript functions before </script>
if 'function showUserForgotPassword' not in c:
    js = """
    // --- USER PASSWORD FUNCTIONS ---
    function showUserForgotPassword() {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('screen-user-forgot').style.display = 'flex';
        document.getElementById('userForgotError').style.display = 'none';
        document.getElementById('userForgotSuccess').style.display = 'none';
    }
    function backToUserLogin() {
        document.getElementById('screen-user-forgot').style.display = 'none';
        document.getElementById('loginScreen').style.display = 'block';
        document.getElementById('userForgotSuccess').style.display = 'none';
        document.getElementById('userForgotError').style.display = 'none';
        document.getElementById('forgotUsername').value = '';
        document.getElementById('forgotEmail').value = '';
    }
    async function submitUserForgotPassword() {
        const username = document.getElementById('forgotUsername').value;
        const email = document.getElementById('forgotEmail').value;
        const errBox = document.getElementById('userForgotError');
        const successBox = document.getElementById('userForgotSuccess');
        errBox.style.display = 'none';
        successBox.style.display = 'none';
        if(!username || !email) { errBox.innerText = 'Please enter username and email.'; errBox.style.display = 'block'; return; }
        try {
            const r = await fetch('/user-forgot-password/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, email }) });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Failed');
            document.getElementById('userForgotTempPw').innerText = d.temp_password;
            successBox.style.display = 'block';
        } catch (e) { errBox.innerText = e.message; errBox.style.display = 'block'; }
    }
    function showChangePassword() {
        document.getElementById('changePwModal').style.display = 'block';
        document.getElementById('changePwError').style.display = 'none';
        document.getElementById('changeCurPw').value = '';
        document.getElementById('changeNewPw').value = '';
        document.getElementById('changeConfirmPw').value = '';
    }
    function closeChangePwModal() { document.getElementById('changePwModal').style.display = 'none'; }
    async function submitChangePassword() {
        const userId = localStorage.getItem('pm_user_id');
        const curPw = document.getElementById('changeCurPw').value;
        const newPw = document.getElementById('changeNewPw').value;
        const confPw = document.getElementById('changeConfirmPw').value;
        const errBox = document.getElementById('changePwError');
        errBox.style.display = 'none';
        try {
            const r = await fetch('/user-change-password/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` }, body: JSON.stringify({ user_id: parseInt(userId), current_password: curPw, new_password: newPw, confirm_password: confPw }) });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Failed');
            alert('Password changed successfully!');
            closeChangePwModal();
        } catch (e) { errBox.innerText = e.message; errBox.style.display = 'block'; }
    }
    async function submitForceChangePw() {
        const userId = localStorage.getItem('pm_user_id');
        const curPw = document.getElementById('forceCurPw').value;
        const newPw = document.getElementById('forceNewPw').value;
        const confPw = document.getElementById('forceConfirmPw').value;
        const errBox = document.getElementById('forceChangePwError');
        errBox.style.display = 'none';
        try {
            const r = await fetch('/user-change-password/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` }, body: JSON.stringify({ user_id: parseInt(userId), current_password: curPw, new_password: newPw, confirm_password: confPw }) });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Failed');
            document.getElementById('screen-force-change-pw').style.display = 'none';
            document.getElementById('mainDashboard').style.display = 'block';
            loadAllData();
        } catch (e) { errBox.innerText = e.message; errBox.style.display = 'block'; }
    }
    async function resetUserPassword(id) {
        if(!confirm('Generate a new temp password for this user?')) return;
        try {
            const r = await fetch(`/admin-reset-user-password/${id}/`, { method: 'POST', headers: getAuthHeaders() });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            alert('TEMP PASSWORD GENERATED\\n\\nUsername: ' + d.username + '\\n\\nTemp Password: ' + d.temp_password + '\\n\\nShare this securely with the user. They will be forced to set their own password on next login.');
            logAction('Reset User Password', 'User ID: ' + id);
        } catch (e) { alert('Error: ' + e.message); }
    }
"""
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]
    changes += 1
    print("  Added JavaScript functions.")

# 10. Modify login() function to handle must_change_password
if 'pm_user_id' not in c:
    c = c.replace(
        "localStorage.setItem('pm_username', user);",
        "localStorage.setItem('pm_username', user);\n            localStorage.setItem('pm_user_id', data.token.split('.')[0] || '1');\n            if(data.must_change_password) {\n                document.getElementById('loginScreen').style.display = 'none';\n                document.getElementById('screen-force-change-pw').style.display = 'flex';\n                return;\n            }"
    )
    changes += 1
    print("  Modified login() to check must_change_password.")

# 11. Modify createUser() to not send password and show temp password
if 'newUserEmail' in c and 'temp_password' not in c.split('createUser')[1].split('loadUsers')[0]:
    c = c.replace(
        "const password = document.getElementById(\"newPassword\").value;",
        "const email = document.getElementById(\"newUserEmail\").value;"
    )
    c = c.replace(
        "if(!username || !password) { alert(\"Username and password required\"); return; }",
        "if(!username || !email) { alert(\"Username and email required\"); return; }"
    )
    c = c.replace(
        "body: JSON.stringify({username, password, role, property_id})",
        "body: JSON.stringify({username, email, role, property_id})"
    )
    c = c.replace(
        'alert(d.message); logAction("Created User", `Username: ${username}, Role: ${role}`); loadUsers();',
        'alert(d.message + "\\n\\nTemp Password: " + d.temp_password + "\\n\\nShare this securely with the user. They will be forced to set their own password on first login."); logAction("Created User", `Username: ${username}, Role: ${role}`); loadUsers();'
    )
    changes += 1
    print("  Modified createUser() to auto-generate temp password.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print(f"DONE! {changes} changes made to dashboard.html.")
print(f"{'='*55}")
print("\nRestart your server, then test:")
print("  1. http://127.0.0.1:8000/dashboard (Ctrl+F5)")
print("  2. Login: admin / password123")
print("  3. You'll be forced to set a new password")
print("  4. After setting it, dashboard loads")
print("  5. Try 'Forgot Password?' on login screen")
print("  6. Try 'Change Password' in header")
print("  7. Create a new user -> temp password auto-generated")
print("  8. Reset Password button in User Management")