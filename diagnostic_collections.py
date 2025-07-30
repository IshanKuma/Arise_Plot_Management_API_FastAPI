#!/usr/bin/env python3
"""
Diagnostic script to check what collections exist in Firestore.
This will help understand which countries have data in the new nested structure.
"""

from app.core.firebase import get_firestore_db

def check_collections():
    """Check what top-level collections exist in Firestore."""
    db = get_firestore_db()
    
    print("🔍 Checking Firestore Collections...")
    print("=" * 50)
    
    # List of countries to check
    countries_to_check = [
        'gabon', 'benin', 'drc', 'nigeria', 'roc', 'togo',
        'cameroon', 'ghana', 'ivorycoast', 'senegal'
    ]
    
    print("📊 Country Collections Status:")
    print("-" * 30)
    
    for country in countries_to_check:
        try:
            # Check if country collection exists
            collection_ref = db.collection(country)
            docs = list(collection_ref.limit(1).stream())
            
            if docs:
                print(f"✅ {country.upper()}: Has collection")
                
                # Check what zones exist
                zone_docs = list(collection_ref.limit(5).stream())
                zones = [doc.id for doc in zone_docs]
                print(f"   📁 Zones: {', '.join(zones) if zones else 'None'}")
                
                # Check phases for first zone
                if zones:
                    first_zone = collection_ref.document(zones[0])
                    try:
                        phase_docs = list(first_zone.collection('phase1').limit(1).stream())
                        phase_count = len(phase_docs)
                        print(f"   📋 Phase1 plots in {zones[0]}: {phase_count} documents")
                    except:
                        print(f"   ⚠️  No phase1 subcollection in {zones[0]}")
            else:
                print(f"❌ {country.upper()}: No collection found")
                
                # Check if old structure exists
                old_collection = f"{country}-plots"
                old_docs = list(db.collection(old_collection).limit(1).stream())
                if old_docs:
                    print(f"   📁 Found old structure: {old_collection}")
                    
        except Exception as e:
            print(f"❌ {country.upper()}: Error checking - {e}")
        
        print()
    
    print("🎯 Summary:")
    print("- ✅ = Country has new nested structure (country/zone/phase)")
    print("- ❌ = Country has no new structure")
    print("- 📁 = Shows what zones/phases exist")

if __name__ == "__main__":
    check_collections()
