import re

print("Fixing login + autocomplete...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Add autocomplete="off" to ALL inputs and selects ===
lines = c.split('\n')
new_lines = []
for line in lines:
    if '<input' in line and 'autocomplete' not in line:
        line = line.replace('<input', '<input autocomplete="off"', 1)
    if '<select' in line and 'autocomplete' not in line and 'id="' in line:
        line = line.replace('<select', '<select autocomplete="off"', 1)
    new_lines.append(line)
c = '\n'.join(new_lines)
print("  Added autocomplete=off to all inputs and selects.")

# === 2. Add page-load clearing (with delay to override browser autofill) ===
clear_script = """
    window.addEventListener('load', function() {
        setTimeout(function() {
            var lu = document.getElementById('loginUser');
            var lp = document.getElementById('loginPass');
            if (lu) lu.value = '';
            if (lp) lp.value = '';
            var le = document.getElementById('loginError');
            if (le) le.innerText = '';
        }, 200);
    });
"""
if "window.addEventListener('load'" not in c or 'loginUser' not in (c.split("window.addEventListener('load'")[1][:300] if "window.addEventListener('load'" in c else ''):
    idx = c.rfind('</script>')
    if idx != -1:
        c = c[:idx] + clear_script + '\n' + c[idx:]
        print("  Added page-load clearing for login fields.")

# === 3. Override login function at the END (guaranteed to work) ===
login_override = """
    // OVERRIDDEN: Clean login function
    async function login() {
        var user = document.getElementById("loginUser").value;
        var pass = document.getElementById("loginPass").value;
        var errorDiv = document.getElementById("loginError");
        if (errorDiv) { errorDiv.innerText = ""; errorDiv.style.display = "none"; }
        
        if (!user || !pass) {
            if (errorDiv) { errorDiv.innerText = "Please enter username and password."; errorDiv.style.display = "block"; }
            return;
        }
        
        try {
            var response = await fetch('/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            
            if (!response.ok) {
                var errData = await response.json().catch(function() { return {}; });
                throw new Error(errData.detail || "Login failed. Check username and password.");
            }
            
            var data = await response.json();
            authToken = data.token;
            localStorage.setItem('pm_token', authToken);
            localStorage.setItem('pm_role', data.role);
            localStorage.setItem('pm_prop_id', data.property_id || "null");
            localStorage.setItem('pm_username', user);
            localStorage.setItem('pm_user_id', String(data.user_id || '1'));
            localStorage.setItem('pm_must_change', String(data.must_change_password || false));
            
            if (data.must_change_password) {
                var ls = document.getElementById("loginScreen");
                if (ls) ls.style.display = "none";
                var fc = document.getElementById("screen-force-change-pw");
                if (fc) { fc.style.display = "flex"; }
                else { location.reload(); }
                return;
            }
            
            location.reload();
        } catch (error) {
            if (errorDiv) { errorDiv.innerText = error.message; errorDiv.style.display = "block"; }
        }
    }
"""
idx = c.rfind('</script>')
if idx != -1:
    c = c[:idx] + login_override + '\n' + c[idx:]
    print("  Added overridden login function.")

# === 4. Make sure login button calls login() ===
if 'onclick="login()"' not in c and 'onclick="login (' not in c:
    c = c.replace('onclick="login()"', 'onclick="login()"')
if 'onclick="login()"' not in c:
    # Try to find the login button
    c = re.sub(r'<button[^>]*>Log In</button>', '<button onclick="login()">Log In</button>', c)
    print("  Fixed login button onclick.")

# === 5. Make sure loginError div exists ===
if 'id="loginError"' not in c:
    c = c.replace(
        '<button onclick="login()">Log In</button>',
        '<button onclick="login()">Log In</button>\n        <div id="loginError" style="color: red; margin-top: 10px; display: none;"></div>'
    )
    print("  Added loginError div.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone!")
print("\nIMPORTANT: After running this script:")
print("  1. Restart your server (Ctrl+C, then start again)")
print("  2. Open dashboard in INCOGNITO mode (Ctrl+Shift+N)")
print("     OR clear cache: F12 -> Console -> type: localStorage.clear()")
print("  3. Press Ctrl+F5")
print("  4. Login fields should be EMPTY")
print("  5. Enter admin / password123")
print("  6. Press Log In — should work!")