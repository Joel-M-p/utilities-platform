print("Fixing login link text...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace ALL variations of the forgot password link text
replacements = [
    ('First time? Set up your password</a> &nbsp;|&nbsp; <a href="#" onclick="tShowForgotPassword()" style="color:#8b949e; text-decoration:none; font-size:0.9em;">Forgot Password?</a>', 
     '<a href="#" onclick="tShowForgotPassword()" style="color:#d4af37; text-decoration:none; font-size:0.9em; font-weight:600;">New Password / Forgot Password</a>'),
    ('First time? Set up your password</a> / <a href="#" onclick="tShowForgotPassword()" style="color:#8b949e; text-decoration:none; font-size:0.9em;">Forgot Password</a>',
     '<a href="#" onclick="tShowForgotPassword()" style="color:#d4af37; text-decoration:none; font-size:0.9em; font-weight:600;">New Password / Forgot Password</a>'),
    ('New Password</a> / <a href="#" onclick="tShowForgotPassword()" style="color:#8b949e; text-decoration:none; font-size:0.9em;">Forgot Password</a>',
     '<a href="#" onclick="tShowForgotPassword()" style="color:#d4af37; text-decoration:none; font-size:0.9em; font-weight:600;">New Password / Forgot Password</a>'),
    ('Forgot Password?</a>',
     'New Password / Forgot Password</a>'),
    ('Forgot Password</a>',
     'New Password / Forgot Password</a>'),
]

for old, new in replacements:
    if old in c:
        c = c.replace(old, new, 1)
        print("  Replaced: " + old[:40] + "...")
        break

# Verify the change
if 'New Password / Forgot Password</a>' in c:
    print("\nDone! Link text is now: New Password / Forgot Password")
else:
    print("\nWARNING: Could not find link text to replace.")
    print("Searching for onclick='tShowForgotPassword'...")
    # Find the line with the link
    lines = c.split('\n')
    for i, line in enumerate(lines, 1):
        if 'tShowForgotPassword' in line and 'onclick' in line and 'function' not in line:
            print(f"  Line {i}: {line.strip()[:150]}")

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nTest: Ctrl+F5 on tenant portal")