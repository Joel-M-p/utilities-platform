import requests
import time

# --- PASTE YOUR RENDER URL HERE ---
BASE_URL = "https://utilities-platform.onrender.com" # <-- CHANGE THIS IF NEEDED
# ----------------------------------

PM_USERNAME = "admin"
PM_PASSWORD = "password123"

def main():
    print(f"Connecting to {BASE_URL}...")
    print("(If Render is asleep, this may take up to 60 seconds to wake it up...)")
    
    # 0. Initialize Database Tables (Fixes the "invoices does not exist" error)
    try:
        print("\nSetting up database tables...")
        r = requests.get(f"{BASE_URL}/setup", timeout=90)
        if r.status_code == 200:
            print("  -> Database tables verified/created successfully!")
        else:
            print(f"  -> Setup returned status {r.status_code}: {r.text}")
    except Exception as e:
        print(f"  -> Could not hit /setup endpoint: {e}")

    # 1. Login to get Token
    try:
        print("\nLogging in...")
        r = requests.post(f"{BASE_URL}/login/", json={"username": PM_USERNAME, "password": PM_PASSWORD}, timeout=90)
        r.raise_for_status()
        token = r.json().get("token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("  -> Login successful!")
    except Exception as e:
        print(f"Failed to login: {e}")
        return

    # Use the exact fields your backend expects (utility_outstanding)
    tenants = [
        {"first_name": "James", "last_name": "Bond", "email": "james@bond.com", "rent_outstanding": 5000, "utility_outstanding": 1200},
        {"first_name": "John", "last_name": "Doe", "email": "john@doe.com", "rent_outstanding": 0, "utility_outstanding": 0},
        {"first_name": "Sarah", "last_name": "Connor", "email": "sarah@sky.net", "rent_outstanding": 2500, "utility_outstanding": 300},
        {"first_name": "Peter", "last_name": "Parker", "email": "peter@parker.com", "rent_outstanding": 1000, "utility_outstanding": 150},
        {"first_name": "Bruce", "last_name": "Wayne", "email": "bruce@wayne.com", "rent_outstanding": 0, "utility_outstanding": 0}
    ]

    tenant_ids = []

    # 2. Create Tenants
    print("\nCreating Tenants...")
    for t in tenants:
        try:
            r = requests.post(f"{BASE_URL}/create-tenant/", headers=headers, json=t, timeout=30)
            if r.status_code == 200:
                data = r.json()
                tid = data.get("tenant_id") or data.get("id")
                if tid:
                    tenant_ids.append(tid)
                    print(f"  -> Created {t['first_name']} {t['last_name']} (ID: {tid})")
                else:
                    print(f"  -> Created {t['first_name']} but couldn't parse ID: {data}")
            else:
                print(f"  -> Failed to create {t['first_name']}: {r.text}")
        except Exception as e:
            print(f"  -> Error creating {t['first_name']}: {e}")
        time.sleep(1) # Be nice to Render free tier

    # 3. Generate Bills & Invoices
    if tenant_ids:
        print("\nGenerating Bills and Invoices...")
        for i, tid in enumerate(tenant_ids):
            period = f"2024-0{(i % 9) + 1}" # Cycles through months 2024-01 to 2024-09
            
            # Generate Bill (Fixed payload to match your backend)
            try:
                bill_payload = {
                    "tenant_id": tid, 
                    "utility_type": "ELECTRICITY", 
                    "amount": 450.75, 
                    "manual_entry": True
                }
                r = requests.post(f"{BASE_URL}/generate-bill/", headers=headers, json=bill_payload, timeout=30)
                if r.status_code == 200:
                    print(f"  -> Bill generated for Tenant {tid}")
                else:
                    print(f"  -> Failed to generate bill for {tid}: {r.text}")
            except Exception as e:
                print(f"  -> Error generating bill: {e}")
            
            time.sleep(1)

            # Generate Invoice
            try:
                inv_payload = {"tenant_id": tid, "billing_period": period, "cycle_type": "MONTHLY"}
                r = requests.post(f"{BASE_URL}/generate-invoice/", headers=headers, json=inv_payload, timeout=30)
                if r.status_code == 200:
                    print(f"  -> Invoice generated for Tenant {tid} ({period})")
                else:
                    print(f"  -> Failed to generate invoice for {tid}: {r.text}")
            except Exception as e:
                print(f"  -> Error generating invoice: {e}")
            
            time.sleep(1)

        # 4. Process a Payment for the first tenant
        if len(tenant_ids) > 0:
            print("\nProcessing a Test Payment...")
            try:
                pay_payload = {"tenant_id": tenant_ids[0], "amount": 1500.00}
                r = requests.post(f"{BASE_URL}/process-payment/", headers=headers, json=pay_payload, timeout=30)
                if r.status_code == 200:
                    print(f"  -> Payment of R1500.00 processed for Tenant {tenant_ids[0]}")
                else:
                    print(f"  -> Failed to process payment: {r.text}")
            except Exception as e:
                print(f"  -> Error processing payment: {e}")

    print("\nDone! Go check your Render dashboard or mobile app.")

if __name__ == "__main__":
    main()