#!/usr/bin/env python3
"""
Simple API test script
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\nTesting / endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_docs():
    """Test docs endpoint"""
    print("\nTesting /docs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Docs available: {response.status_code == 200}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_statistics():
    """Test public statistics endpoint"""
    print("\nTesting /statistic endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/statistic/", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("API Test Script")
    print("=" * 50)
    
    results = {
        "Health": test_health(),
        "Root": test_root(),
        "Docs": test_docs(),
        "Statistics": test_statistics(),
    }
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 50)
