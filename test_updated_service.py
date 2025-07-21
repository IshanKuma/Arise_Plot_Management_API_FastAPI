#!/usr/bin/env python3
"""
Updated Firestore service to work with the actual database structure.
Handles country-specific collections and existing data formats.
"""
import os
import sys
sys.path.append('/home/user/Desktop/arise_fastapi')

from app.core.firebase import get_firestore_db
from app.core.config import settings
from app.schemas.plots import PlotDetailsQueryParams, PlotDetailsResponse, PlotDetailsItem, PlotDetailsMetadata
from typing import Optional, Dict, Any, List
from datetime import datetime, date

class UpdatedFirestoreService:
    """Updated service to work with actual database structure."""
    
    def __init__(self):
        self.db = get_firestore_db()
        
        # Country-specific plot collections mapping
        self.country_plot_collections = {
            "gabon": "gabon-plots",
            "benin": "benin-plots", 
            "togo": "togo-plots",
            "roc": "roc-plots",
            "rwanda": "rwanda-plots",
            "drc": "drc-plots",
            "nigeria": "nigeria-plots",
            "tanzania": "tanzania-plots"
        }
    
    def get_plot_collection_name(self, country: str) -> str:
        """Get the correct collection name for a country."""
        country_lower = country.lower()
        return self.country_plot_collections.get(country_lower, f"{country_lower}-plots")
    
    async def get_plot_details(self, params: PlotDetailsQueryParams, user_zone: Optional[str] = None) -> PlotDetailsResponse:
        """
        Get plot details using the actual database structure.
        """
        try:
            # Get the correct collection for the country
            collection_name = self.get_plot_collection_name(params.country)
            print(f"🔍 Querying collection: {collection_name}")
            
            plots_collection = self.db.collection(collection_name)
            
            # For now, get all plots (since zoneCode filtering needs zone-master mapping)
            docs = list(plots_collection.stream())
            print(f"📊 Found {len(docs)} documents in {collection_name}")
            
            # Process plot data
            plot_items = []
            available_count = 0
            
            for doc in docs:
                doc_data = doc.to_dict()
                
                # Extract details from the nested structure
                details = doc_data.get('details', {})
                
                # Map the actual data structure to our schema
                plot_status = self._map_plot_status(details.get('plotStatus', ''))
                category = self._map_category(details.get('category', ''))
                
                # Count available plots
                if plot_status == "Available":
                    available_count += 1
                
                # Handle area conversion
                area_ha = self._parse_area(details.get('areaInHa', '0'))
                
                # Create plot item
                plot_item = PlotDetailsItem(
                    plotName=doc_data.get('name', details.get('name', 'Unknown')),
                    category=category,
                    areaInHa=area_ha,
                    sector=None,  # Not in current structure
                    activity=details.get('activity', None),
                    plotStatus=plot_status,
                    companyName=details.get('companyName', None) if details.get('companyName') else None,
                    allocatedDate=None,  # Would need date parsing
                    investmentAmount=None,  # Not in current structure
                    employmentGenerated=None  # Not in current structure
                )
                plot_items.append(plot_item)
            
            # Create metadata
            metadata = PlotDetailsMetadata(
                country=params.country,
                zoneCode=params.zoneCode,
                totalPlots=len(docs),
                availablePlots=available_count
            )
            
            return PlotDetailsResponse(metadata=metadata, plots=plot_items)
            
        except Exception as e:
            print(f"❌ Error in get_plot_details: {e}")
            raise
    
    def _map_plot_status(self, status: str) -> str:
        """Map database status to API status."""
        status_lower = status.lower()
        if 'available' in status_lower:
            return "Available"
        elif 'occupied' in status_lower or 'allocated' in status_lower:
            return "Allocated"
        elif 'reserved' in status_lower:
            return "Reserved"
        else:
            return "Available"  # Default
    
    def _map_category(self, category: str) -> str:
        """Map database category to API category."""
        category_lower = category.lower()
        if 'industrial' in category_lower:
            return "Industrial"
        elif 'commercial' in category_lower:
            return "Commercial"
        elif 'residential' in category_lower:
            return "Residential"
        else:
            return "Industrial"  # Default
    
    def _parse_area(self, area_str: str) -> float:
        """Parse area string to float."""
        try:
            if isinstance(area_str, (int, float)):
                return float(area_str)
            # Remove any non-numeric characters except decimal point
            import re
            numeric_str = re.sub(r'[^\d.]', '', str(area_str))
            return float(numeric_str) if numeric_str else 0.0
        except:
            return 0.0

# Test the updated service
async def test_updated_service():
    """Test the updated service with actual data."""
    try:
        service = UpdatedFirestoreService()
        
        # Test with Gabon data
        params = PlotDetailsQueryParams(country="Gabon", zoneCode="GSEZ")
        result = await service.get_plot_details(params)
        
        print("✅ Test Results:")
        print(f"Country: {result.metadata.country}")
        print(f"Zone: {result.metadata.zoneCode}")
        print(f"Total Plots: {result.metadata.totalPlots}")
        print(f"Available Plots: {result.metadata.availablePlots}")
        print(f"Plot Details: {len(result.plots)} plots")
        
        for i, plot in enumerate(result.plots[:3], 1):
            print(f"  Plot {i}: {plot.plotName} - {plot.plotStatus} ({plot.category})")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_updated_service())
