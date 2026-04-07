import requests
import json

BASE_URL = "http://localhost:8000"

# Test login first
print("Testing login...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "superadmin", "password": "superadmin123"}
)
print(f"Login status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /admin/audios
    print("\n\nTesting /admin/audios...")
    audios_response = requests.get(
        f"{BASE_URL}/admin/audios?page=1&limit=5",
        headers=headers
    )
    print(f"Status: {audios_response.status_code}")
    if audios_response.status_code == 200:
        data = audios_response.json()
        print(f"Response type: {type(data)}")
        print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"Error: {audios_response.text}")
    
    # Test /admin/checked-audios
    print("\n\nTesting /admin/checked-audios...")
    checked_response = requests.get(
        f"{BASE_URL}/admin/checked-audios?page=1&limit=5",
        headers=headers
    )
    print(f"Status: {checked_response.status_code}")
    if checked_response.status_code == 200:
        data = checked_response.json()
        print(f"Response type: {type(data)}")
        print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"Error: {checked_response.text}")
    
    # Test /admin/statistics
    print("\n\nTesting /admin/statistics...")
    stats_response = requests.get(
        f"{BASE_URL}/admin/statistics",
        headers=headers
    )
    print(f"Status: {stats_response.status_code}")
    if stats_response.status_code == 200:
        data = stats_response.json()
        print(f"Response type: {type(data)}")
        print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict):
            print(f"Audios type: {type(data.get('audios'))}")
            print(f"Audios length: {len(data.get('audios', []))}")
            print(f"Checked audios type: {type(data.get('checked_audios'))}")
            print(f"Checked audios length: {len(data.get('checked_audios', []))}")
    else:
        print(f"Error: {stats_response.text}")
else:
    print(f"Login failed: {login_response.text}")
