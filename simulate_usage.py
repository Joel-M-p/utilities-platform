import json
import urllib.request
import random

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data is not None:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(f"{BASE_URL}{url}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        return 0, {"error": str(e)}

print("Logging in...")
# Using your exact credentials
status, login_data = make_request("/api/auth/login", method="POST", data={"email": "admin", "password": "password123"})

if status != 200:
    print(f"❌ Login failed (Status {status}):", login_data)
    if status == 422:
        print("\n💡 Hint: The backend expects a valid email format. You might need to use 'admin@elups.com' instead of just 'admin', or change 'EmailStr' to 'str' in api/routers/auth.py.")
    exit()
    
token = login_data.get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful!\n")

print("Fetching tenants...")
status, tenants_data = make_request("/all-tenants/", headers=headers)

if status != 200:
    print(f"❌ Failed to fetch tenants (Status {status}):", tenants_data)
    exit()

tenants = tenants_data.get("tenants", [])
if len(tenants) == 0:
    print("❌ No tenants found. Please create a tenant in the dashboard first.")
    exit()

print(f"Found {len(tenants)} tenants. Simulating utility usage...\n")

for tenant in tenants:
    tenant_id = tenant["tenant_id"]
    usage_amount = round(random.uniform(50, 200), 2)
    
    payload = {
        "tenant_id": tenant_id,
        "utility_type": "ELECTRICITY",
        "amount": usage_amount,
        "manual_entry": True
    }
    
    print(f"Simulating {usage_amount} kWh for Tenant ID {tenant_id} ({tenant['full_name']})...")
    status, bill_data = make_request("/generate-bill/", method="POST", data=payload, headers=headers)
    
    if status == 200:
        print(f"   -> Success: {bill_data.get('message')}")
    else:
        print(f"   -> Skipped/Error (Status {status}): {bill_data.get('detail')}")
    print("-" * 40)

print("\n✅ Simulation complete!")