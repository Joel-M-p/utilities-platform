import os, re

print("SCANNING BACKEND ENDPOINTS")
print("=" * 60)

routers_dir = 'api/routers'
endpoints = []

for filename in sorted(os.listdir(routers_dir)):
    if filename.endswith('.py') and not filename.startswith('__'):
        filepath = os.path.join(routers_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
        for method, path in matches:
            endpoints.append((method.upper(), path, filename))

endpoints.sort(key=lambda x: x[1])
print(f"\nFound {len(endpoints)} endpoints:\n")
for method, path, filename in endpoints:
    print(f"  {method:6} {path:45} ({filename})")

print("\n" + "=" * 60)
print("\nDASHBOARD.HTML FETCH CALLS:")
print("-" * 60)

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

fetch_urls = re.findall(r"fetch\([`']([^`']+)", content)
unique_urls = sorted(set(fetch_urls))

for url in unique_urls:
    print(f"  {url}")