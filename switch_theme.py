import shutil, os, re

print("=" * 50)
print("  THEME SWITCHER")
print("=" * 50)
print()
print("  A = Dark Premium (charcoal + neon cyan)")
print("  B = Emerald Gold (dark green + gold)")
print("  C = Electric Ocean (dark blue + turquoise)")
print("  S = Sunset (orange → purple gradient)")
print()
choice = input("  Enter A, B, C, or S: ").strip().upper()

themes = {
    'A': {
        'name': 'Dark Premium',
        'body_bg': '#0d1117', 'text': '#e6edf3', 'card_bg': '#161b22',
        'card_border': '#30363d', 'input_bg': '#0d1117', 'accent': '#00d4ff',
        'success': '#00ff88', 'danger': '#ff4757', 'warning': '#ffa502',
        'text_dim': '#8b949e', 'nav_inactive': '#6e7681', 'nav_active': '#00d4ff',
        'login_bg': 'radial-gradient(circle at 50% 30%, #161b22 0%, #0d1117 100%)',
        'login_card_bg': 'rgba(22, 27, 34, 0.85)',
        'login_card_border': '1px solid #30363d',
        'login_card_shadow': '0 0 60px rgba(0, 212, 255, 0.1), 0 20px 40px rgba(0,0,0,0.5)',
        'login_logo_color': '#00d4ff',
        'login_logo_shadow': '0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(0, 212, 255, 0.3)',
        'login_btn_bg': 'linear-gradient(135deg, #00d4ff, #0099cc)',
        'login_btn_color': '#0d1117',
        'header_bg': 'rgba(13, 17, 23, 0.95)', 'header_border': '1px solid #30363d',
        'wallet_bg': 'linear-gradient(135deg, #0d1117, #161b22)',
        'wallet_border': '1px solid rgba(0, 212, 255, 0.2)',
        'wallet_balance_color': '#00d4ff',
        'wallet_balance_shadow': '0 0 30px rgba(0, 212, 255, 0.3)',
        'fund_btn_bg': 'linear-gradient(135deg, #00d4ff, #0099cc)', 'fund_btn_color': '#0d1117',
        'nav_bg': 'rgba(13, 17, 23, 0.95)',
        'btn_bg': 'linear-gradient(135deg, #00d4ff, #0099cc)', 'btn_color': '#0d1117',
        'rgba_accent': 'rgba(0, 212, 255,', 'rgba_success': 'rgba(0, 255, 136,',
        'rgba_danger': 'rgba(255, 71, 87,', 'badge_bg': 'rgba(0,212,255,0.1)',
        'badge_color': '#00d4ff', 'badge_border': '1px solid rgba(0,212,255,0.3)',
        'subtitle_color': 'rgba(230, 237, 243, 0.8)',
        'animation_name': 'darkGlow', 'animation_particles': 'rgba(0, 212, 255, 0.06)',
        'shadow_opacity': '3',
    },
    'B': {
        'name': 'Emerald Gold',
        'body_bg': '#0a2e1f', 'text': '#e8f5e9', 'card_bg': '#0f3d2a',
        'card_border': '#1a5e3a', 'input_bg': '#061d12', 'accent': '#d4af37',
        'success': '#2ecc71', 'danger': '#e74c3c', 'warning': '#f39c12',
        'text_dim': '#7a9b87', 'nav_inactive': '#7a9b87', 'nav_active': '#d4af37',
        'login_bg': 'radial-gradient(ellipse at 50% 0%, #0f3d2a 0%, #0a2e1f 50%, #051910 100%)',
        'login_card_bg': 'rgba(15, 61, 42, 0.85)',
        'login_card_border': '1px solid rgba(212, 175, 55, 0.2)',
        'login_card_shadow': '0 0 60px rgba(212, 175, 55, 0.1), 0 20px 40px rgba(0,0,0,0.5)',
        'login_logo_color': '#d4af37',
        'login_logo_shadow': '0 0 20px rgba(212, 175, 55, 0.6), 0 0 40px rgba(212, 175, 55, 0.4)',
        'login_btn_bg': 'linear-gradient(135deg, #d4af37, #b8941f)',
        'login_btn_color': '#0a2e1f',
        'header_bg': 'rgba(10, 46, 31, 0.95)', 'header_border': '1px solid #1a5e3a',
        'wallet_bg': 'linear-gradient(135deg, #0a2e1f, #0f3d2a)',
        'wallet_border': '1px solid rgba(212, 175, 55, 0.15)',
        'wallet_balance_color': '#d4af37',
        'wallet_balance_shadow': '0 0 30px rgba(212, 175, 55, 0.5)',
        'fund_btn_bg': 'linear-gradient(135deg, #d4af37, #b8941f)', 'fund_btn_color': '#0a2e1f',
        'nav_bg': 'rgba(10, 46, 31, 0.95)',
        'btn_bg': 'linear-gradient(135deg, #d4af37, #b8941f)', 'btn_color': '#0a2e1f',
        'rgba_accent': 'rgba(212, 175, 55,', 'rgba_success': 'rgba(46, 204, 113,',
        'rgba_danger': 'rgba(231, 76, 60,', 'badge_bg': 'rgba(212,175,55,0.1)',
        'badge_color': '#d4af37', 'badge_border': '1px solid rgba(212,175,55,0.3)',
        'subtitle_color': 'rgba(232, 245, 233, 0.8)',
        'animation_name': 'emeraldGlow', 'animation_particles': 'rgba(212, 175, 55, 0.06)',
        'shadow_opacity': '3',
    },
    'C': {
        'name': 'Electric Ocean',
        'body_bg': '#001428', 'text': '#e0f7fa', 'card_bg': '#001f3f',
        'card_border': '#003d5c', 'input_bg': '#000a14', 'accent': '#00d4d4',
        'success': '#00ff9f', 'danger': '#ff6b6b', 'warning': '#ff9502',
        'text_dim': '#5c7a89', 'nav_inactive': '#5c7a89', 'nav_active': '#00d4d4',
        'login_bg': 'radial-gradient(ellipse at 50% 0%, #003d5c 0%, #001428 50%, #000a14 100%)',
        'login_card_bg': 'rgba(0, 31, 63, 0.85)',
        'login_card_border': '1px solid rgba(0, 212, 212, 0.2)',
        'login_card_shadow': '0 0 80px rgba(0, 212, 212, 0.08), 0 0 40px rgba(0, 255, 159, 0.05), 0 20px 40px rgba(0,0,0,0.5)',
        'login_logo_color': '#00d4d4',
        'login_logo_shadow': '0 0 20px rgba(0, 212, 212, 0.6), 0 0 40px rgba(0, 212, 212, 0.3)',
        'login_btn_bg': 'linear-gradient(135deg, #00d4d4, #008080)',
        'login_btn_color': '#001428',
        'header_bg': 'rgba(0, 20, 40, 0.95)', 'header_border': '1px solid #003d5c',
        'wallet_bg': 'linear-gradient(135deg, #001428, #003d5c)',
        'wallet_border': '1px solid rgba(0, 212, 212, 0.15)',
        'wallet_balance_color': '#00d4d4',
        'wallet_balance_shadow': '0 0 30px rgba(0, 212, 212, 0.4)',
        'fund_btn_bg': 'linear-gradient(135deg, #00d4d4, #00b3b3)', 'fund_btn_color': '#001428',
        'nav_bg': 'rgba(0, 20, 40, 0.95)',
        'btn_bg': 'linear-gradient(135deg, #00d4d4, #008080)', 'btn_color': '#001428',
        'rgba_accent': 'rgba(0, 212, 212,', 'rgba_success': 'rgba(0, 255, 159,',
        'rgba_danger': 'rgba(255, 107, 107,', 'badge_bg': 'rgba(0,212,212,0.1)',
        'badge_color': '#00d4d4', 'badge_border': '1px solid rgba(0,212,212,0.25)',
        'subtitle_color': 'rgba(224, 247, 250, 0.8)',
        'animation_name': 'oceanWave', 'animation_particles': 'rgba(0, 212, 212, 0.08)',
        'shadow_opacity': '3',
    },
    'S': {
        'name': 'Sunset',
        'body_bg': '#f5f6fa', 'text': '#2d3436', 'card_bg': '#ffffff',
        'card_border': '#dfe6e9', 'input_bg': '#ffffff', 'accent': '#6c5ce7',
        'success': '#00b894', 'danger': '#e84393', 'warning': '#fdcb6e',
        'text_dim': '#636e72', 'nav_inactive': '#b2bec3', 'nav_active': '#6c5ce7',
        'login_bg': 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 40%, #6c5ce7 100%)',
        'login_card_bg': 'rgba(255, 255, 255, 0.95)',
        'login_card_border': '1px solid rgba(255, 255, 255, 0.5)',
        'login_card_shadow': '0 20px 60px rgba(0,0,0,0.12), 0 0 40px rgba(255, 107, 107, 0.1)',
        'login_logo_color': '#ffffff',
        'login_logo_shadow': '0 2px 15px rgba(0,0,0,0.15)',
        'login_btn_bg': 'linear-gradient(135deg, #6c5ce7, #5849be)',
        'login_btn_color': '#ffffff',
        'header_bg': 'rgba(255, 255, 255, 0.95)', 'header_border': '1px solid rgba(0,0,0,0.05)',
        'wallet_bg': 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #6c5ce7 100%)',
        'wallet_border': 'none',
        'wallet_balance_color': '#ffffff',
        'wallet_balance_shadow': '0 2px 10px rgba(0,0,0,0.1)',
        'fund_btn_bg': '#ffffff', 'fund_btn_color': '#6c5ce7',
        'nav_bg': 'rgba(255, 255, 255, 0.95)',
        'btn_bg': 'linear-gradient(135deg, #6c5ce7, #5849be)', 'btn_color': '#ffffff',
        'rgba_accent': 'rgba(108, 92, 231,', 'rgba_success': 'rgba(0, 184, 148,',
        'rgba_danger': 'rgba(232, 67, 147,', 'badge_bg': 'rgba(255,255,255,0.15)',
        'badge_color': '#ffffff', 'badge_border': '1px solid rgba(255,255,255,0.25)',
        'subtitle_color': 'rgba(255,255,255,0.8)',
        'animation_name': 'sunsetPulse', 'animation_particles': 'rgba(255, 107, 107, 0.1)',
        'shadow_opacity': '06',
    },
}

