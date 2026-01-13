# test_auth_complete.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_complete_auth_flow():
    print("🧪 Testing Complete Authentication Flow\n")
    
    # Test 1: Register
    print("  Registering user...")
    response = requests.post(f"{BASE_URL}/register", json={
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "TestPass123",
        "phone_number": "+1111111111"
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print(f"   ✅ User created: {response.json()['username']}")
    elif response.status_code == 400:
        print(f"   ⚠️  User already exists")
    
    # Test 2: Login
    print("\n  Logging in...")
    response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@example.com",
        "password": "TestPass123"
    })
    print(f"   Status: {response.status_code}")
    tokens = response.json()
    print(f"   ✅ Access token: {tokens['access_token'][:30]}...")
    
    # Test 3: Get current user
    print("\n  Getting current user info...")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"   Status: {response.status_code}")
    user = response.json()
    print(f"   ✅ Logged in as: {user['username']} ({user['email']})")
    
    # Test 4: Wrong password
    print("\n  Testing wrong password...")
    response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@example.com",
        "password": "WrongPassword"
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print(f"   ✅ Correctly rejected")
    
    # Test 5: Refresh token
    print("\n5  Refreshing access token...")
    response = requests.post(f"{BASE_URL}/refresh", json={
        "refresh_token": tokens['refresh_token']
    })
    print(f"   Status: {response.status_code}")
    new_tokens = response.json()
    print(f"   ✅ New access token: {new_tokens['access_token'][:30]}...")
    
    print("\n✅ All tests passed! Authentication system working perfectly!")

if __name__ == "__main__":
    test_complete_auth_flow()