import shutil

print("Final fix for login and passwords...")

# === 1. FIX auth.py - ensure user_id is in login response ===
print("\n1. Checking auth.py...")
shutil.copy('api/routers/auth.py', 'api/routers/auth.py.bak5')

with open('api/routers/auth.py', 'r', encoding='utf-8') as f:
    auth = f.read()

if '"user_id"' not in auth:
    auth = auth.replace('"token": token,', '"token": token,\n            "user_id": user[0],', 1)
    print("   Added user_id to login response.")
else:
    print("   user_id already present.")

with open('api/routers/auth.py', 'w', encoding='utf-8') as f:
    f.write(auth)

# === 2. FIX dashboard.html - replace entire login function ===
print("\n2. Fixing dashboard.html...")
shutil.copy('dashboard.html', 'dashboard.html.bak6')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# New login function with pm_user_id and must_change check
new_login = """    async function login() {
        const user = document.getElementById("loginUser").value, pass = document.getElementById("loginPass").value, errorDiv = document.getElementById("loginError");
        try {
            const response = await fetch(`/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: user, password: pass }) });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Login failed");
            authToken = data.token; 
            localStorage.setItem('pm_token', authToken);
            localStorage.setItem('pm_role', data.role);
            localStorage.setItem('pm_prop_id', data.property_id || "null");
            localStorage.setItem('pm_username', user);
            localStorage.setItem('pm_user_id', data.user_id);
            localStorage.setItem('pm_must_change', data.must_change_password || false);
            if(data.must_change_password) {
                document.getElementById("loginScreen").style.display = "none";
                var fc = document.getElementById("screen-force-change-pw");
                if(fc) { fc.style.display = "flex"; } else { location.reload(); }
                return;
            }
            location.reload(); 
        } catch (error) { errorDiv.innerText = error.message; }
    }"""

# Find and replace the entire login function
lines = c.split('\n')
new_lines = []
skip = False
depth = 0
replaced = False

for line in lines:
    if not skip and ('async function login()' in line or ('function login()' in line and 'async' not in line and 'create' not in line and 'change' not in line)):
        skip = True
        depth = line.count('{') - line.count('}')
        new_lines.append(new_login)
        replaced = True
        if depth <= 0:
            skip = False
        continue
    if skip:
        depth += line.count('{') - line.count('}')
        if depth <= 0:
            skip = False
        continue
    new_lines.append(line)

if replaced:
    c = '\n'.join(new_lines)
    print("   Replaced login function.")
else:
    print("   WARNING: Could not find login function! Trying direct insert...")
    c = c.replace(
        "localStorage.setItem('pm_username', user);",
        "localStorage.setItem('pm_username', user);\n            localStorage.setItem('pm_user_id', data.user_id);\n            localStorage.setItem('pm_must_change', data.must_change_password || false);\n            if(data.must_change_password) {\n                document.getElementById('loginScreen').style.display = 'none';\n                var fc = document.getElementById('screen-force-change-pw');\n                if(fc) { fc.style.display = 'flex'; } else { location.reload(); }\n                return;\n            }"
    )
    print("   Added pm_user_id via direct insert.")

# Fix window.onload to check must_change
if 'pm_must_change' not in c or ('pm_must_change' in c and 'window.onload' in c and 'screen-force-change-pw' not in c.split('window.onload')[1][:500]):
    c = c.replace(
        'document.getElementById("loginScreen").style.display = "none";\n            document.getElementById("mainDashboard").style.display = "block";',
        'document.getElementById("loginScreen").style.display = "none";\n            if(localStorage.getItem("pm_must_change") === "true") {\n                var fc = document.getElementById("screen-force-change-pw");\n                if(fc) { fc.style.display = "flex"; }\n                else { document.getElementById("mainDashboard").style.display = "block"; }\n            } else {\n                document.getElementById("mainDashboard").style.display = "block";\n            }',
        1
    )
    print("   Fixed window.onload.")