if choice not in themes:
    print("Invalid choice. Run again and enter A, B, C, or S.")
    exit()

t = themes[choice]
print(f"\n  Applying {t['name']} theme...")

# === STEP 1: Restore from clean backup ===
backups = ['tenant_portal.html.bak_brand', 'tenant_portal.html.bak_demo']
restored = False
for bak in backups:
    if os.path.exists(bak):
        shutil.copy(bak, 'tenant_portal.html')
        print(f"  Restored from: {bak}")
        restored = True
        break
if not restored:
    print("  No clean backup. Working with current file.")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# === STEP 2: Replace :root ===
root_css = f""":root {{
            --bg: {t['body_bg']}; --card-bg: {t['card_bg']}; --card-border: {t['card_border']};
            --text: {t['text']}; --text-dim: {t['text_dim']}; --accent: {t['accent']};
            --accent-glow: {t['rgba_accent']} 0.3); --success: {t['success']};
            --danger: {t['danger']}; --warning: {t['warning']}; --primary: {t['body_bg']};
            --secondary: {t['accent']}; --gray: {t['text_dim']}; --light: {t['card_bg']}; --dark: {t['body_bg']};
        }}"""
c = re.sub(r':root\s*\{[^}]*\}', root_css, c, count=1)
print("  Set :root variables.")

