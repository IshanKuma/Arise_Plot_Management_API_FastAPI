#!/usr/bin/env python3
"""
Script to check zone-master collection and understand country-specific zone codes.
"""
import os
import sys
sys.path.append('/home/user/Desktop/arise_fastapi')

from app.core.firebase import get_firestore_db
from app.core.config import settings

def check_zone_master():
    """Check zone-master collection for country-specific zone codes."""
    try:
        print("🔍 Checking zone-master collection...")
        db = get_firestore_db()
        
        # Check zone-master collection
        zone_collection = db.collection('zone-master')
        zone_docs = list(zone_collection.stream())
        
        print(f"📊 Found {len(zone_docs)} zones in zone-master collection")
        
        if zone_docs:
            print("\n🏢 Zone codes by country:")
            country_zones = {}
            
            for doc in zone_docs:
                data = doc.to_dict()
                country = data.get('country', 'Unknown')
                zone_code = data.get('zoneCode', 'Unknown')
                zone_name = data.get('zoneName', 'Unknown')
                
                if country not in country_zones:
                    country_zones[country] = []
                country_zones[country].append(f"{zone_code} ({zone_name})")
            
            for country, zones in country_zones.items():
                print(f"  {country}: {', '.join(zones)}")
        else:
            print("📭 No zones found in zone-master collection")
            
        # Also check admin-access for any zone information
        print("\n🔍 Checking admin-access collection...")
        admin_collection = db.collection('admin-access')
        admin_docs = list(admin_collection.limit(5).stream())
        
        print(f"📊 Found {len(admin_docs)} documents in admin-access collection")
        
        if admin_docs:
            print("\n👤 Sample admin access data:")
            for doc in admin_docs[:3]:
                data = doc.to_dict()
                print(f"  - {doc.id}: {data}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_zone_master()
