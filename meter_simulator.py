import requests
import time
import random

API_URL = "http://127.0.0.1:8000"
TENANT_ID = 1  # Make sure this tenant exists!

print("="*50)
print("🔌 SMART METER SIMULATOR STARTED")
print(f"Monitoring Tenant ID: {TENANT_ID}")
print("Sending raw UNITS USED (kWh/kL) every 15 seconds...")
print("Keep this window open!")
print("="*50)

try:
    login_res = requests.post(f"{API_URL}/login/", json={"username": "admin", "password": "password123"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
except Exception as e:
    print("Failed to login to API. Make sure your API server is running!")
    exit()

while True:
    try:
        # Send Electricity Usage (e.g., 1.5 kWh used)
        elec_usage = round(random.uniform(1.0, 5.0), 2)
        print(f"\n⚡ Electricity Meter: {elec_usage} kWh used. Sending to API...")
        res1 = requests.post(
            f"{API_URL}/generate-bill/", 
            json={"tenant_id": TENANT_ID, "utility_type": "ELECTRICITY", "amount": elec_usage},
            headers=headers
        )
        if res1.status_code == 200:
            print(f"✅ API calculated cost and processed electricity!")
        else:
            print(f"❌ API Error: {res1.text}")
            
        # Send Water Usage (e.g., 0.5 kL used)
        water_usage = round(random.uniform(0.1, 1.5), 2)
        print(f"💧 Water Meter: {water_usage} kL used. Sending to API...")
        res2 = requests.post(
            f"{API_URL}/generate-bill/", 
            json={"tenant_id": TENANT_ID, "utility_type": "WATER", "amount": water_usage},
            headers=headers
        )
        if res2.status_code == 200:
            print(f"✅ API calculated cost and processed water!")
        else:
            print(f"❌ API Error: {res2.text}")
            
        time.sleep(15)
        
    except KeyboardInterrupt:
        print("\nMeter simulator stopped.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)