# === STEP 3: Comprehensive color replacement ===
all_colors = {
    '#2c3e50': t['body_bg'], '#3498db': t['accent'], '#27ae60': t['success'],
    '#e74c3c': t['danger'], '#f39c12': t['warning'], '#ecf0f1': t['card_bg'],
    '#7f8c8d': t['text_dim'], '#f4f7f6': t['body_bg'], '#1c1c1e': t['text'],
    '#f8f9fa': t['card_bg'], '#f1f1f1': t['card_border'], '#eee': t['card_border'],
    '#ccc': t['card_border'], '#ddd': t['card_border'], '#aaa': '#b2bec3',
    '#1abc9c': t['accent'], '#e8f8f5': t['card_bg'], '#003366': t['text'],
    '#0d1117': t['body_bg'], '#161b22': t['card_bg'], '#30363d': t['card_border'],
    '#00d4ff': t['accent'], '#00ff88': t['success'], '#ff4757': t['danger'],
    '#e6edf3': t['text'], '#8b949e': t['text_dim'], '#6e7681': '#b2bec3',
    '#0099cc': t['accent'], '#001428': t['body_bg'], '#001f3f': t['card_bg'],
    '#003d5c': t['card_border'], '#00d4d4': t['accent'], '#00ff9f': t['success'],
    '#ff6b6b': t['danger'], '#e0f7fa': t['text'], '#5c7a89': t['text_dim'],
    '#008080': t['accent'], '#000a14': t['input_bg'], '#051910': t['body_bg'],
    '#0a2e1f': t['body_bg'], '#0f3d2a': t['card_bg'], '#1a5e3a': t['card_border'],
    '#d4af37': t['accent'], '#2ecc71': t['success'], '#e8f5e9': t['text'],
    '#7a9b87': t['text_dim'], '#b8941f': t['accent'], '#061d12': t['input_bg'],
    '#f5f6fa': t['body_bg'], '#dfe6e9': t['card_border'], '#6c5ce7': t['accent'],
    '#00b894': t['success'], '#e84393': t['danger'], '#fdcb6e': t['warning'],
    '#2d3436': t['text'], '#636e72': t['text_dim'], '#5849be': t['accent'],
    '#ffa502': t['warning'], '#ff9502': t['warning'],
}
for old, new in all_colors.items():
    if old != new:
        c = c.replace(old, new)
