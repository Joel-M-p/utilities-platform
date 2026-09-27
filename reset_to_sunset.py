import shutil, os, re

print("RESETTING to clean state and applying Sunset theme...")

# === STEP 1: Restore from clean backup (before any branding) ===
backups = ['tenant_portal.html.bak_brand', 'tenant_portal.html.bak_demo']
restored = False

for bak in backups:
    if os.path.exists(bak):
        shutil.copy(bak, 'tenant_portal.html')
        print("  Restored from: " + bak)
        restored = True
        break

if not restored:
    print("  No clean backup found. Working with current file.")
    print("  Will do comprehensive color replacement.")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === STEP 2: Replace :root variables ===
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
print("  Set Sunset :root variables.")

# === STEP 3: COMPREHENSIVE color replacement ===
# Map EVERY possible color from EVERY theme to Sunset equivalent
color_map = {
    # === DARK BACKGROUNDS → LIGHT ===
    '#0d1117': '#f5f6fa', '#0a2540': '#f5f6fa', '#001428': '#f5f6fa',
    '#0a2e1f': '#f5f6fa', '#2c3e50': '#f5f6fa', '#051910': '#f5f6fa',
    '#161b22': '#ffffff', '#001f3f': '#ffffff', '#0f3d2a': '#ffffff',
    '#000a14': '#ffffff', '#061d12': '#ffffff',
    '#30363d': '#dfe6e9', '#003d5c': '#dfe6e9', '#1a5e3a': '#dfe6e9',
    '#ecf0f1': '#f5f6fa', '#f4f7f6': '#f5f6fa',
    '#1c1c1e': '#2d3436',
    
    # === ACCENT → PURPLE ===
    '#00d4ff': '#6c5ce7', '#00d4d4': '#6c5ce7', '#d4af37': '#6c5ce7',
    '#3498db': '#6c5ce7', '#1976d2': '#6c5ce7', '#1565c0': '#6c5ce7',
    '#0099cc': '#5849be', '#008080': '#5849be', '#b8941f': '#5849be',
    '#c9a227': '#7c6ce0', '#00b3b3': '#7c6ce0',
    
    # === SUCCESS → TEAL ===
    '#00ff88': '#00b894', '#00ff9f': '#00b894', '#2ecc71': '#00b894', '#27ae60': '#00b894',
    
    # === DANGER → PINK-RED ===
    '#ff4757': '#e84393', '#ff6b6b': '#e84393', '#e74c3c': '#e84393', '#c0392b': '#d63031',
    
    # === WARNING ===
    '#ffa502': '#fdcb6e', '#ff9502': '#fdcb6e', '#f39c12': '#fdcb6e',
    '#fdcb6e': '#fdcb6e',  # Already correct
    
    # === TEXT → DARK ===
    '#e6edf3': '#2d3436', '#e0f7fa': '#2d3436', '#e8f5e9': '#2d3436',
    
    # === DIM TEXT → GRAY ===
    '#8b949e': '#636e72', '#6e7681': '#b2bec3', '#5c7a89': '#636e72',
    '#4a6275': '#b2bec3', '#7a9b87': '#636e72', '#5a7a66': '#b2bec3',
    '#7f8c8d': '#636e72', '#607d8b': '#636e72',
    
    # === OTHER ===
    '#f8f9fa': '#f8f9fa', '#ffffff': '#ffffff', '#fff': '#ffffff',
    '#eee': '#f1f2f6', '#f1f1f1': '#f1f2f6', '#ccc': '#dfe6e9',
    '#ddd': '#dfe6e9', '#aaa': '#b2bec3',
    '#003366': '#2d3436',
}

for old, new in color_map.items():
    c = c.replace(old, new)

print("  Replaced ALL colors from ALL previous themes.")