# Ensure force-change screen exists
if 'screen-force-change-pw' not in c:
    force_html = '<div id="screen-force-change-pw" style="display:none;flex-direction:column;justify-content:center;align-items:center;min-height:100vh;background:#2c3e50;color:white;padding:20px;box-sizing:border-box;"><div style="background:white;padding:30px;border-radius:10px;width:100%;max-width:400px;"><h1 style="color:#2c3e50;text-align:center;">Set Your Password</h1><p style="color:#7f8c8d;font-size:0.9em;text-align:center;margin-bottom:15px;">Please set a new password.</p><input type="password" id="forceCurPw" placeholder="Temporary Password" style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:5px;box-sizing:border-box;"><input type="password" id="forceNewPw" placeholder="New Password (min 8 chars)" style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:5px;box-sizing:border-box;"><input type="password" id="forceConfirmPw" placeholder="Confirm New Password" style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:5px;box-sizing:border-box;"><button onclick="submitForceChangePw()" style="width:100%;padding:10px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;">Set Password</button><div id="forceChangePwError" style="color:red;margin-top:10px;display:none;"></div></div></div>'
    c = c.replace('<div id="mainDashboard"', force_html + '\n<div id="mainDashboard"', 1)
    print("   Added force-change screen.")

# Ensure submitForceChangePw function exists
if 'function submitForceChangePw' not in c:
    js = """
    async function submitForceChangePw() {
        var userId = localStorage.getItem("pm_user_id");
        var curPw = document.getElementById("forceCurPw").value;
        var newPw = document.getElementById("forceNewPw").value;
        var confPw = document.getElementById("forceConfirmPw").value;
        var errBox = document.getElementById("forceChangePwError");
        errBox.style.display = "none";
        try {
            var r = await fetch("/user-change-password/", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + authToken }, body: JSON.stringify({ user_id: parseInt(userId), current_password: curPw, new_password: newPw, confirm_password: confPw }) });
            var d = await r.json();
            if (!r.ok) throw new Error(d.detail || "Failed");
            document.getElementById("screen-force-change-pw").style.display = "none";
            document.getElementById("mainDashboard").style.display = "block";
            localStorage.setItem("pm_must_change", "false");
            loadAllData();
        } catch (e) { errBox.innerText = e.message; errBox.style.display = "block"; }
    }
"""
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + c[idx:]
    print("   Added submitForceChangePw function.")

# Fix submitChangePassword to handle missing user_id gracefully
if 'function submitChangePassword' in c:
    lines = c.split('\n')
    new_lines = []
    skip = False
    depth = 0
    ccp_replaced = False
    new_ccp = """    async function submitChangePassword() {
        var userId = localStorage.getItem('pm_user_id');
        if(!userId || userId === 'undefined' || userId === 'null') {
            alert('Session expired. Please log out and log in again.');
            return;
        }
        const curPw = document.getElementById('changeCurPw').value;
        const newPw = document.getElementById('changeNewPw').value;
        const confPw = document.getElementById('changeConfirmPw').value;
        const errBox = document.getElementById('changePwError');
        errBox.style.display = 'none';
        try {
            const r = await fetch('/user-change-password/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken }, body: JSON.stringify({ user_id: parseInt(userId), current_password: curPw, new_password: newPw, confirm_password: confPw }) });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Failed');
            alert('Password changed successfully!');
            closeChangePwModal();
        } catch (e) { errBox.innerText = e.message; errBox.style.display = 'block'; }
    }"""
    for line in lines:
        if not skip and 'function submitChangePassword' in line:
            skip = True
            depth = line.count('{') - line.count('}')
            new_lines.append(new_ccp)
            ccp_replaced = True
            if depth <= 0:
                skip = False
            continue
        if skip:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                skip = False
            continue
        new_lines.append(line)
    if ccp_replaced:
        c = '\n'.join(new_lines)
        print("   Replaced submitChangePassword function.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print("DONE! All fixes applied.")
print(f"{'='*50}")
print("\nCRITICAL: You MUST clear localStorage before testing!")
print("  1. Open http://127.0.0.1:8000/dashboard")
print("  2. Press F12 -> Console tab")
print("  3. Type: localStorage.clear()  and press Enter")
print("  4. Press F5 to refresh")
print("  5. Restart your server (Ctrl+C, then start again)")
print("  6. Login: admin / password123")
print("  7. Should see 'Set Your Password' screen")
print("  8. Temp pw = password123, set new pw")
print("  9. Dashboard loads")
print(" 10. Change Password button should work")