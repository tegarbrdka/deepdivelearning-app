"""
Simple script to test if backend is running and accessible
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("Testing EduClassify Backend")
print("=" * 60)

# Test 1: Root endpoint
print("\n1. Testing root endpoint...")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Docs endpoint
print("\n2. Testing /docs endpoint...")
try:
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Docs accessible")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Login endpoint
print("\n3. Testing /auth/login endpoint...")
try:
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✓ Login successful")
        print(f"   Response: {response.json()}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