# === STEP 4: Replace rgba values ===
rgba_map = {
    'rgba(0, 212, 255,': 'rgba(108, 92, 231,',
    'rgba(0, 212, 212,': 'rgba(108, 92, 231,',
    'rgba(212, 175, 55,': 'rgba(108, 92, 231,',
    'rgba(52, 152, 219,': 'rgba(108, 92, 231,',
    'rgba(25, 118, 210,': 'rgba(108, 92, 231,',
    'rgba(0, 255, 136,': 'rgba(0, 184, 148,',
    'rgba(0, 255, 159,': 'rgba(0, 184, 148,',
    'rgba(46, 204, 113,': 'rgba(0, 184, 148,',
    'rgba(255, 71, 87,': 'rgba(232, 67, 147,',
    'rgba(255, 107, 107,': 'rgba(232, 67, 147,',
    'rgba(231, 76, 60,': 'rgba(232, 67, 147,',
    'rgba(44, 62, 80,': 'rgba(45, 52, 54,',
    'rgba(10, 37, 64,': 'rgba(0, 0, 0,',
    'rgba(10, 46, 31,': 'rgba(255, 255, 255,',
    'rgba(0, 20, 40,': 'rgba(255, 255, 255,',
    'rgba(15, 61, 42,': 'rgba(255, 255, 255,',
    'rgba(13, 17, 23,': 'rgba(255, 255, 255,',
    'rgba(22, 27, 34,': 'rgba(255, 255, 255,',
    'rgba(48, 54, 61,': 'rgba(223, 230, 233,',
}

for old, new in rgba_map.items():
    c = c.replace(old, new)

print("  Replaced ALL rgba colors.")

# === STEP 5: Fix specific CSS rules for gradients ===

# Body background
c = c.replace('background-color: #f5f6fa;', 'background: #f5f6fa;')
c = c.replace('background: #f5f6fa; margin: 0; padding: 0; color: #2d3436;', 
              'background: #f5f6fa; margin: 0; padding: 0; color: #2d3436;')

# Login screen — sunset gradient
c = re.sub(
    r'\.login-screen\s*\{[^}]*background:[^;]*;',
    '.login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 40%, #6c5ce7 100%);',
    c
)

# Login logo — white
c = re.sub(
    r'\.login-logo\s*\{[^}]*\}',
    '.login-logo { font-size: 3em; font-weight: 900; margin-bottom: 5px; letter-spacing: 6px; text-align: center; color: #ffffff; text-shadow: 0 2px 15px rgba(0,0,0,0.15); }',
    c
)

# Login card — white glass
c = re.sub(
    r'\.login-card\s*\{[^}]*\}',
    '.login-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 20px 60px rgba(0,0,0,0.12), 0 0 40px rgba(255, 107, 107, 0.1); }',
    c
)

# Login card h2
c = re.sub(
    r'\.login-card h2\s*\{[^}]*\}',
    '.login-card h2 { text-align: center; color: #2d3436; margin-top: 0; margin-bottom: 20px; font-weight: 700; }',
    c
)

# Login inputs
c = re.sub(
    r'\.login-card input, \.login-card select\s*\{[^}]*\}',
    '.login-card input, .login-card select { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #ffffff; color: #2d3436; transition: border-color 0.3s, box-shadow 0.3s; }',
    c
)

# Login input focus
if '.login-card input:focus' not in c:
    c = c.replace('.login-card input::placeholder', 
        '.login-card input:focus, .login-card select:focus { outline: none; border-color: #6c5ce7; box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.1); }\n        .login-card input::placeholder')

# Login button — purple gradient
c = re.sub(
    r'\.login-card button\s*\{[^}]*\}',
    '.login-card button { width: 100%; padding: 15px; background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 25px rgba(108, 92, 231, 0.35); transition: all 0.3s; }',
    c
)

# Login button hover
c = re.sub(
    r'\.login-card button:hover\s*\{[^}]*\}',
    '.login-card button:hover { box-shadow: 0 6px 30px rgba(108, 92, 231, 0.5); transform: translateY(-2px); }',
    c
)

print("  Fixed login screen CSS.")

# Header — white
c = re.sub(
    r'\.app-header\s*\{[^}]*\}',
    '.app-header { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); color: #2d3436; padding: 15px; text-align: center; font-size: 1.1em; font-weight: bold; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 10px rgba(0,0,0,0.03); display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; }',
    c
)

