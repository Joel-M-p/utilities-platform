import requests
import json

def print_result(test_name, passed, message=""):
    status = "\033[92m[PASS]\033[0m" if passed else "\033[91m[FAIL]\033[0m"
    print(f"{status} {test_name}: {message}")

def run_tests():
    print("="*50)
    print("  UTILITIES PLATFORM - AUTOMATED TEST KIT")
    print("="*50)
    
    # 1. Get Configuration from User
    base_url = input("Enter API URL (e.g., http://127.0.0.1:8000 or https://your-app.onrender.com): ").strip()
    if base_url.endswith('/'):
        base_url = base_url[:-1]
        
    username = input("Enter Admin Username (default: admin): ").strip() or "admin"
    password = input("Enter Admin Password (default: password123): ").strip() or "password123"
    
    print("\nStarting tests...\n")
    
    auth_token = None
    headers = {}

    # Test 1: System Health
    try:
        r = requests.get(f"{base_url}/", timeout=10)
        passed = r.status_code == 200 and "running" in r.json().get("message", "").lower()
        print_result("1. System Health Check", passed, r.json().get("message", "No message"))
    except Exception as e:
        print_result("1. System Health Check", False, str(e))
        print("\n[!] Server is not reachable. Aborting tests.")
        return

    # Test 2: Authentication
    try:
        r = requests.post(f"{base_url}/login", json={"username": username, "password": password})
        passed = r.status_code == 200 and "token" in r.json()
        if passed:
            auth_token = r.json()["token"]
            headers = {"Authorization": f"Bearer {auth_token}"}
        print_result("2. Admin Authentication", passed, "Token acquired successfully" if passed else r.text)
    except Exception as e:
        print_result("2. Admin Authentication", False, str(e))
        return

    # Test 3: Dashboard Stats (Requires Auth)
    try:
        r = requests.get(f"{base_url}/dashboard-stats/", headers=headers)
        passed = r.status_code == 200 and "revenue" in r.json()
        print_result("3. Dashboard Stats Fetch", passed, "Stats loaded" if passed else r.text)
    except Exception as e:
        print_result("3. Dashboard Stats Fetch", False, str(e))

    # Test 4: Fetch Properties
    prop_id = None
    try:
        r = requests.get(f"{base_url}/properties/", headers=headers)
        passed = r.status_code == 200 and len(r.json().get("properties", [])) > 0
        if passed:
            prop_id = r.json()["properties"][0]["id"]
        print_result("4. Fetch Properties", passed, f"Found {len(r.json().get('properties', []))} properties")
    except Exception as e:
        print_result("4. Fetch Properties", False, str(e))

    # Test 5: Fetch Tenants
    tenant_id = None
    try:
        r = requests.get(f"{base_url}/all-tenants/?property_id={prop_id}", headers=headers) if prop_id else requests.get(f"{base_url}/all-tenants/", headers=headers)
        passed = r.status_code == 200 and len(r.json().get("tenants", [])) > 0
        if passed:
            tenant_id = r.json()["tenants"][0]["tenant_id"]
        print_result("5. Fetch Tenants", passed, f"Found {len(r.json().get('tenants', []))} tenants")
    except Exception as e:
        print_result("5. Fetch Tenants", False, str(e))

    # Test 6: Fetch Meters
    try:
        r = requests.get(f"{base_url}/all-meters/", headers=headers)
        passed = r.status_code == 200 and "meters" in r.json()
        print_result("6. Fetch Meters", passed, f"Found {len(r.json().get('meters', []))} meters")
    except Exception as e:
        print_result("6. Fetch Meters", False, str(e))

    # Test 7: Fetch Tariffs
    try:
        r = requests.get(f"{base_url}/tariffs/", headers=headers)
        passed = r.status_code == 200 and "tariffs" in r.json()
        print_result("7. Fetch Tariffs", passed, f"Found {len(r.json().get('tariffs', []))} tariffs")
    except Exception as e:
        print_result("7. Fetch Tariffs", False, str(e))

    # Test 8: Payment Waterfall Logic (Process R10 Top-up)
    if tenant_id:
        try:
            payload = {
                "tenant_id": tenant_id,
                "amount": 10.00,
                "idempotency_key": "test-kit-topup-001"
            }
            r = requests.post(f"{base_url}/process-payment/", json=payload, headers=headers)
            passed = r.status_code == 200 and r.json().get("status") == "success"
            print_result("8. Payment Waterfall Logic", passed, f"R10 topup applied to Tenant {tenant_id}" if passed else r.text)
        except Exception as e:
            print_result("8. Payment Waterfall Logic", False, str(e))
    else:
        print_result("8. Payment Waterfall Logic", False, "Skipped (No tenants found to test)")

    # Test 9: Audit Log Fetch
    try:
        r = requests.get(f"{base_url}/audit-log/", headers=headers)
        passed = r.status_code == 200 and "logs" in r.json()
        print_result("9. Audit Log Fetch", passed, f"Found {len(r.json().get('logs', []))} logs")
    except Exception as e:
        print_result("9. Audit Log Fetch", False, str(e))

    print("\n" + "="*50)
    print("  TEST KIT EXECUTION COMPLETE")
    print("="*50)

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n[!] Test interrupted by user.")