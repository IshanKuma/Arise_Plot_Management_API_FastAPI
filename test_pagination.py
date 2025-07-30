#!/usr/bin/env python3
"""
Test script for pagination implementation
"""
import requests
import json

# JWT token for authentication
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJhZG1pbjAwMSIsInJvbGUiOiJzdXBlcl9hZG1pbiIsInpvbmUiOiJHU0VaIiwicGVybWlzc2lvbnMiOnsicmVhZCI6WyJwbG90cyIsInpvbmVzIiwidXNlcnMiXSwid3JpdGUiOlsicGxvdHMiLCJ6b25lcyIsInVzZXJzIl19LCJpYXQiOjE3NTM4MzQ3MjAsImV4cCI6MTc1MzkyMTEyMH0.Je2XLjMi9Kas3tDGx6Dp5WznK6o-fEMpv79PRgp9fmw"

BASE_URL = "http://localhost:8000/api/v1"

def test_available_plots_pagination():
    """Test available plots endpoint with pagination"""
    print("🧪 Testing Available Plots Endpoint with Pagination")
    print("=" * 60)
    
    # Test 1: Basic pagination
    url = f"{BASE_URL}/plot/available"
    params = {
        "country": "gabon",
        "limit": 5
    }
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Available plots endpoint working!")
            print(f"📊 Response Structure:")
            print(f"  - plots: {len(data.get('plots', []))} items")
            print(f"  - pagination: {data.get('pagination', {})}")
            
            # Pretty print first few plots
            plots = data.get('plots', [])
            if plots:
                print(f"\n📋 Sample Plot Data:")
                for i, plot in enumerate(plots[:2]):
                    print(f"  Plot {i+1}: {plot.get('plotName')} - {plot.get('plotStatus')} - {plot.get('category')}")
                    
            # Test pagination
            pagination = data.get('pagination', {})
            print(f"\n🔄 Pagination Info:")
            print(f"  - Limit: {pagination.get('limit')}")
            print(f"  - Total Returned: {pagination.get('totalReturned')}")
            print(f"  - Has Next Page: {pagination.get('hasNextPage')}")
            print(f"  - Next Cursor: {pagination.get('nextCursor')}")
            
            # Test cursor pagination if available
            if pagination.get('hasNextPage') and pagination.get('nextCursor'):
                print(f"\n🔄 Testing Cursor Pagination...")
                params['cursor'] = pagination['nextCursor']
                response2 = requests.get(url, params=params, headers=headers)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"✅ Cursor pagination working! Got {len(data2.get('plots', []))} more plots")
                else:
                    print(f"❌ Cursor pagination failed: {response2.status_code}")
                    
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")

def test_plot_details_pagination():
    """Test plot details endpoint with pagination"""
    print("\n🧪 Testing Plot Details Endpoint with Pagination")
    print("=" * 60)
    
    url = f"{BASE_URL}/plot/plot-detail"
    params = {
        "country": "gabon",
        "zoneCode": "GSEZ",
        "limit": 3
    }
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Plot details endpoint working!")
            print(f"📊 Response Structure:")
            print(f"  - metadata: {data.get('metadata', {})}")
            print(f"  - plots: {len(data.get('plots', []))} items")
            print(f"  - pagination: {data.get('pagination', {})}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")

if __name__ == "__main__":
    test_available_plots_pagination()
    test_plot_details_pagination()
