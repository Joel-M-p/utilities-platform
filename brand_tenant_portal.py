import shutil

print("Branding tenant portal as ELUP...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_brand')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace CSS variables with ELUP brand colors ===
old_root = """:root {
            --primary: #2c3e50;
            --secondary: #3498db;
            --success: #27ae60;
            --danger: #e74c3c;
            --warning: #f39c12;
            --light: #ecf0f1;
            --dark: #2c3e50;
            --gray: #7f8c8d;
            --bg: #f4f7f6;
        }"""

new_root = """:root {
            --primary: #0a2540;
            --secondary: #1976d2;
            --success: #2e7d32;
            --danger: #c62828;
            --warning: #f9a825;
            --light: #e3f2fd;
            --dark: #0a2540;
            --gray: #607d8b;
            --bg: #f0f4f8;
            --accent: #4fc3f7;
        }"""

if old_root in c:
    c = c.replace(old_root, new_root)
    print("  Updated brand colors.")
else:
    # Try flexible match
    import re
    c = re.sub(r':root\s*\{[^}]*\}', new_root, c, count=1)
    print("  Updated brand colors (flexible match).")

# === 2. Update login screen ===
# Replace login background with ELUP gradient
c = c.replace(
    '.login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background: var(--primary);',
    '.login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #0a2540 0%, #1565c0 50%, #1976d2 100%);'
)

# Replace login logo text
c = c.replace(
    '<div class="login-logo">Tenant Portal</div>',
    '<div class="login-logo">ELUP</div>\n        <div style="color: white; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px; opacity: 0.8;">SERVICES &bull; Utilities Management</div>'
)

# Add B-BBEE badge to login screen
if 'B-BBEE' not in c:
    c = c.replace(
        '<div id="loginError" class="login-error">',
        '<div style="text-align:center; margin-top:15px;"><span style="background:rgba(255,255,255,0.15); color:white; padding:4px 12px; border-radius:12px; font-size:0.7em;">Level 1 B-BBEE</span></div>\n        <div id="loginError" class="login-error">'
    )

# Add subtle shadow to login card
c = c.replace(
    '.login-card { background: white; padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }',
    '.login-card { background: white; padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }'
)

# Style login logo
c = c.replace(
    '.login-logo { font-size: 2.2em; font-weight: 800; margin-bottom: 30px; letter-spacing: 1px; text-align: center; }',
    '.login-logo { font-size: 2.8em; font-weight: 900; margin-bottom: 5px; letter-spacing: 4px; text-align: center; color: white; }'
)

# Update login button
c = c.replace(
    '.login-card button { width: 100%; padding: 15px; background: var(--secondary); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }',
    '.login-card button { width: 100%; padding: 15px; background: linear-gradient(135deg, #1976d2, #1565c0); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(25,118,210,0.3); transition: all 0.3s; }\n        .login-card button:hover { box-shadow: 0 6px 20px rgba(25,118,210,0.5); transform: translateY(-1px); }'
)

print("  Updated login screen with ELUP branding.")

# === 3. Update header ===
c = c.replace(
    '<span id="appHeaderText">My Utilities</span>',
    '<span id="appHeaderText">ELUP Utilities</span>'
)

# Update header background
c = c.replace(
    '.app-header { background: var(--primary);',
    '.app-header { background: linear-gradient(135deg, #0a2540, #1565c0);'
)

print("  Updated header with ELUP branding.")

# === 4. Update wallet card ===
c = c.replace(
    '.wallet-card { background: linear-gradient(135deg, var(--primary), var(--secondary));',
    '.wallet-card { background: linear-gradient(135deg, #0a2540, #1976d2);'
)

# Update fund button
c = c.replace(
    '.btn-fund { background: white; color: var(--primary);',
    '.btn-fund { background: white; color: #0a2540;'
)

print("  Updated wallet card with brand gradient.")

# === 5. Update bottom navigation ===
c = c.replace(
    '.nav-btn.active { color: var(--secondary); }',
    '.nav-btn.active { color: #1976d2; font-weight: bold; }'
)

# Add bottom nav shadow
c = c.replace(
    '.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: 1px solid #ddd;',
    '.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: none; box-shadow: 0 -4px 20px rgba(0,0,0,0.08);'
)

print("  Updated bottom navigation.")

# === 6. Add card shadows and transitions ===
if 'card-shadow' not in c:
    c = c.replace(
        '.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }',
        '.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(10,37,64,0.08); transition: box-shadow 0.3s; }\n        .card:hover { box-shadow: 0 8px 25px rgba(10,37,64,0.12); }'
    )
    print("  Added card shadows and hover effects.")

# === 7. Update KPI cards ===
c = c.replace(
    '.kpi-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }',
    '.kpi-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 15px rgba(10,37,64,0.08); text-align: center; }'
)

# === 8. Update alert banners ===
c = c.replace(
    '.alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }',
    '.alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; box-shadow: 0 4px 15px rgba(10,37,64,0.08); }'
)

# === 9. Update force-change and forgot password screens ===
c = c.replace(
    '.force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: var(--primary);',
    '.force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #0a2540, #1565c0);'
)

print("  Updated all screens with ELUP branding.")

# === 10. Update change password modal ===
c = c.replace(
    '.change-pw-content { background: white; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; }',
    '.change-pw-content { background: white; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }'
)

# === 11. Update WhatsApp button color to match brand ===
c = c.replace(
    '.whatsapp-float { position: fixed; bottom: 80px; right: 20px; background: #25D366;',
    '.whatsapp-float { position: fixed; bottom: 80px; right: 20px; background: #25D366;'
)

# === 12. Add smooth transitions ===
if 'transition: all 0.3s' not in c:
    c = c.replace(
        '.nav-btn { background: none; border: none; color: var(--gray);',
        '.nav-btn { background: none; border: none; color: #607d8b;'
    )
    c = c.replace(
        '.nav-icon { font-size: 1.5em; margin-bottom: 3px; }',
        '.nav-icon { font-size: 1.5em; margin-bottom: 3px; transition: transform 0.2s; }\n        .nav-btn.active .nav-icon { transform: scale(1.15); }'
    )

# === 13. Update forgot password screen logo ===
c = c.replace(
    '<div class="login-logo">Set Your Password</div>',
    '<div class="login-logo" style="font-size: 1.5em; color: white;">ELUP</div>\n        <div style="color: white; font-size: 0.8em; letter-spacing: 2px; margin-bottom: 20px; opacity: 0.8;">Set Your Password</div>'
)

c = c.replace(
    '<div class="login-logo">Reset Password</div>',
    '<div class="login-logo" style="font-size: 1.5em; color: white;">ELUP</div>\n        <div style="color: white; font-size: 0.8em; letter-spacing: 2px; margin-bottom: 20px; opacity: 0.8;">Reset Password</div>'
)

print("  Updated forgot/change password screens.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print("ELUP BRANDING COMPLETE!")
print(f"{'='*50}")
print("\nWhat changed:")
print("  1. Login screen: Navy gradient + 'ELUP' + 'SERVICES'")
print("  2. B-BBEE Level 1 badge on login")
print("  3. Header: 'ELUP Utilities' with gradient")
print("  4. Wallet card: Navy-to-blue gradient")
print("  5. Buttons: Blue gradient with shadow")
print("  6. Cards: Subtle shadows + hover effect")
print("  7. Bottom nav: Blue active + icon animation")
print("  8. All screens: ELUP navy/blue theme")
print("\nTest: http://127.0.0.1:8000/tenant (Ctrl+F5)")