import shutil, re

print("Switching to Emerald Gold theme...")

shutil.copy('tenant_portal.html', 'tenant_portal.html.bak_emerald')

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace :root variables ===
new_root = """:root {
            --bg: #0a2e1f;
            --card-bg: #0f3d2a;
            --card-border: #1a5e3a;
            --text: #e8f5e9;
            --text-dim: #7a9b87;
            --accent: #d4af37;
            --accent-glow: rgba(212, 175, 55, 0.3);
            --success: #2ecc71;
            --danger: #e74c3c;
            --warning: #f39c12;
            --primary: #0a2e1f;
            --secondary: #d4af37;
            --gray: #7a9b87;
            --light: #0f3d2a;
            --dark: #0a2e1f;
        }"""

c = re.sub(r':root\s*\{[^}]*\}', new_root, c, count=1)
print("  Set Emerald Gold color variables.")

# === 2. Replace ALL color values ===
replacements = [
    # Backgrounds — ocean → emerald
    ('#001428', '#0a2e1f'),
    ('#001f3f', '#0f3d2a'),
    ('#000a14', '#061d12'),
    ('#003d5c', '#1a5e3a'),
    
    # Accent — turquoise → gold
    ('#00d4d4', '#d4af37'),
    ('rgba(0, 212, 212,', 'rgba(212, 175, 55,'),
    ('#008080', '#b8941f'),
    ('#00b3b3', '#c9a227'),
    
    # Success — mint → green
    ('#00ff9f', '#2ecc71'),
    ('rgba(0, 255, 159,', 'rgba(46, 204, 113,'),
    
    # Danger — coral → red
    ('#ff6b6b', '#e74c3c'),
    ('rgba(255, 107, 107,', 'rgba(231, 76, 60,'),
    
    # Warning
    ('#ff9502', '#f39c12'),
    
    # Text — cyan-white → green-white
    ('#e0f7fa', '#e8f5e9'),
    
    # Dim text
    ('#5c7a89', '#7a9b87'),
    ('#4a6275', '#5a7a66'),
]

for old, new in replacements:
    c = c.replace(old, new)

print("  Replaced all colors.")

# === 3. Login screen — emerald gradient with gold glow ===
c = c.replace(
    "background: radial-gradient(ellipse at 50% 0%, #1a5e3a 0%, #0a2e1f 50%, #061d12 100%);",
    "background: radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%);"
)

# Login logo — gold glow
c = c.replace(
    "color: #d4af37; text-shadow: 0 0 20px rgba(212, 175, 55, 0.6), 0 0 40px rgba(212, 175, 55, 0.3), 0 0 60px rgba(46, 204, 113, 0.15);",
    "color: #d4af37; text-shadow: 0 0 20px rgba(212, 175, 55, 0.6), 0 0 40px rgba(212, 175, 55, 0.4), 0 0 80px rgba(212, 175, 55, 0.15);"
)

# Login card — emerald glass with gold border
c = c.replace(
    "border: 1px solid rgba(212, 175, 55, 0.2); box-shadow: 0 0 80px rgba(212, 175, 55, 0.08), 0 0 40px rgba(46, 204, 113, 0.05), 0 20px 40px rgba(0,0,0,0.5);",
    "border: 1px solid rgba(212, 175, 55, 0.2); box-shadow: 0 0 60px rgba(212, 175, 55, 0.1), 0 0 40px rgba(212, 175, 55, 0.05), 0 20px 40px rgba(0,0,0,0.5);"
)

# Login button — gold gradient
c = c.replace(
    "background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f;",
    "background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f;"
)
c = c.replace(
    "box-shadow: 0 4px 25px rgba(212, 175, 55, 0.35);",
    "box-shadow: 0 4px 25px rgba(212, 175, 55, 0.35);"
)

print("  Built emerald login screen with gold glow.")