# Cards — white
c = re.sub(
    r'\.card\s*\{[^}]*\}',
    '.card { background: #ffffff; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 20px rgba(0,0,0,0.06); transition: border-color 0.3s, box-shadow 0.3s; }',
    c
)

c = re.sub(
    r'\.card:hover\s*\{[^}]*\}',
    '.card:hover { border-color: rgba(108, 92, 231, 0.15); box-shadow: 0 8px 30px rgba(108, 92, 231, 0.08); }',
    c
)

c = re.sub(
    r'\.card h3\s*\{[^}]*\}',
    '.card h3 { margin: 0 0 15px 0; color: #2d3436; font-size: 1.1em; border-bottom: 1px solid #dfe6e9; padding-bottom: 10px; font-weight: 700; }',
    c
)

print("  Fixed header and cards CSS.")

# Wallet card — sunset gradient
c = re.sub(
    r'\.wallet-card\s*\{[^}]*\}',
    '.wallet-card { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #6c5ce7 100%); color: #ffffff; padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(238, 90, 111, 0.3), 0 4px 15px rgba(0,0,0,0.1); }',
    c
)

c = re.sub(
    r'\.wallet-card h2\s*\{[^}]*\}',
    '.wallet-card h2 { margin: 0 0 10px 0; font-size: 1.2em; font-weight: 400; color: rgba(255,255,255,0.9); }',
    c
)

c = re.sub(
    r'\.wallet-balance\s*\{[^}]*\}',
    '.wallet-balance { font-size: 3em; font-weight: 800; margin-bottom: 5px; color: #ffffff; text-shadow: 0 2px 10px rgba(0,0,0,0.1); }',
    c
)

c = re.sub(
    r'\.wallet-sub\s*\{[^}]*\}',
    '.wallet-sub { font-size: 0.9em; opacity: 0.85; margin-bottom: 25px; color: #ffffff; }',
    c
)

c = re.sub(
    r'\.btn-fund\s*\{[^}]*\}',
    '.btn-fund { background: #ffffff; color: #6c5ce7; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.3s; }',
    c
)

c = re.sub(
    r'\.btn-fund:hover\s*\{[^}]*\}',
    '.btn-fund:hover { box-shadow: 0 6px 30px rgba(0,0,0,0.15); transform: translateY(-2px); }',
    c
)

print("  Fixed wallet card CSS.")

# Bottom nav — white
c = re.sub(
    r'\.bottom-nav\s*\{[^}]*\}',
    '.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.05); box-shadow: 0 -4px 20px rgba(0,0,0,0.06); display: flex; justify-content: space-around; padding: 8px 0; z-index: 100; }',
    c
)

c = re.sub(
    r'\.nav-btn\s*\{[^}]*\}',
    '.nav-btn { background: none; border: none; color: #b2bec3; font-size: 0.65em; display: flex; flex-direction: column; align-items: center; cursor: pointer; padding: 5px; width: 100%; }',
    c
)

c = re.sub(
    r'\.nav-btn\.active\s*\{[^}]*\}',
    '.nav-btn.active { color: #6c5ce7; font-weight: bold; }',
    c
)

c = re.sub(
    r'\.nav-icon\s*\{[^}]*\}',
    '.nav-icon { font-size: 1.5em; margin-bottom: 3px; transition: transform 0.2s; }',
    c
)

if '.nav-btn.active .nav-icon' in c:
    c = re.sub(r'\.nav-btn\.active \.nav-icon\s*\{[^}]*\}', 
        '.nav-btn.active .nav-icon { transform: scale(1.15); }', c)

print("  Fixed bottom navigation CSS.")

# General inputs
c = re.sub(
    r'input, select\s*\{[^}]*\}',
    'input, select { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #dfe6e9; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #ffffff; color: #2d3436; }',
    c
)

# General buttons
c = re.sub(
    r'^button\s*\{[^}]*\}',
    'button { width: 100%; padding: 12px; background: linear-gradient(135deg, #6c5ce7, #5849be); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }',
    c, count=1, flags=re.MULTILINE
)

