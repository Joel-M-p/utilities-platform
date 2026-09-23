import shutil

print("Building Dark Premium theme for ELUP...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_dark')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace ALL CSS with dark premium theme ===
import re

# Replace the :root variables
old_root_pattern = r':root\s*\{[^}]*\}'
new_root = """:root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --card-border: #30363d;
            --text: #e6edf3;
            --text-dim: #8b949e;
            --accent: #00d4ff;
            --accent-glow: rgba(0, 212, 255, 0.3);
            --success: #00ff88;
            --danger: #ff4757;
            --warning: #ffa502;
            --primary: #0d1117;
            --secondary: #00d4ff;
            --gray: #8b949e;
            --light: #161b22;
            --dark: #0d1117;
        }"""

c = re.sub(old_root_pattern, new_root, c, count=1)
print("  Set dark premium color variables.")

# === 2. Body background ===
c = c.replace(
    'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg); margin: 0; padding: 0; color: #1c1c1e; -webkit-font-smoothing: antialiased; padding-bottom: 70px; }',
    'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0d1117; margin: 0; padding: 0; color: #e6edf3; -webkit-font-smoothing: antialiased; padding-bottom: 70px; }'
)
print("  Set dark body background.")

# === 3. Login screen — dark gradient with glow ===
c = c.replace(
    '.login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #0a2540 0%, #1565c0 50%, #1976d2 100%);',
    '.login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: radial-gradient(circle at 50% 30%, #161b22 0%, #0d1117 100%);'
)

# Login logo — neon glow
c = c.replace(
    '.login-logo { font-size: 2.8em; font-weight: 900; margin-bottom: 5px; letter-spacing: 4px; text-align: center; color: white; }',
    '.login-logo { font-size: 3em; font-weight: 900; margin-bottom: 5px; letter-spacing: 6px; text-align: center; color: #00d4ff; text-shadow: 0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(0, 212, 255, 0.3); }'
)

# Login card — glassmorphism
c = c.replace(
    '.login-card { background: white; padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }',
    '.login-card { background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; border: 1px solid #30363d; box-shadow: 0 0 60px rgba(0, 212, 255, 0.1), 0 20px 40px rgba(0,0,0,0.5); }'
)

# Login card heading
c = c.replace(
    '.login-card h2 { text-align: center; color: var(--dark); margin-top: 0; margin-bottom: 20px; }',
    '.login-card h2 { text-align: center; color: #e6edf3; margin-top: 0; margin-bottom: 20px; font-weight: 600; }'
)

# Login card inputs — dark style
c = c.replace(
    '.login-card input, .login-card select { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; }',
    '.login-card input, .login-card select { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #0d1117; color: #e6edf3; transition: border-color 0.3s, box-shadow 0.3s; }\n        .login-card input:focus, .login-card select:focus { outline: none; border-color: #00d4ff; box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15); }\n        .login-card input::placeholder { color: #6e7681; }\n        .login-card select option { background: #161b22; color: #e6edf3; }'
)

# Login button — cyan gradient with glow
c = c.replace(
    '.login-card button { width: 100%; padding: 15px; background: linear-gradient(135deg, #1976d2, #1565c0); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(25,118,210,0.3); transition: all 0.3s; }\n        .login-card button:hover { box-shadow: 0 6px 20px rgba(25,118,210,0.5); transform: translateY(-1px); }',
    '.login-card button { width: 100%; padding: 15px; background: linear-gradient(135deg, #00d4ff, #0099cc); color: #0d1117; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3); transition: all 0.3s; }\n        .login-card button:hover { box-shadow: 0 6px 30px rgba(0, 212, 255, 0.5); transform: translateY(-2px); }\n        .login-card button:active { transform: translateY(0); }'
)

# Login error
c = c.replace(
    '.login-error { color: var(--danger); text-align: center; margin-top: 15px; font-size: 0.9em; display: none; }',
    '.login-error { color: #ff4757; text-align: center; margin-top: 15px; font-size: 0.9em; display: none; }'
)

# Forgot password link
if "Forgot Password" in c:
    c = c.replace(
        "color:var(--secondary); text-decoration:none; font-size:0.9em;",
        "color:#00d4ff; text-decoration:none; font-size:0.9em;"
    )

print("  Built dark premium login screen with glassmorphism.")

# === 4. Force-change screen — same dark theme ===
c = c.replace(
    '.force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #0a2540, #1565c0);',
    '.force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: radial-gradient(circle at 50% 30%, #161b22 0%, #0d1117 100%);'
)

# Force change screen inputs
c = c.replace(
    '.force-change-screen .login-card input { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; }',
    '.force-change-screen .login-card input { width: 100%; padding: 15px; margin-bottom: 15px; box-sizing: border-box; background: #0d1117; color: #e6edf3; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; }\n        .force-change-screen .login-card input:focus { outline: none; border-color: #00d4ff; box-shadow: 0 0 0 3px rgba(0,212,255,0.15); }'
)

print("  Built dark premium force-change screen.")

# === 5. App header — dark with cyan accent ===
c = c.replace(
    '.app-header { background: linear-gradient(135deg, #0a2540, #1565c0);',
    '.app-header { background: rgba(13, 17, 23, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid #30363d;'
)

c = c.replace(
    '<span id="appHeaderText">ELUP Utilities</span>',
    '<span id="appHeaderText" style="font-weight: 700; letter-spacing: 1px;">ELUP</span>'
)

# Change password button
if 'btn-change-pw' in c:
    c = c.replace(
        '.btn-change-pw { background-color: #2980b9; color: white; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 0.9em; margin-right: 5px; }',
        '.btn-change-pw { background: rgba(0, 212, 255, 0.1); color: #00d4ff; border: 1px solid rgba(0, 212, 255, 0.3); padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 0.9em; margin-right: 5px; transition: all 0.3s; }\n        .btn-change-pw:hover { background: rgba(0, 212, 255, 0.2); border-color: #00d4ff; }'
    )

# Logout button
c = c.replace(
    '.btn-logout { background: var(--danger); color: white; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 0.9em; }',
    '.btn-logout { background: rgba(255, 71, 87, 0.15); color: #ff4757; border: 1px solid rgba(255, 71, 87, 0.3); padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 0.9em; transition: all 0.3s; }\n        .btn-logout:hover { background: rgba(255, 71, 87, 0.25); }'
)

print("  Built dark premium header.")

# === 6. Screens — dark background ===
c = c.replace(
    '.screen { display: none; padding: 15px; max-width: 500px; margin: 0 auto; }',
    '.screen { display: none; padding: 15px; max-width: 500px; margin: 0 auto; }'
)

# === 7. Cards — dark glass ===
c = c.replace(
    '.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(10,37,64,0.08); transition: box-shadow 0.3s; }\n        .card:hover { box-shadow: 0 8px 25px rgba(10,37,64,0.12); }',
    '.card { background: #161b22; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #30363d; box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: border-color 0.3s, box-shadow 0.3s; }\n        .card:hover { border-color: rgba(0, 212, 255, 0.3); box-shadow: 0 8px 30px rgba(0, 212, 255, 0.08); }'
)

c = c.replace(
    '.card h3 { margin: 0 0 15px 0; color: var(--dark); font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 10px; }',
    '.card h3 { margin: 0 0 15px 0; color: #e6edf3; font-size: 1.1em; border-bottom: 1px solid #30363d; padding-bottom: 10px; font-weight: 600; }'
)

print("  Built dark glass cards.")

# === 8. Wallet card — dark with cyan glow ===
c = c.replace(
    '.wallet-card { background: linear-gradient(135deg, #0a2540, #1976d2); color: white; padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.15); }',
    '.wallet-card { background: linear-gradient(135deg, #0d1117, #161b22); border: 1px solid rgba(0, 212, 255, 0.2); color: #e6edf3; padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 20px; box-shadow: 0 0 40px rgba(0, 212, 255, 0.08), 0 10px 30px rgba(0,0,0,0.4); }'
)

c = c.replace(
    '.wallet-card h2 { margin: 0 0 10px 0; font-size: 1.2em; font-weight: 400; }',
    '.wallet-card h2 { margin: 0 0 10px 0; font-size: 1.2em; font-weight: 400; color: #8b949e; }'
)

c = c.replace(
    '.wallet-balance { font-size: 3em; font-weight: 800; margin-bottom: 5px; }',
    '.wallet-balance { font-size: 3em; font-weight: 800; margin-bottom: 5px; color: #00d4ff; text-shadow: 0 0 30px rgba(0, 212, 255, 0.3); }'
)

c = c.replace(
    '.wallet-sub { font-size: 0.9em; opacity: 0.8; margin-bottom: 25px; }',
    '.wallet-sub { font-size: 0.9em; opacity: 0.6; margin-bottom: 25px; color: #8b949e; }'
)

# Fund button — cyan gradient
c = c.replace(
    '.btn-fund { background: white; color: #0a2540; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }',
    '.btn-fund { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #0d1117; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 20px rgba(0, 212, 255, 0.25); transition: all 0.3s; }\n        .btn-fund:hover { box-shadow: 0 6px 30px rgba(0, 212, 255, 0.4); transform: translateY(-2px); }'
)

print("  Built dark premium wallet card with cyan glow.")

# === 9. Credit card ===
c = c.replace(
    '.credit-card { background: white; border: 2px dashed var(--warning); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }',
    '.credit-card { background: #161b22; border: 2px dashed rgba(255, 165, 2, 0.4); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }'
)

c = c.replace(
    '.credit-card h3 { color: var(--warning); border: none; margin-bottom: 5px; }',
    '.credit-card h3 { color: #ffa502; border: none; margin-bottom: 5px; }'
)

c = c.replace(
    '.credit-card .val { font-size: 1.8em; font-weight: bold; color: var(--warning); margin-bottom: 5px; }',
    '.credit-card .val { font-size: 1.8em; font-weight: bold; color: #ffa502; margin-bottom: 5px; }'
)

c = c.replace(
    ".credit-card .taps-badge { background: var(--warning); color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }",
    ".credit-card .taps-badge { background: rgba(255, 165, 2, 0.2); color: #ffa502; border: 1px solid rgba(255, 165, 2, 0.3); padding: 3px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }"
)

# === 10. KPI cards ===
c = c.replace(
    '.kpi-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 15px rgba(10,37,64,0.08); text-align: center; }',
    '.kpi-card { background: #161b22; border-radius: 12px; padding: 15px; border: 1px solid #30363d; text-align: center; }'
)

c = c.replace(
    '.kpi-card h4 { margin: 0 0 5px 0; color: var(--gray); font-size: 0.8em; text-transform: uppercase; }',
    '.kpi-card h4 { margin: 0 0 5px 0; color: #8b949e; font-size: 0.8em; text-transform: uppercase; }'
)

c = c.replace(
    '.kpi-card .val { font-size: 1.4em; font-weight: bold; color: var(--dark); }',
    '.kpi-card .val { font-size: 1.4em; font-weight: bold; color: #e6edf3; }'
)

c = c.replace(
    '.kpi-card.success .val { color: var(--success); }',
    '.kpi-card.success .val { color: #00ff88; }'
)

c = c.replace(
    '.kpi-card.danger .val { color: var(--danger); }',
    '.kpi-card.danger .val { color: #ff4757; }'
)

c = c.replace(
    '.kpi-card.warning .val { color: var(--warning); }',
    '.kpi-card.warning .val { color: #ffa502; }'
)

c = c.replace(
    '.kpi-card.secondary .val { color: var(--secondary); }',
    '.kpi-card.secondary .val { color: #00d4ff; }'
)

print("  Built dark KPI cards.")

# === 11. Alert banners — dark ===
c = c.replace(
    '.alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; box-shadow: 0 4px 15px rgba(10,37,64,0.08); }',
    '.alert-banner { padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid; text-align: center; background: #161b22; border: 1px solid #30363d; }'
)

c = c.replace(
    '.alert-danger { background-color: #ffebee; color: #c0392b; border-left-color: #c0392b; }',
    '.alert-danger { background-color: rgba(255, 71, 87, 0.08); color: #ff4757; border-left-color: #ff4757; border: 1px solid rgba(255, 71, 87, 0.2); }'
)

c = c.replace(
    '.alert-danger h3 { color: #c0392b; }',
    '.alert-danger h3 { color: #ff4757; }'
)

c = c.replace(
    '.alert-danger button { background: #c0392b; }',
    '.alert-danger button { background: rgba(255, 71, 87, 0.2); border: 1px solid rgba(255, 71, 87, 0.4); color: #ff4757; }'
)

c = c.replace(
    '.alert-warning { background-color: #fff3cd; color: #856404; border-left-color: #f39c12; }',
    '.alert-warning { background-color: rgba(255, 165, 2, 0.08); color: #ffa502; border-left-color: #ffa502; border: 1px solid rgba(255, 165, 2, 0.2); }'
)

c = c.replace(
    '.alert-warning h3 { color: #856404; }',
    '.alert-warning h3 { color: #ffa502; }'
)

c = c.replace(
    '.alert-warning button { background: #f39c12; }',
    '.alert-warning button { background: rgba(255, 165, 2, 0.2); border: 1px solid rgba(255, 165, 2, 0.4); color: #ffa502; }'
)

print("  Built dark alert banners.")

# === 12. Transaction items ===
c = c.replace(
    '.txn-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f1f1; font-size: 0.95em; }',
    '.txn-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; font-size: 0.95em; }'
)

c = c.replace(
    '.txn-date { color: var(--gray); font-size: 0.85em; }',
    '.txn-date { color: #8b949e; font-size: 0.85em; }'
)

c = c.replace(
    '.text-success { color: var(--success); }',
    '.text-success { color: #00ff88; }'
)

c = c.replace(
    '.text-danger { color: var(--danger); }',
    '.text-danger { color: #ff4757; }'
)

print("  Built dark transaction items.")

# === 13. Utility cards (buy electricity/water) ===
c = c.replace(
    '.utility-card { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: #f8f9fa; }',
    '.utility-card { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: #0d1117; border: 1px solid #30363d; }'
)

c = c.replace(
    '.utility-card h4 { margin: 0 0 10px 0; color: var(--dark); font-size: 1.2em; display: flex; align-items: center; gap: 8px; }',
    '.utility-card h4 { margin: 0 0 10px 0; color: #e6edf3; font-size: 1.2em; display: flex; align-items: center; gap: 8px; }'
)

c = c.replace(
    '.utility-card input { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; font-weight: bold; }',
    '.utility-card input { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; font-weight: bold; background: #161b22; color: #e6edf3; }\n        .utility-card input:focus { outline: none; border-color: #00d4ff; }'
)

# Buy buttons
c = c.replace(
    '.btn-buy { width: 100%; padding: 12px; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }',
    '.btn-buy { width: 100%; padding: 12px; color: #0d1117; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }\n        .btn-buy:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }'
)

c = c.replace(
    '.btn-elec { background: var(--warning); }',
    '.btn-elec { background: linear-gradient(135deg, #ffa502, #ff6b00); color: #0d1117; }'
)

c = c.replace(
    '.btn-water-cold { background: var(--secondary); }',
    '.btn-water-cold { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #0d1117; }'
)

c = c.replace(
    '.btn-water-hot { background: #e74c3c; }',
    '.btn-water-hot { background: linear-gradient(135deg, #ff4757, #c62828); color: white; }'
)

print("  Built dark utility cards.")

# === 14. Bottom navigation — dark with cyan active ===
c = c.replace(
    '.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: none; box-shadow: 0 -4px 20px rgba(0,0,0,0.08);',
    '.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(13, 17, 23, 0.95); backdrop-filter: blur(10px); border-top: 1px solid #30363d; box-shadow: 0 -4px 30px rgba(0,0,0,0.3);'
)

c = c.replace(
    '.nav-btn { background: none; border: none; color: #607d8b;',
    '.nav-btn { background: none; border: none; color: #6e7681;'
)

c = c.replace(
    '.nav-btn.active { color: #1976d2; font-weight: bold; }',
    '.nav-btn.active { color: #00d4ff; font-weight: bold; text-shadow: 0 0 10px rgba(0, 212, 255, 0.3); }'
)

c = c.replace(
    '.nav-icon { font-size: 1.5em; margin-bottom: 3px; transition: transform 0.2s; }\n        .nav-btn.active .nav-icon { transform: scale(1.15); }',
    '.nav-icon { font-size: 1.5em; margin-bottom: 3px; transition: transform 0.2s; }\n        .nav-btn.active .nav-icon { transform: scale(1.2); filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.4)); }'
)

print("  Built dark bottom navigation with cyan glow.")

# === 15. Token button ===
c = c.replace(
    '.btn-token { background: var(--secondary); padding: 5px 10px; font-size: 0.75em; width: auto; }',
    '.btn-token { background: rgba(0, 212, 255, 0.15); color: #00d4ff; border: 1px solid rgba(0, 212, 255, 0.3); padding: 5px 10px; font-size: 0.75em; width: auto; border-radius: 4px; cursor: pointer; }\n        .btn-token:hover { background: rgba(0, 212, 255, 0.25); }'
)

# Token link (from utilities fix)
if 'token-link' in c:
    c = c.replace(
        "color:#3498db;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;",
        "color:#00d4ff;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;"
    )

print("  Built dark token buttons.")

# === 16. Change password modal — dark ===
c = c.replace(
    '.change-pw-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 300; }',
    '.change-pw-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 300; }'
)

c = c.replace(
    '.change-pw-content { background: white; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }',
    '.change-pw-content { background: #161b22; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; border: 1px solid #30363d; box-shadow: 0 0 60px rgba(0, 212, 255, 0.1), 0 20px 40px rgba(0,0,0,0.5); }'
)

c = c.replace(
    '.change-pw-content h2 { color: #2c3e50; margin-top: 0; }',
    '.change-pw-content h2 { color: #e6edf3; margin-top: 0; }'
)

c = c.replace(
    '.change-pw-content input { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; }',
    '.change-pw-content input { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #0d1117; color: #e6edf3; }\n        .change-pw-content input:focus { outline: none; border-color: #00d4ff; box-shadow: 0 0 0 3px rgba(0,212,255,0.15); }'
)

c = c.replace(
    '.change-pw-content button { width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-bottom: 10px; }',
    '.change-pw-content button { width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-bottom: 10px; transition: all 0.3s; }'
)

c = c.replace(
    ".change-pw-content .btn-submit { background: var(--secondary); color: white; }",
    ".change-pw-content .btn-submit { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #0d1117; box-shadow: 0 4px 15px rgba(0,212,255,0.25); }"
)

c = c.replace(
    ".change-pw-content .btn-cancel { background: var(--gray); color: white; }",
    ".change-pw-content .btn-cancel { background: rgba(139, 148, 158, 0.15); color: #8b949e; border: 1px solid #30363d; }"
)

print("  Built dark change password modal.")

# === 17. Helper text and other text elements ===
c = c.replace(
    '.helper-text { font-size: 0.85em; color: var(--gray); margin-bottom: 8px; text-align: center; }',
    '.helper-text { font-size: 0.85em; color: #6e7681; margin-bottom: 8px; text-align: center; }'
)

# === 18. Home header ===
c = c.replace(
    '.home-header h1 { margin: 0; font-size: 1.8em; color: var(--dark); }',
    '.home-header h1 { margin: 0; font-size: 1.8em; color: #e6edf3; font-weight: 700; }'
)

c = c.replace(
    '.home-header p { margin: 5px 0 0 0; color: var(--gray); font-size: 0.9em; }',
    '.home-header p { margin: 5px 0 0 0; color: #6e7681; font-size: 0.9em; }'
)

# === 19. PayGate section ===
c = c.replace(
    '.paygate-logo { font-weight: 800; color: #003366; font-size: 1.5em; margin: 10px 0; }',
    '.paygate-logo { font-weight: 800; color: #00d4ff; font-size: 1.5em; margin: 10px 0; }'
)

c = c.replace(
    '.payment-logo { background: #f8f9fa; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: var(--gray); border: 1px solid #ddd; }',
    '.payment-logo { background: #0d1117; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: #8b949e; border: 1px solid #30363d; }'
)

# General inputs
c = c.replace(
    'input, select { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; }',
    'input, select { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #0d1117; color: #e6edf3; }\n        input:focus, select:focus { outline: none; border-color: #00d4ff; }\n        input::placeholder { color: #6e7681; }\n        select option { background: #161b22; color: #e6edf3; }'
)

# General buttons
c = c.replace(
    'button { width: 100%; padding: 12px; background: var(--secondary); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }',
    'button { width: 100%; padding: 12px; background: linear-gradient(135deg, #00d4ff, #0099cc); color: #0d1117; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }\n        button:hover { box-shadow: 0 4px 20px rgba(0,212,255,0.3); transform: translateY(-1px); }'
)

# PayGate button
c = c.replace(
    '.btn-paygate { background: #003366; }',
    '.btn-paygate { background: linear-gradient(135deg, #0d1117, #161b22); color: #00d4ff; border: 1px solid rgba(0,212,255,0.3); }'
)

print("  Built dark forms and buttons.")

# === 20. Summary chart (pie chart legend) ===
c = c.replace(
    '.legend-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }',
    '.legend-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px currentColor; }'
)

# === 21. Insight card ===
c = c.replace(
    '.insight-card { background: #e8f4f8; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid var(--secondary); }',
    '.insight-card { background: rgba(0, 212, 255, 0.05); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #00d4ff; }'
)

c = c.replace(
    '.insight-card h4 { margin: 0 0 5px 0; color: var(--dark); font-size: 0.95em; }',
    '.insight-card h4 { margin: 0 0 5px 0; color: #00d4ff; font-size: 0.95em; }'
)

c = c.replace(
    '.insight-card p { margin: 0; font-size: 0.85em; color: var(--gray); }',
    '.insight-card p { margin: 0; font-size: 0.85em; color: #8b949e; }'
)

print("  Built dark insight cards.")

# === 22. Smart meter info banner ===
if 'smartMeterInfo' in c:
    c = c.replace(
        'background: #e8f4f8; border-left: 4px solid var(--secondary);',
        'background: rgba(0, 212, 255, 0.05); border-left: 4px solid #00d4ff;'
    )
    c = c.replace(
        'color: var(--dark);',
        'color: #e6edf3;'
    )

# === 23. Update B-BBEE badge styling ===
if 'Level 1 B-BBEE' in c:
    c = c.replace(
        'background:rgba(255,255,255,0.15); color:white;',
        'background:rgba(0,212,255,0.1); color:#00d4ff; border:1px solid rgba(0,212,255,0.2);'
    )

# === 24. Update forgot password subtitle ===
c = c.replace(
    "color: white; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px; opacity: 0.8;\">SERVICES",
    "color: #8b949e; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px; opacity: 0.8;\">SERVICES"
)

# === 25. Force change screen logo text ===
c = c.replace(
    'style="font-size: 1.5em; color: white;">ELUP',
    'style="font-size: 1.8em; color: #00d4ff; text-shadow: 0 0 20px rgba(0,212,255,0.4);">ELUP'
)

# === 26. Scrollbar styling ===
if 'scrollbar' not in c:
    scrollbar_css = """
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #00d4ff; }
    """
    c = c.replace('<style>', '<style>\n' + scrollbar_css, 1)

print("  Built custom scrollbar.")

# === 27. Update demo banner if exists ===
if 'demo-banner' in c:
    c = c.replace(
        '.demo-banner { background: linear-gradient(135deg, #2c3e50, #3498db);',
        '.demo-banner { background: linear-gradient(135deg, #0d1117, #161b22); border: 1px solid rgba(0,212,255,0.2);'
    )

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print("DARK PREMIUM THEME COMPLETE!")
print(f"{'='*55}")
print("""
What you'll see:
  Login:  Deep charcoal background, ELUP in neon cyan
          Glass card with blur, cyan gradient button
          B-BBEE badge in cyan
          
  Header: Dark with blur, ELUP branding
          Cyan "Change Password" button (outline)
          Red "Logout" button (outline)
          
  Cards:  Dark (#161b22) with subtle borders
          Hover: cyan border glow
          
  Wallet: Dark with cyan balance number
          Cyan glow on the amount
          Cyan gradient "Fund" button
          
  Nav:    Dark with blur
          Active items: cyan with glow
          Icons scale up when active
          
  Inputs: Dark background, cyan focus glow
  Buttons: Cyan gradient with shadow
  Text:   Soft white on dark background
  Scrollbar: Dark with cyan thumb
  
Test: http://127.0.0.1:8000/tenant (Ctrl+F5)
""")