print("  Replaced all hex colors.")

# === STEP 4: Replace rgba ===
all_rgba = {
    'rgba(0, 212, 255,': t['rgba_accent'], 'rgba(0, 212, 212,': t['rgba_accent'],
    'rgba(212, 175, 55,': t['rgba_accent'], 'rgba(52, 152, 219,': t['rgba_accent'],
    'rgba(25, 118, 210,': t['rgba_accent'], 'rgba(108, 92, 231,': t['rgba_accent'],
    'rgba(0, 255, 136,': t['rgba_success'], 'rgba(0, 255, 159,': t['rgba_success'],
    'rgba(46, 204, 113,': t['rgba_success'], 'rgba(255, 71, 87,': t['rgba_danger'],
    'rgba(255, 107, 107,': t['rgba_danger'], 'rgba(231, 76, 60,': t['rgba_danger'],
    'rgba(232, 67, 147,': t['rgba_danger'], 'rgba(44, 62, 80,': 'rgba(45, 52, 54,',
    'rgba(10, 37, 64,': 'rgba(0, 0, 0,', 'rgba(10, 46, 31,': t['header_bg'].replace('0.95','').replace('rgba(','rgba(') if 'rgba' in t['header_bg'] else 'rgba(255, 255, 255,',
    'rgba(0, 20, 40,': 'rgba(255, 255, 255,' if t['body_bg'] == '#f5f6fa' else t['header_bg'].replace('0.95',''),
    'rgba(13, 17, 23,': 'rgba(255, 255, 255,' if t['body_bg'] == '#f5f6fa' else 'rgba(255, 255, 255,',
    'rgba(22, 27, 34,': 'rgba(255, 255, 255,' if t['body_bg'] == '#f5f6fa' else 'rgba(255, 255, 255,',
    'rgba(15, 61, 42,': 'rgba(255, 255, 255,' if t['body_bg'] == '#f5f6fa' else 'rgba(255, 255, 255,',
    'rgba(0, 31, 63,': 'rgba(255, 255, 255,' if t['body_bg'] == '#f5f6fa' else 'rgba(255, 255, 255,',
}
for old, new in all_rgba.items():
    c = c.replace(old, new)
print("  Replaced all rgba colors.")

# === STEP 5: Fix CSS rules ===
sh = t['shadow_opacity']

# Body
c = re.sub(r'body\s*\{[^}]*background-color:[^;]*;', f'body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: {t["body_bg"]};', c, count=1)

# Login screen
c = re.sub(r'\.login-screen\s*\{[^}]*background:[^;]*;', f'.login-screen {{ display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: {t["login_bg"]};', c)

# Login logo
c = re.sub(r'\.login-logo\s*\{[^}]*\}', f'.login-logo {{ font-size: 3em; font-weight: 900; margin-bottom: 5px; letter-spacing: 6px; text-align: center; color: {t["login_logo_color"]}; text-shadow: {t["login_logo_shadow"]}; }}', c)

