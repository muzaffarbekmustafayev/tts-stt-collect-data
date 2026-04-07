#!/usr/bin/env python3
"""
Test login endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_ping():
    """Test ping endpoint"""
    print("Testing /ping endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login_json():
    """Test login with JSON"""
    print("\nTesting /auth/login with JSON...")
    try:
        data = {
            "username": "admin",
            "password": "admin123"
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=data,
            headers=headers,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login_form():
    """Test login with form data"""
    print("\nTesting /auth/login-form with form data...")
    try:
        data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(
            f"{BASE_URL}/auth/login-form",
            data=data,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\nTesting CORS...")
    try:
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
        response = requests.options(
            f"{BASE_URL}/auth/login",
            headers=headers,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        print(f"CORS Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower():
                print(f"  {key}: {value}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Login Test Script")
    print("=" * 60)
    
    test_ping()
    test_cors()
    test_login_json()
    test_login_form()
    
    print("\n" + "=" * 60)
    print("Note: Default credentials are username='admin', password='admin123'")
    print("If login fails, you may need to create an admin user first.")
    print("=" * 60)