# KPI cards
c = re.sub(
    r'\.kpi-card\s*\{[^}]*\}',
    '.kpi-card { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 10px rgba(0,0,0,0.04); text-align: center; }',
    c
)

# Credit card
c = re.sub(
    r'\.credit-card\s*\{[^}]*\}',
    '.credit-card { background: #ffffff; border: 2px dashed rgba(108, 92, 231, 0.2); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }',
    c
)

# Utility card
c = re.sub(
    r'\.utility-card\s*\{[^}]*\}',
    '.utility-card { display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: #f8f9fa; border: 1px solid rgba(0,0,0,0.05); }',
    c
)

# Change password modal
c = re.sub(
    r'\.change-pw-content\s*\{[^}]*\}',
    '.change-pw-content { background: #ffffff; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 20px 60px rgba(0,0,0,0.15); }',
    c
)

# Force-change screen
c = re.sub(
    r'\.force-change-screen\s*\{[^}]*\}',
    '.force-change-screen { display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 40%, #6c5ce7 100%); color: white; padding: 20px; box-sizing: border-box; }',
    c
)

print("  Fixed all remaining CSS rules.")

# === STEP 6: Fix scrollbar ===
c = c.replace('::-webkit-scrollbar-track { background: #f5f6fa; }',
              '::-webkit-scrollbar-track { background: #f5f6fa; }')
c = c.replace('::-webkit-scrollbar-thumb { background: #6c5ce7; border-radius: 3px; }',
              '::-webkit-scrollbar-thumb { background: #6c5ce7; border-radius: 3px; }')
c = c.replace('::-webkit-scrollbar-thumb:hover { background: #5849be; }',
              '::-webkit-scrollbar-thumb:hover { background: #5849be; }')

# === STEP 7: Update B-BBEE badge ===
if 'Level 1 B-BBEE' in c:
    c = c.replace(
        'background:rgba(108,92,231,0.1); color:#6c5ce7; border:1px solid rgba(108,92,231,0.3);',
        'background:rgba(255,255,255,0.15); color:#ffffff; border:1px solid rgba(255,255,255,0.25);'
    )

# === STEP 8: Update SERVICES subtitle ===
if 'SERVICES' in c and 'color:' in c:
    c = c.replace(
        "color: #636e72; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px; opacity: 0.8;\">SERVICES",
        "color: rgba(255,255,255,0.8); font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px;\">SERVICES"
    )

# === STEP 9: Replace any animation ===
c = c.replace('@keyframes oceanWave', '@keyframes sunsetPulse')
c = c.replace('@keyframes emeraldGlow', '@keyframes sunsetPulse')
c = c.replace('animation: oceanWave', 'animation: sunsetPulse')
c = c.replace('animation: emeraldGlow', 'animation: sunsetPulse')

# Update animation content
c = re.sub(
    r'@keyframes sunsetPulse\s*\{[^}]*\}',
    '@keyframes sunsetPulse { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }',
    c
)

# Update animation particles
c = c.replace(
    'rgba(108, 92, 231, 0.06)',
    'rgba(255, 107, 107, 0.1)'
)
c = c.replace(
    'rgba(108, 92, 231, 0.04)',
    'rgba(108, 92, 231, 0.08)'
)

print("  Fixed animation and badges.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print("SUNSET THEME APPLIED FROM SCRATCH!")
print(f"{'='*55}")
print("""
This script:
  1. Restored from clean backup (before any branding)
  2. Replaced EVERY color from EVERY previous theme
  3. Used regex to fix ALL CSS rules
  4. No chaining — applies directly from clean state

Color scheme:
  Login:    Orange → magenta → purple gradient
  App bg:   #f5f6fa (light)
  Cards:    #ffffff (white)
  Accent:   #6c5ce7 (purple)
  Text:     #2d3436 (dark)
  Wallet:   Sunset gradient (orange → purple)
  Buttons:  Purple gradient, white text
  
Test: http://127.0.0.1:8000/tenant (Ctrl+F5)
  *** If still showing old theme, also clear localStorage:
      F12 → Console → localStorage.clear() → F5 ***
""")