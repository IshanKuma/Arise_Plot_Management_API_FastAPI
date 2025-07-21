#!/usr/bin/env python3
"""
Comprehensive Firestore diagnostic script to discover all collections and their structure.
"""
import os
import sys
sys.path.append('/home/user/Desktop/arise_fastapi')

from app.core.firebase import get_firestore_db
from app.core.config import settings
import json

def discover_firestore_structure():
    """Discover all collections and document structures in Firestore."""
    try:
        print("🔍 Discovering Firestore database structure...")
        db = get_firestore_db()
        print(f"✅ Connected to project: {settings.FIREBASE_PROJECT_ID}")
        print("=" * 70)
        
        # Get all collections
        collections = db.collections()
        collection_names = []
        
        for collection in collections:
            collection_names.append(collection.id)
        
        if not collection_names:
            print("📭 No collections found in the database.")
            print("This means your Firestore database is empty.")
            return
        
        print(f"📚 Found {len(collection_names)} collection(s):")
        for name in collection_names:
            print(f"  - {name}")
        
        print("\n" + "=" * 70)
        
        # Examine each collection
        for collection_name in collection_names:
            print(f"\n📊 Collection: '{collection_name}'")
            print("-" * 50)
            
            collection_ref = db.collection(collection_name)
            docs = list(collection_ref.limit(3).stream())  # Get first 3 documents
            
            print(f"Documents found: {len(docs)}")
            
            if docs:
                print("Sample document structure:")
                for i, doc in enumerate(docs[:2], 1):  # Show first 2 docs
                    doc_data = doc.to_dict()
                    print(f"\nDocument {i} (ID: {doc.id}):")
                    
                    # Pretty print the document structure
                    for key, value in doc_data.items():
                        value_type = type(value).__name__
                        if isinstance(value, str) and len(value) > 50:
                            value_preview = value[:47] + "..."
                        else:
                            value_preview = value
                        print(f"  {key}: {value_preview} ({value_type})")
            else:
                print("  (Collection is empty)")
        
        print("\n" + "=" * 70)
        print("🔧 Configuration Check:")
        print(f"Expected collections from config:")
        print(f"  - Plots: {settings.FIRESTORE_COLLECTION_PLOTS}")
        print(f"  - Zones: {settings.FIRESTORE_COLLECTION_ZONES}")
        print(f"  - Users: {settings.FIRESTORE_COLLECTION_USERS}")
        
        print(f"\nActual collections found:")
        for name in collection_names:
            print(f"  - {name}")
        
        # Check for mismatches
        expected = {settings.FIRESTORE_COLLECTION_PLOTS, settings.FIRESTORE_COLLECTION_ZONES, settings.FIRESTORE_COLLECTION_USERS}
        actual = set(collection_names)
        
        missing = expected - actual
        extra = actual - expected
        
        if missing:
            print(f"\n⚠️  Missing expected collections: {missing}")
        
        if extra:
            print(f"\n📋 Additional collections found: {extra}")
        
        if not missing and not extra and expected == actual:
            print(f"\n✅ All expected collections are present!")
        
    except Exception as e:
        print(f"❌ Error discovering Firestore structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    discover_firestore_structure()
