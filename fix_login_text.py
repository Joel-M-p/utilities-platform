print("Updating login message...")

with open('tenant_portal.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace whatever is there with the simple text
import re

# Find the paragraph with the forgot password link and replace it
c = re.sub(
    r'<a href="#" onclick="tShowForgotPassword\(\)"[^>]*>[^<]*</a>\s*(\|\s*&nbsp;\s*)?<a[^>]*>[^<]*</a>',
    '<a href="#" onclick="tShowForgotPassword()" style="color:#00d4ff; text-decoration:none; font-size:0.9em;">New Password</a> / <a href="#" onclick="tShowForgotPassword()" style="color:#8b949e; text-decoration:none; font-size:0.9em;">Forgot Password</a>',
    c
)

# Also try simpler replacement if regex didn't match
if 'New Password</a>' not in c:
    c = c.replace(
        'First time? Set up your password',
        'New Password'
    )
    # Clean up any leftover
    c = c.replace('&nbsp;|&nbsp;', ' / ')

# Final check — if still not there, find and replace the whole paragraph
if 'New Password</a>' not in c:
    # Find the old forgot password link and replace
    old_patterns = [
        '<a href="#" onclick="tShowForgotPassword()" style="color:#00d4ff; text-decoration:none; font-size:0.9em;">Forgot Password?</a>',
        '<a href="#" onclick="tShowForgotPassword()" style="color:var(--secondary); text-decoration:none; font-size:0.9em;">Forgot Password?</a>',
        '<a href="#" onclick="tShowForgotPassword()" style="color:#3498db; text-decoration:none; font-size:0.9em;">Forgot Password?</a>',
    ]
    new_link = '<a href="#" onclick="tShowForgotPassword()" style="color:#00d4ff; text-decoration:none; font-size:0.9em;">New Password</a> / <a href="#" onclick="tShowForgotPassword()" style="color:#8b949e; text-decoration:none; font-size:0.9em;">Forgot Password</a>'
    
    for old in old_patterns:
        if old in c:
            c = c.replace(old, new_link)
            break

with open('tenant_portal.html', 'w', encoding='utf-8') as f:
    f.write(c)

if 'New Password</a>' in c:
    print("Done! Login screen now shows: New Password / Forgot Password")
else:
    print("WARNING: Could not find the link. Paste the line with 'Forgot Password' from tenant_portal.html")