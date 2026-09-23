print("Making month compulsory in reconciliation...")

# === FIX BACKEND (recon.py) ===
with open('api/routers/recon.py', 'r', encoding='utf-8') as f:
    c = f.read()

if 'Month is required' not in c:
    c = c.replace(
        "month = payload.get(\"month\")",
        "month = payload.get(\"month\")\n        if not month:\n            raise HTTPException(status_code=400, detail=\"Month is required. Please enter the billing month (e.g., 2026-09).\")"
    )
    with open('api/routers/recon.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("  Fixed backend: month is now required.")
else:
    print("  Backend already fixed.")

# === FIX FRONTEND (dashboard.html) ===
with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Change input type to month picker for better UX
if 'type="text" id="reconMonth"' in c:
    c = c.replace(
        '<input type="text" id="reconMonth" placeholder="Month">',
        '<input type="month" id="reconMonth" placeholder="Month">'
    )
    print("  Fixed frontend: month input is now a date picker.")

# Add validation in runRecon function
if 'Please enter a month' not in c:
    # Find runRecon function and add validation
    old = 'const payload = {\n            month: document.getElementById("reconMonth").value,\n            utility_type: document.getElementById("reconType").value,'
    new = 'var reconMonth = document.getElementById("reconMonth").value;\n        if(!reconMonth) {\n            document.getElementById("reconResult").style.display = "block";\n            document.getElementById("reconResult").innerHTML = "<p style=\'color:red;\'>Please select a month.</p>";\n            return;\n        }\n        const payload = {\n            month: reconMonth,\n            utility_type: document.getElementById("reconType").value,'
    
    if old in c:
        c = c.replace(old, new)
        print("  Fixed frontend: month validation added.")
    else:
        # Try alternative format
        old2 = "month: document.getElementById('reconMonth').value,"
        new2 = "month: document.getElementById('reconMonth').value,"
        # Just add validation before the payload
        c = c.replace(
            "const payload = {",
            "var reconMonth = document.getElementById('reconMonth').value;\n        if(!reconMonth) { alert('Please select a month.'); return; }\n        const payload = {",
            1
        )
        print("  Fixed frontend: month validation added (alternative).")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart server and test.")
print("  1. Try running reconciliation WITHOUT a month → should show error")
print("  2. Select a month → should save successfully")