# Login card
c = re.sub(r'\.login-card\s*\{[^}]*\}', f'.login-card {{ background: {t["login_card_bg"]}; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 30px; border-radius: 16px; width: 100%; max-width: 350px; border: {t["login_card_border"]}; box-shadow: {t["login_card_shadow"]}; }}', c)

# Login h2
c = re.sub(r'\.login-card h2\s*\{[^}]*\}', f'.login-card h2 {{ text-align: center; color: {t["text"]}; margin-top: 0; margin-bottom: 20px; font-weight: 700; }}', c)

# Login inputs
c = re.sub(r'\.login-card input[^}]*\}', f'.login-card input, .login-card select {{ width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid {t["card_border"]}; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: {t["input_bg"]}; color: {t["text"]}; transition: border-color 0.3s, box-shadow 0.3s; }}', c)

# Login button
c = re.sub(r'\.login-card button\s*\{[^}]*\}', f'.login-card button {{ width: 100%; padding: 15px; background: {t["login_btn_bg"]}; color: {t["login_btn_color"]}; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 25px {t["rgba_accent"]} 0.35); transition: all 0.3s; }}', c)

# Header
c = re.sub(r'\.app-header\s*\{[^}]*\}', f'.app-header {{ background: {t["header_bg"]}; backdrop-filter: blur(10px); color: {t["text"]}; padding: 15px 20px; text-align: center; font-size: 1.1em; font-weight: bold; position: sticky; top: 0; z-index: 100; border-bottom: {t["header_border"]}; box-shadow: 0 2px 10px rgba(0,0,0,0.0{"3" if sh == "3" else "3"}); display: flex; justify-content: space-between; align-items: center; }}', c)

# Cards
c = re.sub(r'\.card\s*\{[^}]*\}', f'.card {{ background: {t["card_bg"]}; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid {t["card_border"]}; box-shadow: 0 4px 20px rgba(0,0,0,0.{sh}); transition: border-color 0.3s, box-shadow 0.3s; }}', c)
c = re.sub(r'\.card:hover\s*\{[^}]*\}', f'.card:hover {{ border-color: {t["rgba_accent"]} 0.3); box-shadow: 0 8px 30px {t["rgba_accent"]} 0.08); }}', c)
c = re.sub(r'\.card h3\s*\{[^}]*\}', f'.card h3 {{ margin: 0 0 15px 0; color: {t["text"]}; font-size: 1.1em; border-bottom: 1px solid {t["card_border"]}; padding-bottom: 10px; font-weight: 700; }}', c)

# Wallet card
c = re.sub(r'\.wallet-card\s*\{[^}]*\}', f'.wallet-card {{ background: {t["wallet_bg"]}; border: {t["wallet_border"]}; color: #ffffff; padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.{"1" if t["body_bg"] == "#f5f6fa" else "4"}); }}', c)
c = re.sub(r'\.wallet-balance\s*\{[^}]*\}', f'.wallet-balance {{ font-size: 3em; font-weight: 800; margin-bottom: 5px; color: {t["wallet_balance_color"]}; text-shadow: {t["wallet_balance_shadow"]}; }}', c)
c = re.sub(r'\.btn-fund\s*\{[^}]*\}', f'.btn-fund {{ background: {t["fund_btn_bg"]}; color: {t["fund_btn_color"]}; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.3s; }}', c)

# Bottom nav — KEY FIX: nav_inactive for text color
c = re.sub(r'\.bottom-nav\s*\{[^}]*\}', f'.bottom-nav {{ position: fixed; bottom: 0; left: 0; width: 100%; background: {t["nav_bg"]}; backdrop-filter: blur(10px); border-top: 1px solid {t["card_border"]}; box-shadow: 0 -4px 20px rgba(0,0,0,0.{sh}); display: flex; justify-content: space-around; padding: 8px 0; z-index: 100; }}', c)
c = re.sub(r'\.nav-btn\s*\{[^}]*\}', f'.nav-btn {{ background: none; border: none; color: {t["nav_inactive"]}; font-size: 0.65em; display: flex; flex-direction: column; align-items: center; cursor: pointer; padding: 5px; width: 100%; }}', c)
c = re.sub(r'\.nav-btn\.active\s*\{[^}]*\}', f'.nav-btn.active {{ color: {t["nav_active"]}; font-weight: bold; }}', c)

