import shutil

# === 1. UPDATE auth.py ===
print("Updating auth.py...")
shutil.copy('api/routers/auth.py', 'api/routers/auth.py.bak')

with open('api/routers/auth.py', 'r', encoding='utf-8') as f:
    auth_content = f.read()

if 'tenant-forgot-password' in auth_content:
    print("  Already exists in auth.py.")
else:
    new_endpoint = """
@router.post("/tenant-forgot-password/")
def api_tenant_forgot_password(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        property_id = payload.get("property_id")
        unit_number = payload.get("unit_number")
        email = payload.get("email")
        
        if not property_id or not unit_number or not email:
            raise HTTPException(status_code=400, detail="Property, Unit Number, and Email are required")
        
        cursor.execute(\"\"\"
            SELECT id, email, property_id 
            FROM tenants 
            WHERE unit_number = %s AND property_id = %s AND status != 'VACATED'
            ORDER BY id DESC
            LIMIT 1
        \"\"\", (unit_number, property_id))
        tenant_data = cursor.fetchone()
        
        if not tenant_data:
            raise HTTPException(status_code=404, detail="No active tenant found for this Unit Number")
        
        if tenant_data[1].strip().lower() != email.strip().lower():
            raise HTTPException(status_code=401, detail="Email does not match our records")
        
        temp_password = generate_temp_password()
        hashed = hash_password(temp_password)
        
        cursor.execute(\"\"\"
            UPDATE tenants 
            SET password_hash = %s, must_change_password = TRUE
            WHERE id = %s
        \"\"\", (hashed, tenant_data[0]))
        conn.commit()
        
        return {
            "status": "success",
            "message": "A temporary password has been generated.",
            "temp_password": temp_password,
            "must_change": True
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

"""
    auth_content = auth_content.replace(
        '# --- USER MANAGEMENT ENDPOINTS ---',
        new_endpoint + '# --- USER MANAGEMENT ENDPOINTS ---'
    )
    with open('api/routers/auth.py', 'w', encoding='utf-8') as f:
        f.write(auth_content)
    print("  Added forgot password endpoint.")

# === 2. UPDATE tenant_portal.html ===
print("\nUpdating tenant_portal.html...")
shutil.copy('tenant_portal.html', 'tenant_portal.html.bak')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    portal_content = f.read()

if 'tShowForgotPassword' in portal_content:
    print("  Already exists in tenant_portal.html.")
else:
    # Add "Forgot Password?" link after login button
    portal_content = portal_content.replace(
        '<button onclick="tLogin()">Login</button>',
        '<button onclick="tLogin()">Login</button>\n        <p style="text-align:center; margin-top:15px;"><a href="#" onclick="tShowForgotPassword()" style="color:var(--secondary); text-decoration:none; font-size:0.9em;">Forgot Password?</a></p>'
    )
    
    # Add forgot password screen before MAIN APP
    forgot_screen = """<!-- FORGOT PASSWORD SCREEN -->
<div id="screen-forgot-password" class="force-change-screen">
    <div class="login-logo">Reset Password</div>
    <div class="login-card">
        <h2>Forgot Password</h2>
        <p style="text-align:center; color:var(--gray); font-size:0.9em; margin-bottom:15px;">Enter your details below. A temporary password will be generated for you.</p>
        <select id="forgot_property"><option value="">Select Property...</option></select>
        <input type="text" id="forgot_unit_number" placeholder="Unit Number">
        <input type="email" id="forgot_email" placeholder="Email Address">
        <button onclick="tSubmitForgotPassword()">Send Reset</button>
        <button style="background: var(--gray);" onclick="tBackToLogin()">Back to Login</button>
        <div id="forgotError" class="login-error"></div>
        <div id="forgotSuccess" style="display:none; background:#e8f8f5; padding:15px; border-radius:8px; margin-top:15px;">
            <p style="color:var(--success); font-weight:bold; margin:0 0 10px 0;">Temporary password generated!</p>
            <p style="margin:0 0 5px 0;">Your temporary password is:</p>
            <p style="font-size:1.2em; font-weight:bold; text-align:center; color:var(--dark); margin:10px 0;" id="forgotTempPw"></p>
            <p style="font-size:0.8em; color:var(--gray); margin:10px 0 0 0;">Use this to log in. You will be asked to set your own password.</p>
            <button onclick="tBackToLogin()" style="margin-top:10px;">Go to Login</button>
        </div>
    </div>
</div>

<!-- MAIN APP -->"""
    portal_content = portal_content.replace('<!-- MAIN APP -->', forgot_screen)
    
    # Add JavaScript functions before last </script>
    new_functions = """
    function tShowForgotPassword() {
        document.getElementById('screen-login').style.display = 'none';
        document.getElementById('screen-forgot-password').style.display = 'flex';
        const loginProp = document.getElementById('login_property');
        const forgotProp = document.getElementById('forgot_property');
        forgotProp.innerHTML = loginProp.innerHTML;
        forgotProp.value = loginProp.value;
        document.getElementById('forgotSuccess').style.display = 'none';
        document.getElementById('forgotError').style.display = 'none';
    }

    function tBackToLogin() {
        document.getElementById('screen-forgot-password').style.display = 'none';
        document.getElementById('screen-login').style.display = 'flex';
        document.getElementById('forgotSuccess').style.display = 'none';
        document.getElementById('forgotError').style.display = 'none';
        document.getElementById('forgot_unit_number').value = '';
        document.getElementById('forgot_email').value = '';
    }

    async function tSubmitForgotPassword() {
        const property_id = document.getElementById('forgot_property').value;
        const unitNumber = document.getElementById('forgot_unit_number').value;
        const email = document.getElementById('forgot_email').value;
        const errBox = document.getElementById('forgotError');
        const successBox = document.getElementById('forgotSuccess');
        errBox.style.display = 'none';
        successBox.style.display = 'none';
        
        if(!property_id) { errBox.innerText = "Please select your property."; errBox.style.display = 'block'; return; }
        if(!unitNumber) { errBox.innerText = "Please enter your unit number."; errBox.style.display = 'block'; return; }
        if(!email) { errBox.innerText = "Please enter your email."; errBox.style.display = 'block'; return; }
        
        try {
            const r = await fetch('/tenant-forgot-password/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ property_id: parseInt(property_id), unit_number: unitNumber, email: email })
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || "Failed to reset password");
            
            document.getElementById('forgotTempPw').innerText = d.temp_password;
            successBox.style.display = 'block';
        } catch (e) {
            errBox.innerText = e.message;
            errBox.style.display = 'block';
        }
    }
</script>"""
    
    idx = portal_content.rfind('</script>')
    if idx != -1:
        portal_content = portal_content[:idx] + new_functions + portal_content[idx + 9:]
    
    with open('tenant_portal.html', 'w', encoding='utf-8') as f:
        f.write(portal_content)
    print("  Added forgot password screen.")

print("\n" + "=" * 50)
print("DONE! Forgot Password feature added.")
print("=" * 50)
print("\nRestart your server, then:")
print("  1. Open http://127.0.0.1:8000/tenant (Ctrl+F5)")
print("  2. Click 'Forgot Password?'")
print("  3. Enter Property + Unit Number + Email")
print("  4. Get temp password")
print("  5. Login with it, set your own password")