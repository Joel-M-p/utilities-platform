import shutil

print("Fixing user password login issues...")

# === 1. FIX auth.py - add user_id to login response ===
print("\n1. Fixing auth.py...")
shutil.copy('api/routers/auth.py', 'api/routers/auth.py.bak3')

with open('api/routers/auth.py', 'r', encoding='utf-8') as f:
    auth = f.read()

if '"user_id": user[0]' not in auth:
    auth = auth.replace(
        '"role": user[3],',
        '"user_id": user[0],\n            "role": user[3],',
        1
    )
    print("   Added user_id to login response.")
else:
    print("   user_id already in login response.")

with open('api/routers/auth.py', 'w', encoding='utf-8') as f:
    f.write(auth)

# === 2. FIX dashboard.html ===
print("\n2. Fixing dashboard.html...")
shutil.copy('dashboard.html', 'dashboard.html.bak4')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# Fix 1: Replace wrong pm_user_id with correct one
if "data.token.split('.')[0]" in c:
    c = c.replace(
        "localStorage.setItem('pm_user_id', data.token.split('.')[0] || '1');",
        "localStorage.setItem('pm_user_id', data.user_id);\n            localStorage.setItem('pm_must_change', data.must_change_password || false);"
    )
    changes += 1
    print("   Fixed pm_user_id storage.")

# Fix 2: Make window.onload check must_change_password
if "pm_must_change" not in c.split('window.onload')[1].split('loadProperties')[0]:
    c = c.replace(
        'document.getElementById("loginScreen").style.display = "none";\n            document.getElementById("mainDashboard").style.display = "block";',
        'document.getElementById("loginScreen").style.display = "none";\n            if(localStorage.getItem(\'pm_must_change\') === \'true\') {\n                document.getElementById("screen-force-change-pw").style.display = "flex";\n            } else {\n                document.getElementById("mainDashboard").style.display = "block";\n            }',
        1
    )
    changes += 1
    print("   Fixed window.onload to check must_change_password.")

# Fix 3: After force-change succeeds, clear the flag
if "localStorage.setItem('pm_must_change', 'false')" not in c:
    c = c.replace(
        "document.getElementById('mainDashboard').style.display = 'block';\n            loadAllData();",
        "document.getElementById('mainDashboard').style.display = 'block';\n            localStorage.setItem('pm_must_change', 'false');\n            loadAllData();"
    )
    changes += 1
    print("   Fixed force-change success handler.")

# Check if force-change screen exists
if 'screen-force-change-pw' not in c:
    print("   WARNING: Force-change screen not found! Adding it...")
    force_screen = """<!-- FORCE CHANGE PASSWORD SCREEN -->
<div id="screen-force-change-pw" class="force-change-screen" style="display:none;">
    <div class="login-card">
        <h1>Set Your Password</h1>
        <p style="color:#7f8c8d; font-size:0.9em; text-align:center; margin-bottom:15px;">Please set a new password to secure your account.</p>
        <input type="password" id="forceCurPw" placeholder="Temporary Password" style="width:100%;padding:10px;margin-bottom:10px;box-sizing:border-box;">
        <input type="password" id="forceNewPw" placeholder="New Password (min 8 chars)" style="width:100%;padding:10px;margin-bottom:10px;box-sizing:border-box;">
        <input type="password" id="forceConfirmPw" placeholder="Confirm New Password" style="width:100%;padding:10px;margin-bottom:10px;box-sizing:border-box;">
        <button onclick="submitForceChangePw()" style="width:100%;padding:10px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;">Set Password</button>
        <div id="forceChangePwError" style="color:red; margin-top:10px; display:none;"></div>
    </div>
</div>
"""
    c = c.replace('<div id="mainDashboard"', force_screen + '\n<div id="mainDashboard"', 1)
    changes += 1
    print("   Added force-change screen.")

# Check if submitForceChangePw function exists
if 'function submitForceChangePw' not in c:
    print("   WARNING: submitForceChangePw function not found! Adding it...")
    js = """
    async function submitForceChangePw() {
        const userId = localStorage.getItem('pm_user_id');
        const curPw = document.getElementById('forceCurPw').value;
        const newPw = document.getElementById('forceNewPw').value;
        const confPw = document.getElementById('forceConfirmPw').value;
        const errBox = document.getElementById('forceChangePwError');
        errBox.style.display = 'none';
        try {
            const r = await fetch('/user-change-password/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken }, body: JSON.stringify({ user_id: parseInt(userId), current_password: curPw, new_password: newPw, confirm_password: confPw }) });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Failed');
            document.getElementById('screen-force-change-pw').style.display = 'none';
            document.getElementById('mainDashboard').style.display = 'block';
            localStorage.setItem('pm_must_change', 'false');
            loadAllData();
        } catch (e) { errBox.innerText = e.message; errBox.style.display = 'block'; }
    }
"""
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + js + '\n' + c[idx:]
    changes += 1
    print("   Added submitForceChangePw function.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print(f"DONE! {changes} fixes applied.")
print(f"{'='*50}")
print("\nIMPORTANT: You MUST clear localStorage before testing!")
print("  Option A: Use Incognito mode (Ctrl+Shift+N)")
print("  Option B: Press F12 -> Console -> type: localStorage.clear()")
print("\nThen:")
print("  1. Restart your server")
print("  2. Open http://127.0.0.1:8000/dashboard (incognito or after clearing)")
print("  3. Login: admin / password123")
print("  4. You should see 'Set Your Password' screen")
print("  5. Temp password = password123, then set your own")
print("  6. Dashboard loads")
print("  7. 'Change Password' button should now work")