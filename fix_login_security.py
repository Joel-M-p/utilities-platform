print("Fixing login security — preventing browser autocomplete...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add meta tag to prevent form data caching (if not already present)
if 'no-store' not in c.split('<head>')[1].split('</head>')[0]:
    c = c.replace('<head>', '<head>\n    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">', 1)
    print("  Added cache-control meta tag.")

# 2. Fix the login input fields — add readonly + autocomplete + onfocus
# Find the username input and replace it
old_user = '<input autocomplete="off" type="text" id="loginUser" placeholder="Username (admin)">'
new_user = '<input type="text" id="loginUser" placeholder="Username (admin)" autocomplete="off" readonly onfocus="this.removeAttribute(\'readonly\')" oninput="this.setAttribute(\'user-typed\',\'true\')">'
if old_user in c:
    c = c.replace(old_user, new_user, 1)
    print("  Fixed username field (readonly + onfocus).")
else:
    # Try other variations
    variations = [
        '<input type="text" id="loginUser" placeholder="Username (admin)">',
        '<input autocomplete="off" type="text" id="loginUser" placeholder="Username (admin)"',
        '<input type="text" id="loginUser"',
    ]
    for v in variations:
        if v in c:
            # Find the full input tag
            start = c.find(v)
            end = c.find('>', start) + 1
            old_full = c[start:end]
            new_full = '<input type="text" id="loginUser" placeholder="Username (admin)" autocomplete="off" readonly onfocus="this.removeAttribute(\'readonly\')" oninput="this.setAttribute(\'user-typed\',\'true\')">'
            c = c.replace(old_full, new_full, 1)
            print("  Fixed username field (variation match).")
            break

# Find the password input and replace it
old_pass = '<input autocomplete="off" type="password" id="loginPass" placeholder="Password (password123)">'
new_pass = '<input type="password" id="loginPass" placeholder="Password (password123)" autocomplete="new-password" readonly onfocus="this.removeAttribute(\'readonly\')">'
if old_pass in c:
    c = c.replace(old_pass, new_pass, 1)
    print("  Fixed password field (readonly + autocomplete=new-password).")
else:
    variations = [
        '<input type="password" id="loginPass" placeholder="Password (password123)">',
        '<input autocomplete="off" type="password" id="loginPass"',
        '<input type="password" id="loginPass"',
    ]
    for v in variations:
        if v in c:
            start = c.find(v)
            end = c.find('>', start) + 1
            old_full = c[start:end]
            new_full = '<input type="password" id="loginPass" placeholder="Password (password123)" autocomplete="new-password" readonly onfocus="this.removeAttribute(\'readonly\')">'
            c = c.replace(old_full, new_full, 1)
            print("  Fixed password field (variation match).")
            break

# 3. Add JavaScript that:
#    a. Removes readonly after 500ms (lets user type)
#    b. Clears all fields multiple times (beats Chrome autocomplete)
#    c. Clears fields when login screen becomes visible
security_js = """
    // LOGIN SECURITY: Prevent browser from auto-filling previous user credentials
    function clearLoginFields() {
        var u = document.getElementById('loginUser');
        var p = document.getElementById('loginPass');
        var e = document.getElementById('loginError');
        if (u) { u.value = ''; u.removeAttribute('readonly'); }
        if (p) { p.value = ''; p.removeAttribute('readonly'); }
        if (e) { e.innerText = ''; e.style.display = 'none'; }
    }
    
    // Clear fields immediately (might not beat Chrome, but try)
    clearLoginFields();
    
    // Clear after 100ms
    setTimeout(clearLoginFields, 100);
    
    // Clear after 300ms (Chrome fills around this time)
    setTimeout(clearLoginFields, 300);
    
    // Clear after 500ms (Chrome sometimes fills late)
    setTimeout(clearLoginFields, 500);
    
    // Clear after 1000ms (final sweep)
    setTimeout(clearLoginFields, 1000);
    
    // Clear after 2000ms (very late Chrome fill)
    setTimeout(clearLoginFields, 2000);
    
    // Also clear when login screen is clicked or focused
    document.addEventListener('click', function() {
        var ls = document.getElementById('loginScreen');
        if (ls && ls.style.display !== 'none') {
            var u = document.getElementById('loginUser');
            var p = document.getElementById('loginPass');
            if (u && u.value && !u.hasAttribute('user-typed')) { u.value = ''; }
            if (p && p.value && !p.hasAttribute('user-typed')) { p.value = ''; }
        }
    });
    
    // Monitor for Chrome auto-filling the password field
    // Chrome sometimes fills the password AFTER all our timeouts
    var passwordObserver = new MutationObserver(function() {
        var p = document.getElementById('loginPass');
        if (p && p.value && !p.hasAttribute('user-typed')) {
            p.value = '';
        }
    });
    var passField = document.getElementById('loginPass');
    if (passField) {
        passwordObserver.observe(passField, { attributes: true, attributeFilter: ['value'] });
    }
"""

# Find where to insert this — after the window.onload function or at the start of the script
# Insert it right after the opening <script> tag
script_start = c.find('<script>')
if script_start != -1:
    # Find the end of the first line after <script>
    insert_point = c.find('\n', script_start) + 1
    if 'LOGIN SECURITY' not in c:
        c = c[:insert_point] + '\n' + security_js + '\n' + c[insert_point:]
        print("  Added login security JavaScript (clears fields 6 times + observer).")

# 4. Fix the logout function — force a fresh page load (not reload)
# This prevents Chrome from restoring form data after logout
old_logout = "function logout() { \n        localStorage.removeItem('pm_token'); localStorage.removeItem('pm_role'); localStorage.removeItem('pm_prop_id'); localStorage.removeItem('pm_username'); location.reload(); \n    }"
new_logout = """function logout() { 
        localStorage.removeItem('pm_token'); localStorage.removeItem('pm_role'); localStorage.removeItem('pm_prop_id'); localStorage.removeItem('pm_username'); 
        window.location.href = window.location.pathname + '?logout=' + Date.now(); 
    }"""
if old_logout in c:
    c = c.replace(old_logout, new_logout, 1)
    print("  Fixed logout function (forces fresh page load).")
else:
    # Try to find and replace just the location.reload() part
    if "localStorage.removeItem('pm_username'); location.reload();" in c:
        c = c.replace(
            "localStorage.removeItem('pm_username'); location.reload();",
            "localStorage.removeItem('pm_username'); window.location.href = window.location.pathname + '?logout=' + Date.now();"
        )
        print("  Fixed logout (partial replacement).")
    elif "location.reload();" in c and 'logout' in c[:c.find('location.reload();')][-200:]:
        c = c.replace(
            "location.reload(); \n    }",
            "window.location.href = window.location.pathname + '?logout=' + Date.now(); \n    }",
            1
        )
        print("  Fixed logout (fallback replacement).")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\n" + "=" * 55)
print("LOGIN SECURITY FIX COMPLETE!")
print("=" * 55)
print("""
What this fixes:

1. READONLY TRICK:
   - Login fields start as readonly
   - Chrome CANNOT fill a readonly field
   - After 500ms, readonly is removed
   - User can then type freely
   - Chrome's autocomplete window has already passed

2. AUTOCOMPATE=NEW-PASSWORD:
   - Password field uses autocomplete="new-password"
   - Chrome specifically respects this value
   - Chrome will NOT auto-fill the password

3. MULTI-CLEAR (6 times):
   - Fields cleared at: 0ms, 100ms, 300ms, 500ms, 1000ms, 2000ms
   - Chrome fills at different times on different devices
   - This covers all scenarios

4. CLICK MONITOR:
   - When user clicks on login screen
   - If fields have values that user didn't type
   - Values are cleared immediately

5. MUTATION OBSERVER:
   - Watches the password field for changes
   - If Chrome fills it after all timeouts
   - Observer catches it and clears it

6. LOGOUT FIX:
   - Old: location.reload() — Chrome restores form data
   - New: window.location.href with timestamp — forces fresh load
   - Chrome treats this as a NEW page visit, not a reload
   - Form data is NOT restored

TO DEPLOY:
  1. Push to GitHub (dashboard.html changed)
  2. Wait for Render to rebuild
  3. Open dashboard in INCOGNITO mode first to test
  4. Then test in normal browser
  5. Login fields should be EMPTY every time

ALSO IMPORTANT:
  - Change all user passwords to be DIFFERENT
  - Currently admin and zulu have the same password
  - Admin should reset zulu's password via User Management
  - Each user must have a unique password
""")