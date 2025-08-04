#!/usr/bin/env python3
"""
Test script for header-based pagination implementation.
Demonstrates how to extract pagination metadata from response headers.
"""

import requests
import json
from typing import Optional

class HeaderPaginationTester:
    """Test class for header-based pagination."""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {
            'Content-Type': 'application/json'
        }
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
    
    def get_auth_token(self, user_id: str = "admin001", role: str = "super_admin", zone: str = "GSEZ") -> str:
        """Get JWT token for testing."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/token",
            json={
                "userId": user_id,
                "role": role,
                "zone": zone
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            self.headers['Authorization'] = f'Bearer {self.auth_token}'
            print(f"✅ Auth token acquired successfully")
            return self.auth_token
        else:
            print(f"❌ Failed to get auth token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_available_plots_pagination(self, country: str = "gabon", limit: int = 5):
        """Test header-based pagination for available plots endpoint."""
        print(f"\n🔍 Testing Available Plots Pagination")
        print(f"Country: {country}, Limit: {limit}")
        print("-" * 50)
        
        cursor = None
        page = 1
        total_plots = 0
        
        while True:
            # Build request URL
            params = {
                'country': country,
                'limit': limit
            }
            if cursor:
                params['cursor'] = cursor
            
            # Make request
            response = requests.get(
                f"{self.base_url}/api/v1/plot/available",
                params=params,
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            # Parse response
            data = response.json()
            plots = data.get('plots', [])
            
            # Extract pagination from headers
            pagination_headers = {
                'limit': response.headers.get('X-Pagination-Limit'),
                'hasNextPage': response.headers.get('X-Pagination-Has-Next-Page'),
                'nextCursor': response.headers.get('X-Pagination-Next-Cursor'),
                'totalReturned': response.headers.get('X-Pagination-Total-Returned')
            }
            
            # Display results
            print(f"📄 Page {page}:")
            print(f"  📊 Plots returned: {len(plots)}")
            print(f"  📋 Pagination headers:")
            for key, value in pagination_headers.items():
                print(f"    {key}: {value}")
            
            # Check for inconsistency
            header_total = int(pagination_headers['totalReturned'] or 0)
            header_limit = int(pagination_headers['limit'] or 0)
            
            if header_total != len(plots):
                print(f"  ⚠️  Header totalReturned ({header_total}) != actual plots count ({len(plots)})")
            
            if header_total < header_limit and pagination_headers['hasNextPage'] == 'true':
                print(f"  🐛 INCONSISTENCY: totalReturned ({header_total}) < limit ({header_limit}) but hasNextPage=true")
                print(f"     This indicates client-side filtering is reducing results!")
            
            total_plots += len(plots)
            
            # Show first plot for verification
            if plots:
                print(f"  📍 First plot: {plots[0].get('plotName', 'Unknown')}")
            
            # Check if there are more pages
            has_next = pagination_headers['hasNextPage'] == 'true'
            cursor = pagination_headers['nextCursor']
            
            if not has_next or not cursor:
                print(f"\n✅ Pagination complete. Total plots retrieved: {total_plots}")
                break
            
            page += 1
            print()
    
    def test_plot_details_pagination(self, country: str = "gabon", zone_code: str = "GSEZ", limit: int = 3):
        """Test header-based pagination for plot details endpoint."""
        print(f"\n🔍 Testing Plot Details Pagination")
        print(f"Country: {country}, Zone: {zone_code}, Limit: {limit}")
        print("-" * 50)
        
        cursor = None
        page = 1
        total_plots = 0
        
        while True:
            # Build request URL
            params = {
                'country': country,
                'zoneCode': zone_code,
                'limit': limit
            }
            if cursor:
                params['cursor'] = cursor
            
            # Make request
            response = requests.get(
                f"{self.base_url}/api/v1/plot/plot-detail",
                params=params,
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            # Parse response
            data = response.json()
            plots = data.get('plots', [])
            metadata = data.get('metadata', {})
            
            # Extract pagination from headers
            pagination_headers = {
                'limit': response.headers.get('X-Pagination-Limit'),
                'hasNextPage': response.headers.get('X-Pagination-Has-Next-Page'),
                'nextCursor': response.headers.get('X-Pagination-Next-Cursor'),
                'totalReturned': response.headers.get('X-Pagination-Total-Returned')
            }
            
            # Display results
            print(f"📄 Page {page}:")
            print(f"  📊 Plots returned: {len(plots)}")
            print(f"  📈 Metadata: {metadata}")
            print(f"  📋 Pagination headers:")
            for key, value in pagination_headers.items():
                print(f"    {key}: {value}")
            
            # Check for inconsistency
            header_total = int(pagination_headers['totalReturned'] or 0)
            header_limit = int(pagination_headers['limit'] or 0)
            
            if header_total != len(plots):
                print(f"  ⚠️  Header totalReturned ({header_total}) != actual plots count ({len(plots)})")
            
            if header_total < header_limit and pagination_headers['hasNextPage'] == 'true':
                print(f"  🐛 INCONSISTENCY: totalReturned ({header_total}) < limit ({header_limit}) but hasNextPage=true")
                print(f"     This indicates client-side filtering is reducing results!")
            
            total_plots += len(plots)
            
            # Show first plot for verification
            if plots:
                print(f"  📍 First plot: {plots[0].get('plotName', 'Unknown')}")
            
            # Check if there are more pages
            has_next = pagination_headers['hasNextPage'] == 'true'
            cursor = pagination_headers['nextCursor']
            
            if not has_next or not cursor:
                print(f"\n✅ Pagination complete. Total plots retrieved: {total_plots}")
                break
            
            page += 1
            print()
    
    def run_tests(self):
        """Run all pagination tests."""
        print("🚀 Starting Header-Based Pagination Tests")
        print("=" * 60)
        
        # Get authentication token
        if not self.auth_token:
            if not self.get_auth_token():
                print("❌ Cannot proceed without authentication token")
                return
        
        # Test available plots pagination
        self.test_available_plots_pagination(country="gabon", limit=5)
        
        # Test plot details pagination
        self.test_plot_details_pagination(country="gabon", zone_code="GSEZ", limit=3)
        
        print("\n" + "=" * 60)
        print("🎯 Test Summary:")
        print("✅ Header-based pagination implementation tested")
        print("📋 Check output above for any inconsistencies between limit and totalReturned")
        print("💡 Expected behavior: totalReturned should equal limit (except on last page)")


def main():
    """Main function to run the tests."""
    tester = HeaderPaginationTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
