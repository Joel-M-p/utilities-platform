import shutil

print("Adding /setup-all endpoint to api/main.py...")

shutil.copy('api/main.py', 'api/main.py.bak')

with open('api/main.py', 'r', encoding='utf-8') as f:
    c = f.read()

if 'setup-all' in c:
    print("  Endpoint already exists. Skipping.")
else:
    endpoint = '''

@app.get("/setup-all")
def setup_all():
    """Run this ONCE after deploying to set up database and generate temp passwords."""
    from api.database import get_db_connection
    from api.services.passwords import hash_password, generate_temp_password
    from fastapi.responses import HTMLResponse
    
    results = []
    temp_passwords = []
    
    # Step 1: Initialize database tables
    try:
        from api.models import init_db
        init_db()
        results.append("Database tables created/updated")
    except Exception as e:
        results.append("Database init error: " + str(e))
    
    # Step 2: Add user password columns + meter_readings table
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP;")
        cursor.execute("UPDATE users SET must_change_password = TRUE WHERE username = 'admin';")
        cursor.execute("UPDATE users SET email = 'admin@elups.co.za' WHERE username = 'admin' AND (email IS NULL OR email = '');")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings (
                id SERIAL PRIMARY KEY,
                meter_id INTEGER,
                tenant_id INTEGER,
                property_id INTEGER,
                meter_type VARCHAR(50),
                serial_number VARCHAR(255),
                reading_value DECIMAL,
                previous_reading DECIMAL DEFAULT 0,
                consumption DECIMAL,
                rate DECIMAL,
                amount DECIMAL,
                reading_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recorded_by VARCHAR(50)
            );
        """)
        
        conn.commit()
        results.append("User password columns added (email, must_change_password)")
        results.append("Meter readings table created")
        results.append("Admin set to must_change_password = TRUE")
        
        # Step 3: Generate temp passwords for tenants
        cursor.execute("SELECT id, first_name, last_name, unit_number FROM tenants WHERE password_hash IS NULL OR password_hash = ''")
        tenants = cursor.fetchall()
        
        for t in tenants:
            tenant_id = t[0]
            name = (t[1] or '') + ' ' + (t[2] or '')
            unit = t[3] or 'N/A'
            
            temp_pw = generate_temp_password()
            hashed = hash_password(temp_pw)
            
            cursor.execute("UPDATE tenants SET password_hash = %s, must_change_password = TRUE WHERE id = %s", (hashed, tenant_id))
            conn.commit()
            
            temp_passwords.append({
                "tenant_id": tenant_id,
                "name": name.strip(),
                "unit": unit,
                "temp_password": temp_pw
            })
        
        if temp_passwords:
            results.append("Generated temp passwords for " + str(len(temp_passwords)) + " tenant(s)")
        else:
            results.append("All tenants already have passwords")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        results.append("Password setup error: " + str(e))
    
    # Return as nice HTML page (easy to read in browser)
    html = "<html><head><title>Setup Results</title><style>"
    html += "body { font-family: Arial; background: #f4f7f6; padding: 30px; }"
    html += "h1 { color: #2c3e50; }"
    html += ".result { background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #27ae60; }"
    html += ".pw-card { background: #e8f8f5; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #1abc9c; }"
    html += ".pw { font-size: 1.4em; font-weight: bold; color: #2c3e50; font-family: monospace; }"
    html += ".label { color: #7f8c8d; font-size: 0.85em; }"
    html += ".instructions { background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #f39c12; }"
    html += "</style></head><body>"
    
    html += "<h1>Setup Complete!</h1>"
    
    html += "<h2>Results:</h2>"
    for r in results:
        html += '<div class="result">' + r + '</div>'
    
    if temp_passwords:
        html += "<h2>Tenant Temp Passwords (WRITE THESE DOWN):</h2>"
        for tp in temp_passwords:
            html += '<div class="pw-card">'
            html += '<div class="label">Unit: ' + tp["unit"] + ' | Tenant: ' + tp["name"] + ' (ID: ' + str(tp["tenant_id"]) + ')</div>'
            html += '<div class="pw">' + tp["temp_password"] + '</div>'
            html += '</div>'
    
    html += '<div class="instructions">'
    html += '<h3>Next Steps:</h3>'
    html += '<p><strong>Admin:</strong> Visit <a href="/dashboard">/dashboard</a> - Login: admin / password123 - You will be forced to set a new password</p>'
    html += '<p><strong>Tenant:</strong> Visit <a href="/tenant">/tenant</a> - Select property, enter Unit Number, enter the temp password above - Tenant will be forced to set their own password</p>'
    html += '</div>'
    
    html += "</body></html>"
    
    return HTMLResponse(content=html)

'''
    
    c = c + endpoint
    print("  Added /setup-all endpoint.")

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Now:")
print("  1. Commit and push to GitHub")
print("  2. Wait for Render to rebuild (5-10 min)")
print("  3. Visit: https://utilities-platform.onrender.com/setup-all")
print("  4. You'll see all setup results + temp passwords on screen")