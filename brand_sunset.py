import shutil, re

print("Switching to Sunset theme...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_sunset')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace :root variables ===
new_root = """:root {
            --bg: #f5f6fa;
            --card-bg: #ffffff;
            --card-border: #dfe6e9;
            --text: #2d3436;
            --text-dim: #636e72;
            --accent: #6c5ce7;
            --accent-glow: rgba(108, 92, 231, 0.3);
            --success: #00b894;
            --danger: #e84393;
            --warning: #fdcb6e;
            --primary: #6c5ce7;
            --secondary: #6c5ce7;
            --gray: #b2bec3;
            --light: #f5f6fa;
            --dark: #2d3436;
        }"""

c = re.sub(r':root\s*\{[^}]*\}', new_root, c, count=1)
print("  Set Sunset color variables.")

# === 2. Replace ALL color values (global) ===
replacements = [
    # Accent — gold → purple
    ('#d4af37', '#6c5ce7'),
    ('rgba(212, 175, 55,', 'rgba(108, 92, 231,'),
    ('#b8941f', '#5849be'),
    ('#c9a227', '#7c6ce0'),
    
    # Success — green → teal
    ('#2ecc71', '#00b894'),
    ('rgba(46, 204, 113,', 'rgba(0, 184, 148,'),
    
    # Danger — red → pink-red
    ('#e74c3c', '#e84393'),
    ('rgba(231, 76, 60,', 'rgba(232, 67, 147,'),
    ('#c0392b', '#d63031'),
    
    # Warning
    ('#f39c12', '#fdcb6e'),
    
    # Text — green-white → dark
    ('#e8f5e9', '#2d3436'),
    
    # Dim text
    ('#7a9b87', '#636e72'),
    ('#5a7a66', '#b2bec3'),
    
    # Borders — dark green → light gray
    ('#1a5e3a', '#dfe6e9'),
]

for old, new in replacements:
    c = c.replace(old, new)

print("  Replaced all accent/text colors.")

# === 3. Body background — dark → light ===
c = c.replace(
    'background: #0a2e1f; margin: 0; padding: 0; color: #2d3436;',
    'background: #f5f6fa; margin: 0; padding: 0; color: #2d3436;'
)

# === 4. Login screen — sunset gradient ===
c = c.replace(
    "background: radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%);",
    "background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 40%, #6c5ce7 100%);"
)

# Login logo — white on gradient
c = c.replace(
    "color: #6c5ce7; text-shadow: 0 0 20px rgba(108, 92, 231, 0.6), 0 0 40px rgba(108, 92, 231, 0.4), 0 0 80px rgba(108, 92, 231, 0.15);",
    "color: #ffffff; text-shadow: 0 2px 15px rgba(0,0,0,0.15);"
)

# Login card — white glass
c = c.replace(
    "background: rgba(15, 61, 42, 0.85); backdrop-filter: blur(20px);",
    "background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px);"
)

c = c.replace(
    "border: 1px solid rgba(108, 92, 231, 0.2); box-shadow: 0 0 60px rgba(108, 92, 231, 0.1), 0 0 40px rgba(108, 92, 231, 0.05), 0 20px 40px rgba(0,0,0,0.5);",
    "border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 20px 60px rgba(0,0,0,0.12), 0 0 40px rgba(255, 107, 107, 0.1);"
)

# Login card heading
c = c.replace(
    ".login-card h2 { text-align: center; color: #2d3436; margin-top: 0; margin-bottom: 20px; font-weight: 600; }",
    ".login-card h2 { text-align: center; color: #2d3436; margin-top: 0; margin-bottom: 20px; font-weight: 700; }"
)

# Login inputs — white
c = c.replace(
    "background: #061d12; color: #2d3436; transition: border-color 0.3s, box-shadow 0.3s;",
    "background: #ffffff; color: #2d3436; transition: border-color 0.3s, box-shadow 0.3s;"
)

c = c.replace(
    ".login-card input::placeholder { color: #b2bec3; }",
    ".login-card input::placeholder { color: #b2bec3; }\n        .login-card select option { background: #ffffff; color: #2d3436; }"
)

# Login button — purple gradient
c = c.replace(
    "background: linear-gradient(135deg, #6c5ce7, #5849be); color: #0a2e1f; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 25px rgba(108, 92, 231, 0.35);",
    "background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 25px rgba(108, 92, 231, 0.35);"
)

# Login links — purple on white
c = c.replace(
    "color:#6c5ce7; text-decoration:none; font-size:0.9em;",
    "color:#6c5ce7; text-decoration:none; font-size:0.9em; font-weight: 600;"
)

# B-BBEE badge — white on gradient
c = c.replace(
    "background:rgba(108,92,231,0.1); color:#6c5ce7; border:1px solid rgba(108,92,231,0.3);",
    "background:rgba(255,255,255,0.15); color:#ffffff; border:1px solid rgba(255,255,255,0.25);"
)

# SERVICES subtitle
c = c.replace(
    "color: #636e72; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px; opacity: 0.8;\">SERVICES",
    "color: rgba(255,255,255,0.8); font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px;\">SERVICES"
)

print("  Built sunset login screen.")

# === 5. Force-change screen — sunset gradient ===
c = c.replace(
    "background: radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%);",
    "background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 40%, #6c5ce7 100%);"
)

# Force change screen inputs — white
c = c.replace(
    "background: #061d12; color: #2d3436; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; }",
    "background: #ffffff; color: #2d3436; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; }"
)

# Force change screen logo
c = c.replace(
    'style="font-size: 1.8em; color: #6c5ce7; text-shadow: 0 0 20px rgba(108,92,231,0.5);">ELUP',
    'style="font-size: 1.8em; color: #ffffff; text-shadow: 0 2px 15px rgba(0,0,0,0.15);">ELUP'
)

print("  Built sunset force-change screen.")

# === 6. Header — white with shadow ===
c = c.replace(
    "background: rgba(10, 46, 31, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid #dfe6e9;",
    "background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(0,0,0,0.05);"
)

# Change password button — purple outline
c = c.replace(
    ".btn-change-pw { background: rgba(108, 92, 231, 0.1); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.3);",
    ".btn-change-pw { background: rgba(108, 92, 231, 0.08); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.2);"
)

# Logout button — pink outline
c = c.replace(
    ".btn-logout { background: rgba(232, 67, 147, 0.15); color: #e84393; border: 1px solid rgba(232, 67, 147, 0.3);",
    ".btn-logout { background: rgba(232, 67, 147, 0.08); color: #e84393; border: 1px solid rgba(232, 67, 147, 0.2);"
)

print("  Built white header with purple/pink accents.")

# === 7. Cards — white with soft shadow ===
c = c.replace(
    "background: #0f3d2a; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(26, 94, 58, 0.4); box-shadow: 0 4px 20px rgba(0,0,0,0.3);",
    "background: #ffffff; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 20px rgba(0,0,0,0.06);"
)

c = c.replace(
    "border-color: rgba(108, 92, 231, 0.3); box-shadow: 0 8px 30px rgba(108, 92, 231, 0.08);",
    "border-color: rgba(108, 92, 231, 0.15); box-shadow: 0 8px 30px rgba(108, 92, 231, 0.08);"
)

# Card headings
c = c.replace(
    ".card h3 { margin: 0 0 15px 0; color: #2d3436; font-size: 1.1em; border-bottom: 1px solid #dfe6e9; padding-bottom: 10px; font-weight: 600; }",
    ".card h3 { margin: 0 0 15px 0; color: #2d3436; font-size: 1.1em; border-bottom: 1px solid #dfe6e9; padding-bottom: 10px; font-weight: 700; }"
)

print("  Built white cards with soft shadows.")

# === 8. Wallet card — sunset gradient ===
c = c.replace(
    "background: linear-gradient(135deg, #0a2e1f, #0f3d2a); border: 1px solid rgba(108, 92, 231, 0.15);",
    "background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #6c5ce7 100%); border: none;"
)

c = c.replace(
    "box-shadow: 0 0 50px rgba(108, 92, 231, 0.08), 0 10px 30px rgba(0,0,0,0.4);",
    "box-shadow: 0 10px 40px rgba(238, 90, 111, 0.3), 0 4px 15px rgba(0,0,0,0.1);"
)

# Wallet balance — white
c = c.replace(
    "color: #6c5ce7; text-shadow: 0 0 30px rgba(108, 92, 231, 0.5), 0 0 60px rgba(108, 92, 231, 0.2);",
    "color: #ffffff; text-shadow: 0 2px 10px rgba(0,0,0,0.1);"
)

# Wallet subtext
c = c.replace(
    ".wallet-sub { font-size: 0.9em; opacity: 0.6; margin-bottom: 25px; color: #636e72; }",
    ".wallet-sub { font-size: 0.9em; opacity: 0.85; margin-bottom: 25px; color: #ffffff; }"
)

c = c.replace(
    ".wallet-card h2 { margin: 0 0 10px 0; font-size: 1.2em; font-weight: 400; color: #636e72; }",
    ".wallet-card h2 { margin: 0 0 10px 0; font-size: 1.2em; font-weight: 400; color: rgba(255,255,255,0.9); }"
)

# Fund button — white on gradient
c = c.replace(
    "background: linear-gradient(135deg, #6c5ce7, #b8941f); color: #0a2e1f; border: none; padding: 15px; width: 100%;",
    "background: #ffffff; color: #6c5ce7; border: none; padding: 15px; width: 100%;"
)

c = c.replace(
    "box-shadow: 0 4px 20px rgba(108, 92, 231, 0.25); transition: all 0.3s;",
    "box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.3s;"
)

print("  Built sunset wallet card.")

# === 9. KPI cards — white ===
c = c.replace(
    ".kpi-card { background: #0f3d2a; border-radius: 12px; padding: 15px; border: 1px solid #dfe6e9; text-align: center; }",
    ".kpi-card { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 10px rgba(0,0,0,0.04); text-align: center; }"
)

c = c.replace(
    ".kpi-card h4 { margin: 0 0 5px 0; color: #636e72; font-size: 0.8em; text-transform: uppercase; }",
    ".kpi-card h4 { margin: 0 0 5px 0; color: #b2bec3; font-size: 0.8em; text-transform: uppercase; }"
)

c = c.replace(
    ".kpi-card .val { font-size: 1.4em; font-weight: bold; color: #2d3436; }",
    ".kpi-card .val { font-size: 1.4em; font-weight: bold; color: #2d3436; }"
)

# Remove glow from KPI values (light theme doesn't need glow)
c = c.replace(
    ".kpi-card.success .val { color: #00b894; text-shadow: 0 0 10px rgba(0, 184, 148, 0.3); }",
    ".kpi-card.success .val { color: #00b894; }"
)

c = c.replace(
    ".kpi-card.danger .val { color: #e84393; text-shadow: 0 0 10px rgba(232, 67, 147, 0.3); }",
    ".kpi-card.danger .val { color: #e84393; }"
)

c = c.replace(
    ".kpi-card.secondary .val { color: #6c5ce7; text-shadow: 0 0 10px rgba(108, 92, 231, 0.3); }",
    ".kpi-card.secondary .val { color: #6c5ce7; }"
)

print("  Built white KPI cards.")

# === 10. Alert banners — light ===
c = c.replace(
    ".alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; background: #0f3d2a; border: 1px solid #dfe6e9; }",
    ".alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; background: #ffffff; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 10px rgba(0,0,0,0.04); }"
)

c = c.replace(
    "background-color: rgba(232, 67, 147, 0.05); color: #e84393; border-left-color: #e84393; border: 1px solid rgba(232, 67, 147, 0.12);",
    "background-color: rgba(232, 67, 147, 0.04); color: #e84393; border-left-color: #e84393; border: 1px solid rgba(232, 67, 147, 0.1);"
)

c = c.replace(
    "background-color: rgba(253, 203, 110, 0.05); color: #f39c12; border-left-color: #f39c12; border: 1px solid rgba(253, 203, 110, 0.12);",
    "background-color: rgba(253, 203, 110, 0.08); color: #d4a017; border-left-color: #fdcb6e; border: 1px solid rgba(253, 203, 110, 0.15);"
)

print("  Built light alert banners.")

# === 11. Transaction items ===
c = c.replace(
    ".txn-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #dfe6e9; font-size: 0.95em; }",
    ".txn-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f2f6; font-size: 0.95em; }"
)

c = c.replace(
    ".txn-date { color: #636e72; font-size: 0.85em; }",
    ".txn-date { color: #b2bec3; font-size: 0.85em; }"
)

# === 12. Bottom nav — white with purple active ===
c = c.replace(
    "background: rgba(10, 46, 31, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(108, 92, 231, 0.1); box-shadow: 0 -4px 30px rgba(0,0,0,0.3);",
    "background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.05); box-shadow: 0 -4px 20px rgba(0,0,0,0.06);"
)

c = c.replace(
    "color: #6c5ce7; font-weight: bold; text-shadow: 0 0 12px rgba(108, 92, 231, 0.5);",
    "color: #6c5ce7; font-weight: bold;"
)

c = c.replace(
    "filter: drop-shadow(0 0 10px rgba(108, 92, 231, 0.5));",
    "filter: none;"
)

c = c.replace(
    ".nav-btn { background: none; border: none; color: #b2bec3;",
    ".nav-btn { background: none; border: none; color: #b2bec3;"
)

print("  Built white bottom navigation.")

# === 13. General inputs — white ===
c = c.replace(
    "input, select { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #061d12; color: #2d3436; }",
    "input, select { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #ffffff; color: #2d3436; }\n        input::placeholder { color: #b2bec3; }\n        select option { background: #ffffff; color: #2d3436; }"
)

c = c.replace(
    "input:focus, select:focus { outline: none; border-color: #6c5ce7; }",
    "input:focus, select:focus { outline: none; border-color: #6c5ce7; box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.1); }"
)

# === 14. General buttons — purple gradient ===
c = c.replace(
    "button { width: 100%; padding: 12px; background: linear-gradient(135deg, #6c5ce7, #5849be); color: #2d3436; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }",
    "button { width: 100%; padding: 12px; background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }\n        button:hover { box-shadow: 0 4px 20px rgba(108,92,231,0.3); transform: translateY(-1px); }"
)

c = c.replace(
    ".btn-paygate { background: linear-gradient(135deg, #0f3d2a, #0a2e1f); color: #6c5ce7; border: 1px solid rgba(108,92,231,0.25); }",
    ".btn-paygate { background: #2d3436; color: #ffffff; border: none; }"
)

print("  Built white inputs and purple buttons.")

# === 15. Utility cards ===
c = c.replace(
    ".utility-card { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: #061d12; border: 1px solid #dfe6e9; }",
    ".utility-card { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: #f8f9fa; border: 1px solid rgba(0,0,0,0.05); }"
)

c = c.replace(
    ".utility-card h4 { margin: 0 0 10px 0; color: #2d3436; font-size: 1.2em;",
    ".utility-card h4 { margin: 0 0 10px 0; color: #2d3436; font-size: 1.2em;"
)

c = c.replace(
    "background: #ffffff; color: #2d3436; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; font-weight: bold; }",
    "background: #ffffff; color: #2d3436; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; font-weight: bold; }"
)

# Utility buttons
c = c.replace(
    ".btn-elec { background: linear-gradient(135deg, #fdcb6e, #b8941f); color: #0a2e1f; }",
    ".btn-elec { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #2d3436; }"
)

c = c.replace(
    ".btn-water-cold { background: linear-gradient(135deg, #00b894, #27ae60); color: #0a2e1f; }",
    ".btn-water-cold { background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; }"
)

c = c.replace(
    ".btn-water-hot { background: linear-gradient(135deg, #e84393, #d63031); color: white;",
    ".btn-water-hot { background: linear-gradient(135deg, #e84393, #d63031); color: #ffffff;"
)

print("  Built light utility cards.")

# === 16. Credit card (emergency fund) ===
c = c.replace(
    ".credit-card { background: #0f3d2a; border: 2px dashed rgba(108, 92, 231, 0.3);",
    ".credit-card { background: #ffffff; border: 2px dashed rgba(108, 92, 231, 0.2);"
)

c = c.replace(
    ".credit-card h3 { color: #6c5ce7;",
    ".credit-card h3 { color: #6c5ce7;"
)

c = c.replace(
    ".credit-card .val { font-size: 1.8em; font-weight: bold; color: #6c5ce7;",
    ".credit-card .val { font-size: 1.8em; font-weight: bold; color: #6c5ce7;"
)

c = c.replace(
    ".credit-card .taps-badge { background: rgba(108, 92, 231, 0.2); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.3);",
    ".credit-card .taps-badge { background: rgba(108, 92, 231, 0.08); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.15);"
)

# === 17. Change password modal — white ===
c = c.replace(
    ".change-pw-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 300; }",
    ".change-pw-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(45, 52, 54, 0.5); backdrop-filter: blur(5px); z-index: 300; }"
)

c = c.replace(
    ".change-pw-content { background: #0f3d2a; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; border: 1px solid rgba(108, 92, 231, 0.15); box-shadow: 0 0 60px rgba(108, 92, 231, 0.06), 0 20px 40px rgba(0,0,0,0.5);",
    ".change-pw-content { background: #ffffff; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 20px 60px rgba(0,0,0,0.15);"
)

c = c.replace(
    ".change-pw-content h2 { color: #2d3436; margin-top: 0; }",
    ".change-pw-content h2 { color: #2d3436; margin-top: 0; }"
)

c = c.replace(
    ".change-pw-content input { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #061d12; color: #2d3436; }",
    ".change-pw-content input { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #ffffff; color: #2d3436; }"
)

c = c.replace(
    ".change-pw-content .btn-submit { background: linear-gradient(135deg, #6c5ce7, #5849be); color: #0a2e1f; box-shadow: 0 4px 15px rgba(108,92,231,0.25); }",
    ".change-pw-content .btn-submit { background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; box-shadow: 0 4px 15px rgba(108,92,231,0.25); }"
)

c = c.replace(
    ".change-pw-content .btn-cancel { background: rgba(139, 148, 158, 0.15); color: #636e72; border: 1px solid #dfe6e9; }",
    ".change-pw-content .btn-cancel { background: #f5f6fa; color: #636e72; border: 1px solid #dfe6e9; }"
)

print("  Built white change password modal.")

# === 18. Token button ===
c = c.replace(
    ".btn-token { background: rgba(108, 92, 231, 0.1); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.25);",
    ".btn-token { background: rgba(108, 92, 231, 0.08); color: #6c5ce7; border: 1px solid rgba(108, 92, 231, 0.15);"
)

# Token link
if 'token-link' in c:
    c = c.replace(
        "color:#6c5ce7;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;",
        "color:#6c5ce7;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;font-weight:600;"
    )

# === 19. Insight card ===
c = c.replace(
    "background: rgba(108, 92, 231, 0.04); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #6c5ce7;",
    "background: rgba(108, 92, 231, 0.03); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #6c5ce7;"
)

c = c.replace(
    ".insight-card h4 { margin: 0 0 5px 0; color: #6c5ce7; font-size: 0.95em; }",
    ".insight-card h4 { margin: 0 0 5px 0; color: #6c5ce7; font-size: 0.95em; font-weight: 600; }"
)

c = c.replace(
    ".insight-card p { margin: 0; font-size: 0.85em; color: #636e72; }",
    ".insight-card p { margin: 0; font-size: 0.85em; color: #636e72; }"
)

# === 20. Home header ===
c = c.replace(
    ".home-header h1 { margin: 0; font-size: 1.8em; color: #2d3436; font-weight: 700; }",
    ".home-header h1 { margin: 0; font-size: 1.8em; color: #2d3436; font-weight: 700; }"
)

c = c.replace(
    ".home-header p { margin: 5px 0 0 0; color: #636e72; font-size: 0.9em; }",
    ".home-header p { margin: 5px 0 0 0; color: #b2bec3; font-size: 0.9em; }"
)

# === 21. Helper text ===
c = c.replace(
    ".helper-text { font-size: 0.85em; color: #636e72; margin-bottom: 8px; text-align: center; }",
    ".helper-text { font-size: 0.85em; color: #b2bec3; margin-bottom: 8px; text-align: center; }"
)

# === 22. PayGate ===
c = c.replace(
    ".paygate-logo { font-weight: 800; color: #6c5ce7; font-size: 1.5em; margin: 10px 0; }",
    ".paygate-logo { font-weight: 800; color: #2d3436; font-size: 1.5em; margin: 10px 0; }"
)

c = c.replace(
    ".payment-logo { background: #061d12; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: #636e72; border: 1px solid #dfe6e9; }",
    ".payment-logo { background: #f8f9fa; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: #636e72; border: 1px solid #dfe6e9; }"
)

# === 23. Smart meter info banner ===
if 'smartMeterInfo' in c:
    c = c.replace(
        'background: rgba(108, 92, 231, 0.04); border-left: 4px solid #6c5ce7;',
        'background: rgba(108, 92, 231, 0.03); border-left: 4px solid #6c5ce7;'
    )

# === 24. Scrollbar — light with purple ===
c = c.replace("::-webkit-scrollbar-track { background: #051910; }", 
              "::-webkit-scrollbar-track { background: #f5f6fa; }")
c = c.replace("::-webkit-scrollbar-thumb { background: #dfe6e9; border-radius: 3px; }",
              "::-webkit-scrollbar-thumb { background: #6c5ce7; border-radius: 3px; }")
c = c.replace("::-webkit-scrollbar-thumb:hover { background: #00b894; }",
              "::-webkit-scrollbar-thumb:hover { background: #5849be; }")

print("  Built light scrollbar.")

# === 25. Replace animation with sunset pulse ===
c = c.replace('@keyframes emeraldGlow', '@keyframes sunsetPulse')
c = c.replace('animation: emeraldGlow 6s ease-in-out infinite;', 'animation: sunsetPulse 10s ease-in-out infinite;')

# Update animation colors — warm sunset particles
c = c.replace(
    "background: radial-gradient(ellipse at 30% 20%, rgba(108, 92, 231, 0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(108, 92, 231, 0.04) 0%, transparent 50%);",
    "background: radial-gradient(ellipse at 30% 20%, rgba(255, 107, 107, 0.1) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(108, 92, 231, 0.08) 0%, transparent 50%);"
)

# Update keyframes
c = c.replace(
    "@keyframes sunsetPulse { 0% { opacity: 0.3; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.05); } 100% { opacity: 0.3; transform: scale(1); } }",
    "@keyframes sunsetPulse { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }"
)

print("  Built sunset pulse animation.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print("SUNSET THEME COMPLETE!")
print(f"{'='*55}")
print("""
Color scheme:
  Login bg:     Orange → magenta → purple gradient
  App bg:       #f5f6fa (light gray)
  Cards:        #ffffff (white with soft shadow)
  Accent:       #6c5ce7 (purple)
  Success:      #00b894 (teal)
  Danger:       #e84393 (pink-red)
  Warning:      #fdcb6e (orange)
  Text:         #2d3436 (dark)
  
Wallet card:   Sunset gradient (orange → purple)
  Balance:      White on gradient
  Fund button:  White with purple text

Buttons:
  Primary:      Purple gradient (#6c5ce7 → #5849be)
  Electricity:  Orange gradient (#fdcb6e → #f39c12)
  Cold Water:   Purple gradient (#6c5ce7 → #5849be)
  Hot Water:    Pink-red gradient (#e84393 → #d63031)
  
Login screen:
  Background:   linear-gradient(135deg, #ff6b6b, #ee5a6f, #6c5ce7)
  ELUP logo:    White with subtle shadow
  Card:         White frosted glass
  Button:       Purple gradient, white text
  B-BBEE:       White badge on gradient
  
Animation:     Subtle sunset pulse (warm particles)
  
Test: http://127.0.0.1:8000/tenant (Ctrl+F5)
""")