# === 4. Wallet card — emerald with gold ===
c = c.replace(
    "background: linear-gradient(135deg, #0a2e1f, #1a5e3a); border: 1px solid rgba(212, 175, 55, 0.15);",
    "background: linear-gradient(135deg, #0a2e1f, #0f3d2a); border: 1px solid rgba(212, 175, 55, 0.15);"
)

c = c.replace(
    "box-shadow: 0 0 50px rgba(212, 175, 55, 0.1), 0 0 30px rgba(46, 204, 113, 0.05), 0 10px 30px rgba(0,0,0,0.4);",
    "box-shadow: 0 0 50px rgba(212, 175, 55, 0.08), 0 10px 30px rgba(0,0,0,0.4);"
)

# Wallet balance — gold with glow
c = c.replace(
    "color: #d4af37; text-shadow: 0 0 30px rgba(212, 175, 55, 0.4), 0 0 60px rgba(46, 204, 113, 0.1);",
    "color: #d4af37; text-shadow: 0 0 30px rgba(212, 175, 55, 0.5), 0 0 60px rgba(212, 175, 55, 0.2);"
)

# Fund button — gold gradient
c = c.replace(
    "background: linear-gradient(135deg, #d4af37, #c9a227); color: #0a2e1f; border: none; padding: 15px; width: 100%;",
    "background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f; border: none; padding: 15px; width: 100%;"
)

print("  Built emerald wallet card with gold accents.")

# === 5. Cards — emerald with gold hover ===
c = c.replace(
    "border: 1px solid rgba(26, 94, 58, 0.5); box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: border-color 0.3s, box-shadow 0.3s;",
    "border: 1px solid rgba(26, 94, 58, 0.4); box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: border-color 0.3s, box-shadow 0.3s;"
)

c = c.replace(
    "border-color: rgba(212, 175, 55, 0.3); box-shadow: 0 8px 30px rgba(212, 175, 55, 0.1), 0 0 20px rgba(46, 204, 113, 0.03);",
    "border-color: rgba(212, 175, 55, 0.3); box-shadow: 0 8px 30px rgba(212, 175, 55, 0.08);"
)

print("  Built emerald cards with gold hover.")

# === 6. Bottom nav — emerald with gold active ===
c = c.replace(
    "background: rgba(0, 20, 40, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(212, 175, 55, 0.1);",
    "background: rgba(10, 46, 31, 0.95); backdrop-filter: blur(10px); border-top: 1px solid rgba(212, 175, 55, 0.1);"
)

c = c.replace(
    "color: #d4af37; font-weight: bold; text-shadow: 0 0 12px rgba(212, 175, 55, 0.4);",
    "color: #d4af37; font-weight: bold; text-shadow: 0 0 12px rgba(212, 175, 55, 0.5);"
)

c = c.replace(
    "filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.5));",
    "filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.5));"
)

print("  Built emerald bottom navigation with gold active.")

# === 7. Inputs — dark emerald with gold focus ===
c = c.replace(
    "background: #061d12; color: #e8f5e9; transition: border-color 0.3s, box-shadow 0.3s;",
    "background: #061d12; color: #e8f5e9; transition: border-color 0.3s, box-shadow 0.3s;"
)

c = c.replace(
    "border-color: #d4af37; box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.15), 0 0 20px rgba(212, 175, 55, 0.1);",
    "border-color: #d4af37; box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.15), 0 0 15px rgba(212, 175, 55, 0.1);"
)

print("  Built emerald inputs with gold focus glow.")

# === 8. Scrollbar — emerald with gold ===
c = c.replace("::-webkit-scrollbar-track { background: #061d12; }", 
              "::-webkit-scrollbar-track { background: #051910; }")

print("  Built emerald scrollbar.")

# === 9. B-BBEE badge — gold ===
c = c.replace(
    "background:rgba(212,175,55,0.08); color:#d4af37; border:1px solid rgba(212,175,55,0.25);",
    "background:rgba(212,175,55,0.1); color:#d4af37; border:1px solid rgba(212,175,55,0.3);"
)