# General inputs
c = re.sub(r'^input, select\s*\{[^}]*\}', f'input, select {{ width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid {t["card_border"]}; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: {t["input_bg"]}; color: {t["text"]}; }}', c, count=1, flags=re.MULTILINE)

# General buttons
c = re.sub(r'^button\s*\{[^}]*\}', f'button {{ width: 100%; padding: 12px; background: {t["btn_bg"]}; color: {t["btn_color"]}; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }}', c, count=1, flags=re.MULTILINE)

# Other elements
c = re.sub(r'\.kpi-card\s*\{[^}]*\}', f'.kpi-card {{ background: {t["card_bg"]}; border-radius: 12px; padding: 15px; border: 1px solid {t["card_border"]}; text-align: center; }}', c)
c = re.sub(r'\.credit-card\s*\{[^}]*\}', f'.credit-card {{ background: {t["card_bg"]}; border: 2px dashed {t["rgba_accent"]} 0.2); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }}', c)
c = re.sub(r'\.utility-card\s*\{[^}]*\}', f'.utility-card {{ display: flex; flex-direction: column; align-items: center; margin-bottom: 15px; padding: 15px; border-radius: 10px; background: {t["input_bg"]}; border: 1px solid {t["card_border"]}; }}', c)
c = re.sub(r'\.force-change-screen\s*\{[^}]*\}', f'.force-change-screen {{ display: none; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: {t["login_bg"]}; color: white; padding: 20px; box-sizing: border-box; }}', c)
c = re.sub(r'\.change-pw-content\s*\{[^}]*\}', f'.change-pw-content {{ background: {t["card_bg"]}; margin: 20px; border-radius: 16px; padding: 30px; margin-top: 60px; max-width: 400px; margin-left: auto; margin-right: auto; border: 1px solid {t["card_border"]}; box-shadow: 0 20px 60px rgba(0,0,0,0.{"15" if t["body_bg"] == "#f5f6fa" else "5"}); }}', c)
c = re.sub(r'\.btn-token\s*\{[^}]*\}', f'.btn-token {{ background: {t["rgba_accent"]} 0.1); color: {t["accent"]}; border: 1px solid {t["rgba_accent"]} 0.25); padding: 5px 10px; font-size: 0.75em; width: auto; border-radius: 4px; cursor: pointer; }}', c)

# Scrollbar
c = re.sub(r'::-webkit-scrollbar-track\s*\{[^}]*\}', f'::-webkit-scrollbar-track {{ background: {t["body_bg"]}; }}', c)
c = re.sub(r'::-webkit-scrollbar-thumb\s*\{[^}]*\}', f'::-webkit-scrollbar-thumb {{ background: {t["accent"]}; border-radius: 3px; }}', c)

# B-BBEE badge
if 'Level 1 B-BBEE' in c:
    c = re.sub(r'background:rgba\([^)]*\); color:[^;]*; border:1px solid rgba\([^)]*\);',
        f'background:{t["badge_bg"]}; color:{t["badge_color"]}; border:{t["badge_border"]};', c)

# Subtitle
if 'SERVICES' in c:
    c = re.sub(r'color:[^;]*; font-size: 0\.8em; letter-spacing: 3px; margin-bottom: 20px[^>]*>SERVICES',
        f'color: {t["subtitle_color"]}; font-size: 0.8em; letter-spacing: 3px; margin-bottom: 20px;">SERVICES', c)

# Animation
for old_anim in ['oceanWave', 'emeraldGlow', 'sunsetPulse', 'darkGlow']:
    c = c.replace('@keyframes ' + old_anim, '@keyframes ' + t['animation_name'])
    c = c.replace('animation: ' + old_anim, 'animation: ' + t['animation_name'])

print("  Fixed all CSS rules.")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print(f"\n{'='*50}")
print(f"  {t['name'].upper()} THEME APPLIED!")
print(f"{'='*50}")
print(f"\n  Nav text color (inactive): {t['nav_inactive']}")
print(f"  Nav text color (active):   {t['nav_active']}")
print(f"\n  Test: http://127.0.0.1:8000/tenant (Ctrl+F5)")
print(f"  If cached: F12 → Console → localStorage.clear() → F5")
print(f"\n  Run again to switch: A, B, C, or S")