# test_api_health_endpoints.py
import requests
import json

print("=== Testing API Health Endpoints ===")

endpoints = [
    "/health",
    "/api/v1/admin/database/health",
    "/api/v1/admin/database/stats"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"http://127.0.0.1:8000{endpoint}")
        print(f"\n🔍 {endpoint}:")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {json.dumps(data, indent=4)}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

print("\n" + "="*50)
print("If the endpoints return healthy status but the dashboard shows unhealthy,")
print("the issue is in the dashboard display logic, not the database!")