# === 10. KPI cards — gold accents ===
c = c.replace(
    ".kpi-card.success .val { color: #2ecc71; text-shadow: 0 0 10px rgba(46, 204, 113, 0.3); }",
    ".kpi-card.success .val { color: #2ecc71; text-shadow: 0 0 10px rgba(46, 204, 113, 0.3); }"
)

c = c.replace(
    ".kpi-card.danger .val { color: #e74c3c; text-shadow: 0 0 10px rgba(231, 76, 60, 0.3); }",
    ".kpi-card.danger .val { color: #e74c3c; text-shadow: 0 0 10px rgba(231, 76, 60, 0.3); }"
)

c = c.replace(
    ".kpi-card.secondary .val { color: #d4af37; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }",
    ".kpi-card.secondary .val { color: #d4af37; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }"
)

print("  Built emerald KPI cards with gold accents.")

# === 11. Replace ocean wave animation with emerald gold shimmer ===
c = c.replace('@keyframes oceanWave', '@keyframes emeraldGlow')
c = c.replace('animation: oceanWave 8s ease-in-out infinite;', 'animation: emeraldGlow 6s ease-in-out infinite;')

# Update the animation colors from turquoise/mint to gold/emerald
c = c.replace(
    "background: radial-gradient(ellipse at 30% 20%, rgba(212, 175, 55, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(46, 204, 113, 0.05) 0%, transparent 50%);",
    "background: radial-gradient(ellipse at 30% 20%, rgba(212, 175, 55, 0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(212, 175, 55, 0.04) 0%, transparent 50%);"
)

# Update the keyframes content
c = c.replace(
    "@keyframes emeraldGlow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }",
    "@keyframes emeraldGlow { 0% { opacity: 0.3; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.05); } 100% { opacity: 0.3; transform: scale(1); } }"
)

print("  Replaced ocean wave with emerald glow animation.")

# === 12. Update change password modal ===
c = c.replace(
    "border: 1px solid rgba(212, 175, 55, 0.15); box-shadow: 0 0 60px rgba(212, 175, 55, 0.08), 0 20px 40px rgba(0,0,0,0.5);",
    "border: 1px solid rgba(212, 175, 55, 0.15); box-shadow: 0 0 60px rgba(212, 175, 55, 0.06), 0 20px 40px rgba(0,0,0,0.5);"
)

# === 13. Update alert banners ===
c = c.replace(
    "background-color: rgba(231, 76, 60, 0.06); color: #e74c3c; border-left-color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.15);",
    "background-color: rgba(231, 76, 60, 0.05); color: #e74c3c; border-left-color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.12);"
)

c = c.replace(
    "background-color: rgba(243, 156, 18, 0.06); color: #f39c12; border-left-color: #f39c12; border: 1px solid rgba(243, 156, 18, 0.15);",
    "background-color: rgba(243, 156, 18, 0.05); color: #f39c12; border-left-color: #f39c12; border: 1px solid rgba(243, 156, 18, 0.12);"
)

# === 14. Update credit card (emergency fund) ===
c = c.replace(
    "border: 2px dashed rgba(243, 156, 18, 0.4);",
    "border: 2px dashed rgba(212, 175, 55, 0.3);"
)

c = c.replace(
    ".credit-card h3 { color: #f39c12;",
    ".credit-card h3 { color: #d4af37;"
)

c = c.replace(
    ".credit-card .val { font-size: 1.8em; font-weight: bold; color: #f39c12;",
    ".credit-card .val { font-size: 1.8em; font-weight: bold; color: #d4af37;"
)

# === 15. Update utility buttons ===
c = c.replace(
    "background: linear-gradient(135deg, #d4af37, #c9a227); color: #0a2e1f;",
    "background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f;"
)

c = c.replace(
    "background: linear-gradient(135deg, #e74c3c, #c0392b); color: white;",
    "background: linear-gradient(135deg, #e74c3c, #c0392b); color: white;"
)

