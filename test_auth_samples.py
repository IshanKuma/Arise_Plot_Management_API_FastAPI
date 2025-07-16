#!/usr/bin/env python3
"""
Sample tests for the Arise Plot Management API Auth Endpoint
Demonstrates all authentication scenarios with clear input/output examples
"""

import requests
import json
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"
PLOTS_ENDPOINT = f"{BASE_URL}/api/v1/plots/available"

# Test Data Configuration
VALID_SECRET_KEY = "arise-master-auth-secret-2025"
INVALID_SECRET_KEY = "wrong-secret-key"

def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def print_request_details(method: str, url: str, headers: Dict, body: Dict = None):
    """Print formatted request details"""
    print(f"\n📤 REQUEST:")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    if body:
        print(f"Body:")
        print(f"  {json.dumps(body, indent=2)}")

def print_response_details(response):
    """Print formatted response details"""
    print(f"\n📥 RESPONSE:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'content-length']:
            print(f"  {key}: {value}")
    print(f"Body:")
    try:
        print(f"  {json.dumps(response.json(), indent=2)}")
    except:
        print(f"  {response.text}")

def test_valid_authentication():
    """Test Case 1: Valid Authentication - Should Return JWT Token"""
    print_test_header("Valid Authentication")
    
    # Request Configuration
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Secret {VALID_SECRET_KEY}"  # 🔑 SECRET KEY GOES HERE
    }
    
    body = {
        "userId": "admin001",        # 👤 USER ID GOES HERE
        "role": "super_admin",       # 🎭 ROLE GOES HERE (super_admin, zone_admin, normal_user)
        "zone": "GSEZ"              # 🌍 ZONE GOES HERE (GSEZ, OSEZ, GABON, TEST)
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    
    # Make Request
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    # Extract JWT Token for later use
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n✅ SUCCESS: JWT Token Generated!")
        print(f"🎫 Token: {token[:50]}...")
        return token
    else:
        print(f"\n❌ FAILED: Expected 200, got {response.status_code}")
        return None

def test_invalid_secret_key():
    """Test Case 2: Invalid Secret Key - Should Return 401 Unauthorized"""
    print_test_header("Invalid Secret Key")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Secret {INVALID_SECRET_KEY}"  # 🔑 WRONG SECRET KEY
    }
    
    body = {
        "userId": "admin001",
        "role": "super_admin", 
        "zone": "GSEZ"
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    if response.status_code == 401:
        print(f"\n✅ SUCCESS: Correctly rejected invalid secret key!")
    else:
        print(f"\n❌ FAILED: Expected 401, got {response.status_code}")

def test_missing_authorization_header():
    """Test Case 3: Missing Authorization Header - Should Return 401"""
    print_test_header("Missing Authorization Header")
    
    headers = {
        "Content-Type": "application/json"
        # 🚫 NO AUTHORIZATION HEADER
    }
    
    body = {
        "userId": "admin001",
        "role": "super_admin",
        "zone": "GSEZ"
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    if response.status_code == 401:
        print(f"\n✅ SUCCESS: Correctly requires Authorization header!")
    else:
        print(f"\n❌ FAILED: Expected 401, got {response.status_code}")

def test_wrong_authorization_format():
    """Test Case 4: Wrong Authorization Format - Should Return 401"""
    print_test_header("Wrong Authorization Format")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_SECRET_KEY}"  # 🚫 WRONG FORMAT (should be "Secret")
    }
    
    body = {
        "userId": "admin001",
        "role": "super_admin",
        "zone": "GSEZ"
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    if response.status_code == 401:
        print(f"\n✅ SUCCESS: Correctly rejects wrong Authorization format!")
    else:
        print(f"\n❌ FAILED: Expected 401, got {response.status_code}")

def test_invalid_role():
    """Test Case 5: Invalid Role - Should Return 400 Bad Request"""
    print_test_header("Invalid Role")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Secret {VALID_SECRET_KEY}"
    }
    
    body = {
        "userId": "admin001",
        "role": "invalid_role",  # 🚫 INVALID ROLE
        "zone": "GSEZ"
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    if response.status_code == 422:  # Pydantic validation error
        print(f"\n✅ SUCCESS: Correctly rejects invalid role!")
    else:
        print(f"\n❌ FAILED: Expected 422, got {response.status_code}")

def test_invalid_zone():
    """Test Case 6: Invalid Zone - Should Return 400 Bad Request"""
    print_test_header("Invalid Zone")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Secret {VALID_SECRET_KEY}"
    }
    
    body = {
        "userId": "admin001",
        "role": "super_admin",
        "zone": "INVALID"  # 🚫 INVALID ZONE (not in VALID_ZONES)
    }
    
    print_request_details("POST", AUTH_ENDPOINT, headers, body)
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    print_response_details(response)
    
    if response.status_code == 400:
        print(f"\n✅ SUCCESS: Correctly rejects invalid zone!")
    else:
        print(f"\n❌ FAILED: Expected 400, got {response.status_code}")

def test_different_roles():
    """Test Case 7: Different Valid Roles - All Should Work"""
    print_test_header("Different Valid Roles")
    
    roles = ["super_admin", "zone_admin", "normal_user"]
    
    for role in roles:
        print(f"\n🎭 Testing Role: {role}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Secret {VALID_SECRET_KEY}"
        }
        
        body = {
            "userId": f"user_{role}",
            "role": role,
            "zone": "GSEZ"
        }
        
        response = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"  ✅ {role}: SUCCESS - Token expires in {token_data['expires_in']} seconds")
        else:
            print(f"  ❌ {role}: FAILED - Status {response.status_code}")

def test_jwt_token_usage(jwt_token: str):
    """Test Case 8: Use JWT Token for Protected Endpoint"""
    if not jwt_token:
        print("\n⚠️ SKIPPING: No JWT token available")
        return
        
    print_test_header("JWT Token Usage")
    
    headers = {
        "Authorization": f"Bearer {jwt_token}"  # 🎫 JWT TOKEN GOES HERE
    }
    
    url = f"{PLOTS_ENDPOINT}?country=Gabon"
    
    print_request_details("GET", url, headers)
    response = requests.get(url, headers=headers)
    print_response_details(response)
    
    if response.status_code == 200:
        plots_data = response.json()
        print(f"\n✅ SUCCESS: Retrieved {len(plots_data.get('plots', []))} plots!")
    else:
        print(f"\n❌ FAILED: Expected 200, got {response.status_code}")

def main():
    """Run all test cases"""
    print("🚀 ARISE PLOT MANAGEMENT API - AUTH ENDPOINT TESTING")
    print("=" * 80)
    print("This script demonstrates all authentication scenarios")
    print("=" * 80)
    
    try:
        # Test valid authentication and get JWT token
        jwt_token = test_valid_authentication()
        
        # Test error scenarios
        test_invalid_secret_key()
        test_missing_authorization_header()
        test_wrong_authorization_format()
        test_invalid_role()
        test_invalid_zone()
        test_different_roles()
        
        # Test JWT token usage
        test_jwt_token_usage(jwt_token)
        
        print(f"\n{'='*60}")
        print("🎉 ALL TESTS COMPLETED!")
        print("📚 Check the output above for detailed results")
        print(f"{'='*60}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("🔧 Make sure the FastAPI server is running on http://localhost:8000")
        print("💡 Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
