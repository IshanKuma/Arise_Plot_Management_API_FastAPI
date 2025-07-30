#!/usr/bin/env python3
"""
Quick test script to verify pagination implementation
"""
import requests
import json

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJhZG1pbjAwMSIsInJvbGUiOiJzdXBlcl9hZG1pbiIsInpvbmUiOiJHU0VaIiwicGVybWlzc2lvbnMiOnsicmVhZCI6WyJwbG90cyIsInpvbmVzIiwidXNlcnMiXSwid3JpdGUiOlsicGxvdHMiLCJ6b25lcyIsInVzZXJzIl19LCJpYXQiOjE3NTM4MzQ3MjAsImV4cCI6MTc1MzkyMTEyMH0.Je2XLjMi9Kas3tDGx6Dp5WznK6o-fEMpv79PRgp9fmw"
BASE_URL = "http://localhost:8000/api/v1"

def test_pagination():
    print("🧪 Testing Pagination Implementation")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    
    # Test 1: Available plots pagination
    print("\n1. Testing Available Plots Pagination...")
    response = requests.get(f"{BASE_URL}/plot/available?country=gabon&limit=3", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Got {len(data['plots'])} plots")
        print(f"   Pagination: limit={data['pagination']['limit']}, hasNext={data['pagination']['hasNextPage']}")
        
        if data['pagination']['hasNextPage']:
            cursor = data['pagination']['nextCursor']
            print(f"   Next cursor: {cursor}")
            
            # Test cursor pagination
            response2 = requests.get(f"{BASE_URL}/plot/available?country=gabon&limit=3&cursor={cursor}", headers=headers)
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✅ Cursor pagination works: Got {len(data2['plots'])} more plots")
            else:
                print(f"❌ Cursor pagination failed: {response2.status_code}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 2: Plot details pagination
    print("\n2. Testing Plot Details Pagination...")
    response = requests.get(f"{BASE_URL}/plot/plot-detail?country=gabon&zoneCode=GSEZ&limit=2", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Got {len(data['plots'])} plot details")
        print(f"   Metadata: {data['metadata']['totalPlots']} total plots")
        print(f"   Pagination: limit={data['pagination']['limit']}, hasNext={data['pagination']['hasNextPage']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    print("\n🎉 Pagination testing complete!")

if __name__ == "__main__":
    test_pagination()
