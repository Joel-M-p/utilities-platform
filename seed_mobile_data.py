import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# --- CHANGE THESE TO MATCH YOUR api/security.py ---
PM_USERNAME = "admin"        
PM_PASSWORD = "password123"  
# --------------------------------------------------

def main():
    print("Logging in to get token...")
    r = requests.post(f"{BASE_URL}/login/", json={"username": PM_USERNAME, "password": PM_PASSWORD})
    if r.status_code != 200:
        print("Failed to login. Please check PM_USERNAME and PM_PASSWORD in the script.")
        print(r.text)
        return
    
    token = r.json().get("token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Login successful!")

    # Simplified tenant data to avoid database column errors
    tenants = [
        {"first_name": "James", "last_name": "Bond", "email": "james@bond.com"},
        {"first_name": "John", "last_name": "Doe", "email": "john@doe.com"},
        {"first_name": "Sarah", "last_name": "Connor", "email": "sarah@sky.net"},
        {"first_name": "Peter", "last_name": "Parker", "email": "peter@parker.com"},
        {"first_name": "Bruce", "last_name": "Wayne", "email": "bruce@wayne.com"}
    ]

    tenant_ids = []
    print("\nCreating Tenants...")
    for t in tenants:
        r = requests.post(f"{BASE_URL}/create-tenant/", headers=headers, json=t)
        if r.status_code == 200:
            data = r.json()
            # Try to extract the tenant ID from the response
            tid = data.get("tenant_id") or data.get("id") 
            if tid:
                tenant_ids.append(tid)
                print(f"  - Created {t['first_name']} {t['last_name']} (ID: {tid})")
            else:
                print(f"  - Created {t['first_name']} (Couldn't parse ID from response: {data})")
        else:
            print(f"  - Failed to create {t['first_name']}: {r.text}")
        time.sleep(0.5)

    # Generate Invoices
    if tenant_ids:
        print("\nGenerating Invoices...")
        for i, tid in enumerate(tenant_ids):
            period = f"2024-0{i+1}" # Creates periods like 2024-01, 2024-02, etc.
            payload = {"tenant_id": tid, "billing_period": period, "cycle_type": "MONTHLY"}
            r = requests.post(f"{BASE_URL}/generate-invoice/", headers=headers, json=payload)
            if r.status_code == 200:
                print(f"  - Invoice generated for Tenant ID {tid}")
            else:
                print(f"  - Failed to generate invoice for {tid}: {r.text}")
            time.sleep(0.5)

        # Process a Payment for the first tenant to test partial payments
        print("\nProcessing a Test Payment...")
        payload = {"tenant_id": tenant_ids[0], "amount": 150.00}
        r = requests.post(f"{BASE_URL}/process-payment/", headers=headers, json=payload)
        if r.status_code == 200:
            print(f"  - Payment of R150.00 processed for Tenant ID {tenant_ids[0]}")
        else:
            print(f"  - Failed to process payment: {r.text}")

    print("\nDone! Go check your mobile app.")

if __name__ == "__main__":
    main()