"""
Firestore database service for plot and zone data management.
Real Firestore integration - replaces mock data.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
from google.cloud import firestore
from app.core.firebase import get_firestore_db
from app.core.config import settings
from app.schemas.plots import (
    PlotResponse, PlotQueryParams, PlotCategory, PlotStatus,
    PlotUpdateRequest, PlotReleaseRequest, ZoneCreateRequest,
    PlotDetailsQueryParams, PlotDetailsResponse, PlotDetailsMetadata, PlotDetailsItem
)


class FirestoreService:
    """
    Service for Firestore database operations.
    Updated to work with actual country-specific database structure.
    
    Logic: Handles country-specific plot collections and existing data formats.
    """
    
    def __init__(self):
        """Initialize Firestore client and collection references."""
        self.db = get_firestore_db()
        # Use the configured collections (now pointing to actual structure)
        self.plots_collection = self.db.collection(settings.FIRESTORE_COLLECTION_PLOTS)
        self.zones_collection = self.db.collection(settings.FIRESTORE_COLLECTION_ZONES)
        self.users_collection = self.db.collection(settings.FIRESTORE_COLLECTION_USERS)
        
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

    def _parse_area(self, area_str: str) -> float:
        """Parse area string to float, handling empty strings and None."""
        try:
            if isinstance(area_str, (int, float)):
                return float(area_str)
            if not area_str or area_str.strip() == '':
                return 0.0
            # Remove any non-numeric characters except decimal point
            import re
            numeric_str = re.sub(r'[^\d.]', '', str(area_str))
            return float(numeric_str) if numeric_str else 0.0
        except Exception:
            return 0.0

    def _convert_firestore_timestamp(self, timestamp) -> Optional[str]:
        """Convert Firestore timestamp to ISO string format."""
        if timestamp is None:
            return None
        if hasattr(timestamp, 'isoformat'):
            return timestamp.isoformat()
        return str(timestamp)

    def _prepare_plot_for_response(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Firestore document data to response format."""
        # Convert Firestore timestamps to strings for JSON serialization
        if 'allocatedDate' in doc_data:
            doc_data['allocatedDate'] = self._convert_firestore_timestamp(doc_data['allocatedDate'])
        if 'expiryDate' in doc_data:
            doc_data['expiryDate'] = self._convert_firestore_timestamp(doc_data['expiryDate'])
        
        return doc_data

    def get_available_plots(
        self, 
        query_params: PlotQueryParams,
        user_zone: Optional[str] = None,
        is_zone_admin: bool = False
    ) -> List[PlotResponse]:
        """
        Query plots from Firestore with filtering and role-based access using dynamic collections.
        
        Updated to handle actual Firestore data structure:
        - Data is nested under 'details' field
        - plotStatus filtering for available plots only
        - Proper field mapping from Firestore to API response
        
        Args:
            query_params: Query filters from request
            user_zone: User's assigned zone (for zone_admin filtering)
            is_zone_admin: Whether user is zone_admin (affects filtering)
            
        Returns:
            List[PlotResponse]: Filtered list of available plots
        """
        
        # Step 1: Determine target collection based on country parameter
        if query_params.country:
            # Use country-specific collection based on the provided country
            collection_name = self.get_plot_collection_name(query_params.country)
            plots_collection = self.db.collection(collection_name)
        else:
            # If no country specified, default to gabon-plots collection
            plots_collection = self.db.collection("gabon-plots")
        
        # Step 2: Get all documents (no where clauses due to nested structure)
        docs = list(plots_collection.stream())
        plots = []
        
        for doc in docs:
            try:
                doc_data = doc.to_dict()
                details = doc_data.get('details', {})
                
                # Step 3: Filter for available plots only
                plot_status = details.get('plotStatus', '').strip()
                
                # Consider plots available if status is "Available" or empty string
                if plot_status.lower() not in ['available', '']:
                    continue
                
                # Step 4: Extract and map fields from nested structure OR root level
                # Check both root level and details for plot name
                plot_name = doc_data.get('name') or details.get('name', f"Plot-{doc.id}")
                category_str = details.get('category', 'Industrial')  # Default to Industrial
                area_sqm = self._parse_area(details.get('areaInSqm', '0'))
                area_ha = self._parse_area(details.get('areaInHa', '0'))
                
                # If area_ha is 0 but area_sqm exists, calculate hectares
                if area_ha == 0.0 and area_sqm > 0:
                    area_ha = area_sqm / 10000  # Convert sqm to hectares
                
                # Map category to valid enum value
                category_mapping = {
                    'residential': 'Residential',
                    'commercial': 'Commercial', 
                    'industrial': 'Industrial',
                    'facility/utility': 'Industrial',  # Map facility to Industrial
                    '': 'Industrial'  # Default empty to Industrial
                }
                category = category_mapping.get(category_str.lower(), 'Industrial')
                
                # Step 5: Apply query parameter filters (client-side filtering)
                # Filter by country if specified (assume collection name indicates country)
                if query_params.country:
                    expected_collection = self.get_plot_collection_name(query_params.country)
                    if collection_name != expected_collection:
                        continue
                
                # Filter by zoneCode if specified (would need zoneCode in data)
                if query_params.zoneCode:
                    # Skip if zoneCode filtering requested but no zoneCode in data
                    doc_zone = details.get('zoneCode', '')
                    if doc_zone != query_params.zoneCode:
                        continue
                
                # Filter by category if specified
                if query_params.category and query_params.category.value != category:
                    continue
                
                # Filter by phase if specified (would need phase in data)
                if query_params.phase:
                    doc_phase = details.get('phase', 1)
                    try:
                        if int(doc_phase) != query_params.phase:
                            continue
                    except (ValueError, TypeError):
                        continue
                
                # Step 6: Apply role-based filtering
                if is_zone_admin and user_zone:
                    doc_zone = details.get('zoneCode', '')
                    if doc_zone != user_zone:
                        continue
                
                # Step 7: Create response object with mapped fields
                plot_response = PlotResponse(
                    plotName=plot_name,
                    plotStatus=PlotStatus.AVAILABLE,  # We only return available plots
                    category=PlotCategory(category),
                    phase=1,  # Default phase since not in current data structure
                    areaInSqm=Decimal(str(area_sqm)),
                    areaInHa=Decimal(str(area_ha)),
                    zoneCode=details.get('zoneCode', 'UNKNOWN'),  # Default if missing
                    country=query_params.country or "Gabon"  # Use query param or default
                )
                
                plots.append(plot_response)
                
            except Exception as e:
                # Skip invalid documents and continue
                print(f"⚠️ Skipping invalid plot document {doc.id}: {e}")
                continue
        
        return plots

    async def update_plot(self, request: PlotUpdateRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update plot information with business allocation details using dynamic collections.
        
        Logic: 
        - Uses country-specific collection based on request.country
        - Finds plot by name field (matches actual DB schema)
        - Adds allocation fields to existing plot document
        - Works with flat document structure (no nested details)
        
        Args:
            request: Plot update request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found
        """
        # Get country-specific collection
        collection_name = self.get_plot_collection_name(request.country)
        plots_collection = self.db.collection(collection_name)
        
        # Build query to find the plot by name (actual field in DB)
        query = plots_collection.where("name", "==", request.plotName)
        
        docs = list(query.stream())
        
        if not docs:
            raise ValueError(f"Plot '{request.plotName}' not found in {request.country}")
        
        plot_doc = docs[0]
        
        # Note: Zone access checking disabled since plots don't have zoneCode in current schema
        # if user_zone and user_zone != request.zoneCode:
        #     raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Prepare update data - match the exact format from GET response
        update_data = {
            "plotStatus": request.plotStatus.value,
            "category": request.category.value,
            "phase": request.phase,
            "areaInSqm": request.areaInSqm,
            "areaInHa": request.areaInHa,
            "zoneCode": request.zoneCode,
            "country": request.country,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Update the document
        plot_doc.reference.update(update_data)
        
        return {
            "message": "Plot updated successfully",
            "plotName": request.plotName,
            "status": request.plotStatus.value
        }

    async def release_plot(self, request: PlotReleaseRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update plot status to Available or Occupied using dynamic collections.
        
        Logic:
        - Uses country-specific collection based on request.country
        - Different from update_plot - only changes status and allocation data (PATCH semantics)
        - If status is set to Available, clears all business allocation fields
        - If status is set to Occupied, keeps existing allocation data
        - Zone admin can only update plots in their zone
        - If zoneCode not provided, looks up plot by country and plotName first
        
        Args:
            request: Plot status update request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found
            PermissionError: If zone access denied
        """
        # Get country-specific collection
        collection_name = self.get_plot_collection_name(request.country)
        plots_collection = self.db.collection(collection_name)
        
        print(f"🔍 Request received - Country: {request.country}, PlotName: {request.plotName}, PlotStatus: {request.plotStatus}")
        print(f"🔍 Searching for plot in collection: {collection_name}")
        print(f"🔍 Search criteria - Country: {request.country}, PlotName: {request.plotName}, ZoneCode: {request.zoneCode}")
        
        # Build query to find the plot
        if request.zoneCode:
            # If zoneCode provided, use it in the query
            query = (plots_collection
                    .where("name", "==", request.plotName)
                    .where("zoneCode", "==", request.zoneCode)
                    .where("country", "==", request.country))
        else:
            # If zoneCode not provided, find by country and plotName only
            query = (plots_collection
                    .where("name", "==", request.plotName)
                    .where("country", "==", request.country))
        
        docs = list(query.stream())
        print(f"🔍 Found {len(docs)} matching documents")
        
        if not docs:
            # Let's try to find any plots with similar names for debugging
            debug_query = plots_collection.where("country", "==", request.country).limit(5)
            debug_docs = list(debug_query.stream())
            print(f"🔍 DEBUG: Found {len(debug_docs)} total plots in {request.country}")
            for doc in debug_docs:
                data = doc.to_dict()
                print(f"🔍 DEBUG: Plot - Name: '{data.get('name')}', Zone: '{data.get('zoneCode')}'")
                print(f"🔍 DEBUG: All fields: {list(data.keys())}")
                if 'details' in data:
                    details = data['details']
                    print(f"🔍 DEBUG: Details fields: {list(details.keys())}")
                    print(f"🔍 DEBUG: Details name: '{details.get('name')}'")
                break  # Only show first plot for debugging
            raise ValueError("Plot not found")
        
        plot_doc = docs[0]
        plot_data = plot_doc.to_dict()
        
        # Get the actual zoneCode from the plot data
        actual_zone_code = plot_data.get("zoneCode")
        
        # Check zone access for zone_admin
        if user_zone and user_zone != actual_zone_code:
            raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Update the plot with the requested status
        update_data = {
            "plotStatus": request.plotStatus,  # Use the status from the request (already a string)
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # If setting to Available, clear allocation data
        if request.plotStatus.lower() == "available":
            update_data.update({
                "companyName": None,
                "allocatedDate": None,
                "expiryDate": None,
                "investmentAmount": None,
                "employmentGenerated": None,
                "activity": None
            })
        
        # Update the document
        try:
            print(f"🔄 Updating plot with data: {update_data}")
            plot_doc.reference.update(update_data)
            print(f"✅ Plot updated successfully")
        except Exception as e:
            print(f"❌ Error updating plot: {e}")
            raise
        
        return {
            "message": f"Plot status updated to {request.plotStatus} successfully",
            "plotName": request.plotName,
            "zoneCode": actual_zone_code,
            "status": request.plotStatus.lower()
        }

    async def create_zone(self, request: ZoneCreateRequest) -> Dict[str, Any]:
        """
        Create or update zone master data with custom document naming.
        
        Logic:
        - Essential for establishing economic zones before creating plots
        - Uses document ID format: {country}_{zoneCode} (e.g., "Gabon_GSEZ")
        - Validates zone code uniqueness by checking document existence
        - Uses simplified format matching existing data structure
        
        Args:
            request: Zone creation request data
            
        Returns:
            Dict: Success response with zone details
            
        Raises:
            ValueError: If zone code already exists
        """
        try:
            # Create document ID using {country}_{zoneCode} format
            document_id = f"{request.country}_{request.zoneCode}"
            
            # Check if zone already exists by checking document ID
            zone_doc_ref = self.zones_collection.document(document_id)
            existing_doc = zone_doc_ref.get()
            
            if existing_doc.exists:
                raise ValueError(f"Zone code '{request.zoneCode}' already exists in {request.country}")
            
            # Prepare zone data in the simplified format
            zone_data = {
                "country": request.country,
                "zoneCode": request.zoneCode,
                "phase": request.phase,  # Keep as string
                "landArea": request.landArea,  # Keep as string with unit
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
            
            # Set the document with the specific ID {country}_{zoneCode}
            zone_doc_ref.set(zone_data)
            
            # Return the created zone data (matching response schema)
            return {
                "country": request.country,
                "zoneCode": request.zoneCode,
                "phase": request.phase,
                "landArea": request.landArea
            }
            
        except Exception as e:
            # Re-raise with more context for debugging
            print(f"❌ Error in create_zone: {e}")
            raise

    async def get_plot_details(self, params: PlotDetailsQueryParams, user_zone: Optional[str] = None) -> PlotDetailsResponse:
        """
        Get simplified plot information for a specific country using actual database structure.
        
        Logic:
        - Uses country-specific collections (e.g., gabon-plots, benin-plots)
        - Returns only essential plot fields without null-heavy data
        - Handles nested 'details' objects in documents
        
        Args:
            params: Query parameters (country, zoneCode)
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            PlotDetailsResponse: Simplified plot information with metadata
            
        Raises:
            PermissionError: If zone access denied
        """
        try:
            # Check zone access for zone_admin
            if user_zone and user_zone != params.zoneCode:
                raise PermissionError("Access denied: zone not in your assigned zone")
            
            # Get the correct collection for the country
            collection_name = self.get_plot_collection_name(params.country)
            plots_collection = self.db.collection(collection_name)
            
            # Get all plots for the country
            docs = list(plots_collection.stream())
            
            # Process plot data with simplified logic
            plot_items = []
            available_count = 0
            
            for doc in docs:
                try:
                    doc_data = doc.to_dict()
                    details = doc_data.get('details', {})
                    
                    # Extract essential data with defaults
                    plot_name = doc_data.get('name', f"Plot-{doc.id}")
                    status = details.get('plotStatus', 'Available')
                    category = details.get('category', '')
                    phase = str(details.get('phase', '1'))
                    area_sqm = self._parse_area(details.get('areaInSqm', '0'))
                    area_ha = self._parse_area(details.get('areaInHa', '0'))
                    
                    # Count available plots
                    if status.lower() in ['available', '']:
                        available_count += 1
                    
                    # Create simplified plot item
                    plot_item = PlotDetailsItem(
                        plotName=plot_name,
                        status=status,
                        category=category,
                        phase=phase,
                        areaInSqm=area_sqm,
                        areaInHa=area_ha,
                        country=params.country,
                        zoneCode=params.zoneCode
                    )
                    plot_items.append(plot_item)
                    
                except Exception as e:
                    # Skip invalid documents but continue processing
                    print(f"⚠️ Skipping invalid plot document {doc.id}: {e}")
                    continue
            
            # Create metadata
            metadata = PlotDetailsMetadata(
                country=params.country,
                zoneCode=params.zoneCode,
                totalPlots=len(plot_items),
                availablePlots=available_count
            )
            
            return PlotDetailsResponse(metadata=metadata, plots=plot_items)
            
        except Exception as e:
            print(f"❌ Error in get_plot_details: {e}")
            raise

    async def create_plot(self, plot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new plot in Firestore.
        
        Args:
            plot_data: Plot information to store
            
        Returns:
            Dict: Success response with plot ID
        """
        # Add timestamps
        plot_data["createdAt"] = firestore.SERVER_TIMESTAMP
        plot_data["updatedAt"] = firestore.SERVER_TIMESTAMP
        
        # Add plot to Firestore
        doc_ref = self.plots_collection.add(plot_data)
        
        return {
            "message": "Plot created successfully",
            "plotId": doc_ref[1].id,
            "plotName": plot_data.get("plotName")
        }

    async def get_zones(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all zones, optionally filtered by country.
        
        Args:
            country: Optional country filter
            
        Returns:
            List[Dict]: List of zone data
        """
        query = self.zones_collection
        
        if country:
            query = query.where("country", "==", country)
        
        docs = query.stream()
        zones = []
        
        for doc in docs:
            zone_data = doc.to_dict()
            zone_data["id"] = doc.id
            zones.append(zone_data)
        
        return zones


# Create a single instance to be used across the application
firestore_service = FirestoreService()