# Electricity button — gold
c = c.replace(
    ".btn-elec { background: linear-gradient(135deg, #f39c12, #ff6b00); color: #0a2e1f; }",
    ".btn-elec { background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f; }"
)

# Cold water button — emerald
c = c.replace(
    ".btn-water-cold { background: linear-gradient(135deg, #d4af37, #b8941f); color: #0a2e1f; }",
    ".btn-water-cold { background: linear-gradient(135deg, #2ecc71, #27ae60); color: #0a2e1f; }"
)

# Hot water button — red
c = c.replace(
    ".btn-water-hot { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }",
    ".btn-water-hot { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }"
)

print("  Built emerald utility buttons.")

# === 16. Token button — gold ===
c = c.replace(
    ".btn-token { background: rgba(212, 175, 55, 0.15); color: #d4af37; border: 1px solid rgba(212, 175, 55, 0.3);",
    ".btn-token { background: rgba(212, 175, 55, 0.1); color: #d4af37; border: 1px solid rgba(212, 175, 55, 0.25);"
)

# Token link
if 'token-link' in c:
    c = c.replace(
        "color:#d4af37;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;",
        "color:#d4af37;cursor:pointer;text-decoration:underline;font-size:0.75em;margin-left:5px;"
    )

# === 17. Insight card — gold accent ===
c = c.replace(
    "background: rgba(212, 175, 55, 0.05); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #d4af37;",
    "background: rgba(212, 175, 55, 0.04); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #d4af37;"
)

# === 18. Update forgot/force-change screens ===
c = c.replace(
    "background: radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%);",
    "background: radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%);"
)

# Force change screen logo
c = c.replace(
    'style="font-size: 1.8em; color: #d4af37; text-shadow: 0 0 20px rgba(212,175,55,0.4);">ELUP',
    'style="font-size: 1.8em; color: #d4af37; text-shadow: 0 0 20px rgba(212,175,55,0.5);">ELUP'
)

# === 19. Update PayGate button ===
c = c.replace(
    ".btn-paygate { background: linear-gradient(135deg, #0a2e1f, #0f3d2a); color: #d4af37; border: 1px solid rgba(212,175,55,0.3); }",
    ".btn-paygate { background: linear-gradient(135deg, #0f3d2a, #0a2e1f); color: #d4af37; border: 1px solid rgba(212,175,55,0.25); }"
)

# === 20. Update smart meter info banner ===
if 'smartMeterInfo' in c:
    c = c.replace(
        'background: rgba(212, 175, 55, 0.05); border-left: 4px solid #d4af37;',
        'background: rgba(212, 175, 55, 0.04); border-left: 4px solid #d4af37;'
    )

print("  Built all emerald gold accents.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*55}")
print("EMERALD GOLD THEME COMPLETE!")
print(f"{'='*55}")
print("""
Color scheme:
  Background:  #0a2e1f (deep emerald)
  Cards:       #0f3d2a (dark green)
  Borders:     #1a5e3a (forest green)
  Accent:      #d4af37 (GOLD)
  Success:     #2ecc71 (green)
  Danger:      #e74c3c (red)
  Warning:     #f39c12 (orange)
  Text:        #e8f5e9 (soft green-white)
  
Special effects:
  - Emerald glow animation on login (subtle pulsing)
  - Gold glow on all accent elements
  - Gold text-shadow on ELUP logo
  - Gold gradient buttons with dark green text
  - Glassmorphism with blur
  - Gold scrollbar
  
Button colors:
  Electricity:  Gold gradient (d4af37 → b8941f)
  Cold Water:   Green gradient (2ecc71 → 27ae60)
  Hot Water:    Red gradient (e74c3c → c0392b)
  Login:        Gold gradient
  Fund Wallet:  Gold gradient
  
Test: http://127.0.0.1:8000/tenant (Ctrl+F5)
""")