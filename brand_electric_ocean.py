import shutil, re

print("Switching to Electric Ocean theme...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_ocean')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace :root variables ===
new_root = """:root {
            --bg: #001428;
            --card-bg: #001f3f;
            --card-border: #003d5c;
            --text: #e0f7fa;
            --text-dim: #5c7a89;
            --accent: #00d4d4;
            --accent-glow: rgba(0, 212, 212, 0.3);
            --success: #00ff9f;
            --danger: #ff6b6b;
            --warning: #ff9502;
            --primary: #001428;
            --secondary: #00d4d4;
            --gray: #5c7a89;
            --light: #001f3f;
            --dark: #001428;
        }"""

c = re.sub(r':root\s*\{[^}]*\}', new_root, c, count=1)
print("  Set Electric Ocean color variables.")

# === 2. Replace ALL color values ===
replacements = [
    # Backgrounds — charcoal → deep ocean
    ('#0d1117', '#001428'),
    ('#161b22', '#001f3f'),
    ('#30363d', '#003d5c'),
    
    # Accent — neon cyan → turquoise
    ('#00d4ff', '#00d4d4'),
    ('rgba(0, 212, 255,', 'rgba(0, 212, 212,'),
    ('#0099cc', '#008080'),
    
    # Success — neon green → mint
    ('#00ff88', '#00ff9f'),
    
    # Danger — hot red → coral
    ('#ff4757', '#ff6b6b'),
    ('rgba(255, 71, 87,', 'rgba(255, 107, 107,'),
    
    # Text — soft white → cyan-white
    ('#e6edf3', '#e0f7fa'),
    
    # Dim text
    ('#8b949e', '#5c7a89'),
    ('#6e7681', '#4a6275'),
    
    # Warning — keep orange
    ('#ffa502', '#ff9502'),
    
    # Darker accent for gradients
    ('#1565c0', '#006666'),
    ('#0a2540', '#001428'),
]

for old, new in replacements:
    c = c.replace(old, new)

print("  Replaced all colors.")

# === 3. Login screen — deep ocean with turquoise glow ===
c = c.replace(
    "background: radial-gradient(circle at 50% 30%, #001f3f 0%, #001428 100%);",
    "background: radial-gradient(ellipse at 50% 0%, #003d5c 0%, #001428 50%, #000a14 100%);"
)

# Login logo — turquoise glow
c = c.replace(
    "color: #00d4d4; text-shadow: 0 0 20px rgba(0, 212, 212, 0.5), 0 0 40px rgba(0, 212, 212, 0.3);",
    "color: #00d4d4; text-shadow: 0 0 20px rgba(0, 212, 212, 0.6), 0 0 40px rgba(0, 212, 212, 0.3), 0 0 60px rgba(0, 255, 159, 0.15);"
)

# Login card — ocean glass
c = c.replace(
    "border: 1px solid #003d5c; box-shadow: 0 0 60px rgba(0, 212, 212, 0.1), 0 20px 40px rgba(0,0,0,0.5);",
    "border: 1px solid rgba(0, 212, 212, 0.2); box-shadow: 0 0 80px rgba(0, 212, 212, 0.08), 0 0 40px rgba(0, 255, 159, 0.05), 0 20px 40px rgba(0,0,0,0.5);"
)

# Login button — turquoise gradient
c = c.replace(
    "background: linear-gradient(135deg, #00d4d4, #008080); color: #001428;",
    "background: linear-gradient(135deg, #00d4d4, #008080); color: #001428;"
)
c = c.replace(
    "box-shadow: 0 4px 20px rgba(0, 212, 212, 0.3);",
    "box-shadow: 0 4px 25px rgba(0, 212, 212, 0.35);"
)

print("  Built ocean login screen.")

# === 4. Wallet card — deep ocean with turquoise glow ===
c = c.replace(
    "background: linear-gradient(135deg, #001428, #001f3f); border: 1px solid rgba(0, 212, 212, 0.2);",
    "background: linear-gradient(135deg, #001428, #003d5c); border: 1px solid rgba(0, 212, 212, 0.15);"
)

c = c.replace(
    "box-shadow: 0 0 40px rgba(0, 212, 212, 0.08), 0 10px 30px rgba(0,0,0,0.4);",
    "box-shadow: 0 0 50px rgba(0, 212, 212, 0.1), 0 0 30px rgba(0, 255, 159, 0.05), 0 10px 30px rgba(0,0,0,0.4);"
)

# Wallet balance — turquoise with glow
c = c.replace(
    "color: #00d4d4; text-shadow: 0 0 30px rgba(0, 212, 212, 0.3);",
    "color: #00d4d4; text-shadow: 0 0 30px rgba(0, 212, 212, 0.4), 0 0 60px rgba(0, 255, 159, 0.1);"
)

# Fund button — turquoise gradient
c = c.replace(
    "background: linear-gradient(135deg, #00d4d4, #008080); color: #001428; border: none; padding: 15px; width: 100%;",
    "background: linear-gradient(135deg, #00d4d4, #00b3b3); color: #001428; border: none; padding: 15px; width: 100%;"
)

print("  Built ocean wallet card.")

# === 5. Cards — ocean dark ===
c = c.replace(
    "border: 1px solid #003d5c; box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: border-color 0.3s, box-shadow 0.3s;",
    "border: 1px solid rgba(0, 61, 92, 0.5); box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: border-color 0.3s, box-shadow 0.3s;"
)

c = c.replace(
    "border-color: rgba(0, 212, 212, 0.3); box-shadow: 0 8px 30px rgba(0, 212, 212, 0.08);",
    "border-color: rgba(0, 212, 212, 0.3); box-shadow: 0 8px 30px rgba(0, 212, 212, 0.1), 0 0 20px rgba(0, 255, 159, 0.03);"
)

print("  Built ocean cards.")

# === 6. Bottom nav — ocean with turquoise active ===
c = c.replace(
    "background: rgba(0, 20, 40, 0.95); backdrop-filter: blur(10px); border-top: 1px solid #003d5c;",
    "background: rgba(0, 20, 40, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(0, 212, 212, 0.1);"
)

c = c.replace(
    "color: #00d4d4; font-weight: bold; text-shadow: 0 0 10px rgba(0, 212, 212, 0.3);",
    "color: #00d4d4; font-weight: bold; text-shadow: 0 0 12px rgba(0, 212, 212, 0.4);"
)

c = c.replace(
    "filter: drop-shadow(0 0 8px rgba(0, 212, 212, 0.4));",
    "filter: drop-shadow(0 0 10px rgba(0, 212, 212, 0.5));"
)

print("  Built ocean bottom navigation.")

# === 7. Inputs — ocean dark with turquoise focus ===
c = c.replace(
    "background: #001428; color: #e0f7fa; transition: border-color 0.3s, box-shadow 0.3s;",
    "background: #000a14; color: #e0f7fa; transition: border-color 0.3s, box-shadow 0.3s;"
)

c = c.replace(
    "border-color: #00d4d4; box-shadow: 0 0 0 3px rgba(0, 212, 212, 0.15);",
    "border-color: #00d4d4; box-shadow: 0 0 0 3px rgba(0, 212, 212, 0.15), 0 0 20px rgba(0, 212, 212, 0.1);"
)

print("  Built ocean inputs with turquoise focus glow.")

# === 8. Scrollbar — ocean themed ===
c = c.replace("::-webkit-scrollbar-track { background: #001428; }", 
              "::-webkit-scrollbar-track { background: #000a14; }")
c = c.replace("::-webkit-scrollbar-thumb:hover { background: #00d4d4; }",
              "::-webkit-scrollbar-thumb:hover { background: #00ff9f; }")

print("  Built ocean scrollbar.")

# === 9. Update B-BBEE badge ===
c = c.replace(
    "background:rgba(0,212,212,0.1); color:#00d4d4; border:1px solid rgba(0,212,212,0.2);",
    "background:rgba(0,212,212,0.08); color:#00d4d4; border:1px solid rgba(0,212,212,0.25);"
)

# === 10. Update alert banners for ocean theme ===
c = c.replace(
    "background-color: rgba(255, 107, 107, 0.08); color: #ff6b6b; border-left-color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.2);",
    "background-color: rgba(255, 107, 107, 0.06); color: #ff6b6b; border-left-color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.15);"
)

c = c.replace(
    "background-color: rgba(255, 149, 2, 0.08); color: #ff9502; border-left-color: #ff9502; border: 1px solid rgba(255, 149, 2, 0.2);",
    "background-color: rgba(255, 149, 2, 0.06); color: #ff9502; border-left-color: #ff9502; border: 1px solid rgba(255, 149, 2, 0.15);"
)

# === 11. KPI cards — ocean accents ===
c = c.replace(
    ".kpi-card.success .val { color: #00ff9f; }",
    ".kpi-card.success .val { color: #00ff9f; text-shadow: 0 0 10px rgba(0, 255, 159, 0.3); }"
)

c = c.replace(
    ".kpi-card.danger .val { color: #ff6b6b; }",
    ".kpi-card.danger .val { color: #ff6b6b; text-shadow: 0 0 10px rgba(255, 107, 107, 0.3); }"
)

c = c.replace(
    ".kpi-card.secondary .val { color: #00d4d4; }",
    ".kpi-card.secondary .val { color: #00d4d4; text-shadow: 0 0 10px rgba(0, 212, 212, 0.3); }"
)

print("  Built ocean KPI cards with glow.")

# === 12. Update utility buy buttons ===
c = c.replace(
    "background: linear-gradient(135deg, #00d4d4, #00b3b3); color: #001428;",
    "background: linear-gradient(135deg, #00d4d4, #00b3b3); color: #001428;"
)

c = c.replace(
    "background: linear-gradient(135deg, #ff6b6b, #c0392b); color: white;",
    "background: linear-gradient(135deg, #ff6b6b, #c0392b); color: white;"
)

# === 13. Add subtle ocean wave animation on login ===
if '@keyframes oceanWave' not in c:
    wave_css = """
        @keyframes oceanWave { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .login-screen::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 30% 20%, rgba(0, 212, 212, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(0, 255, 159, 0.05) 0%, transparent 50%); pointer-events: none; animation: oceanWave 8s ease-in-out infinite; background-size: 200% 200%; }
        .force-change-screen::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 30% 20%, rgba(0, 212, 212, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(0, 255, 159, 0.05) 0%, transparent 50%); pointer-events: none; animation: oceanWave 8s ease-in-out infinite; background-size: 200% 200%; }
    """
    c = c.replace('<style>', '<style>\n' + wave_css, 1)
    print("  Added ocean wave animation on login screen.")

# === 14. Update change password modal ===
c = c.replace(
    "border: 1px solid #003d5c; box-shadow: 0 0 60px rgba(0, 212, 212, 0.1), 0 20px 40px rgba(0,0,0,0.5);",
    "border: 1px solid rgba(0, 212, 212, 0.15); box-shadow: 0 0 60px rgba(0, 212, 212, 0.08), 0 20px 40px rgba(0,0,0,0.5);"
)

print("  Built ocean modal.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print("ELECTRIC OCEAN THEME COMPLETE!")
print(f"{'='*55}")
print("""
Color scheme:
  Background:  #001428 (deep ocean)
  Cards:       #001f3f (dark navy)
  Borders:     #003d5c (dark cyan)
  Accent:      #00d4d4 (turquoise — water + energy)
  Success:     #00ff9f (mint — bioluminescence)
  Danger:      #ff6b6b (coral)
  Warning:     #ff9502 (orange)
  Text:        #e0f7fa (cyan-white — foam)
  
Special effects:
  - Ocean wave animation on login (subtle moving gradient)
  - Turquoise glow on all accent elements
  - Mint green glow on success elements
  - Glassmorphism with blur
  - Custom ocean scrollbar
  
Test: http://127.0.0.1:8000/tenant (Ctrl+F5)
""")