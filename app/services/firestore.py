"""
Firestore database service for plot and zone data management.
Real Firestore integration - replaces mock data.
"""
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
from google.cloud import firestore
from app.core.firebase import get_firestore_db
from app.core.config import settings
from app.schemas.plots import (
    PlotResponse, PlotQueryParams, PlotCategory, PlotStatus,
    PlotUpdateRequest, PlotReleaseRequest, ZoneCreateRequest,
    PlotDetailsQueryParams, PlotDetailsMetadata, PlotDetailsItem
)


class FirestoreService:
    """
    Service for Firestore database operations.
    Updated to work with {country} -> {zoneCode} -> {phase} collection structure.
    
    Logic: Uses static country-to-zone mapping for optimal performance.
    Targets {country} collections with zone and phase sub-collections.
    """
    
    def __init__(self):
        """Initialize Firestore client and static country-zone mapping."""
        self.db = get_firestore_db()
        
        # Static mapping for optimal performance
        self.country_zone_mapping = {
            "drc": "CIP",
            "benin": "GDIZ", 
            "gabon": "GSEZ",
            "nigeria": "IPR",
            "roc": "PIC",
            "rwanda": "BSEZ",
            "togo": "PIA"
        }
        
        # Use the configured collections (now pointing to actual structure)
        self.zones_collection = self.db.collection(settings.FIRESTORE_COLLECTION_ZONES)
        self.users_collection = self.db.collection(settings.FIRESTORE_COLLECTION_USERS)

    def get_plot_collection_path(self, country: str, zone_code: str, phase: str) -> str:
        """
        Get the correct collection path for country -> zone -> phase structure.
        
        Args:
            country: Country name (e.g., 'gabon')
            zone_code: Zone code (e.g., 'GSEZ') 
            phase: Phase identifier (e.g., 'phase1')
            
        Returns:
            str: Collection path for plots
        """
        return f"{country.lower()}/{zone_code}/{phase}"

    def validate_country_zone_mapping(self, country: str, zone_code: str) -> bool:
        """
        Validate that the provided country and zone code match the static mapping.
        
        Args:
            country: Country name
            zone_code: Zone code
            
        Returns:
            bool: True if mapping is valid
            
        Raises:
            ValueError: If mapping is invalid
        """
        country_lower = country.lower()
        expected_zone = self.country_zone_mapping.get(country_lower)
        
        if not expected_zone:
            raise ValueError(f"Unsupported country: {country}. Supported countries: {list(self.country_zone_mapping.keys())}")
        
        if zone_code != expected_zone:
            raise ValueError(f"Invalid zone code for {country}. Expected: {expected_zone}, Got: {zone_code}")
        
        return True

    def _parse_area(self, area_str: str) -> float:
        """Parse area string to float, handling empty strings and None."""
        try:
            if isinstance(area_str, (int, float)):
                return float(area_str)
            if not area_str or area_str.strip() == '':
                return 0.0
            # Remove any non-numeric characters except decimal point
            numeric_str = re.sub(r'[^\d.]', '', str(area_str))
            return float(numeric_str) if numeric_str else 0.0
        except Exception:
            return 0.0

    # COMMENTED OUT - REDUNDANT: Not used anywhere in the codebase
    # def _convert_firestore_timestamp(self, timestamp) -> Optional[str]:
    #     """Convert Firestore timestamp to ISO string format."""
    #     if timestamp is None:
    #         return None
    #     if hasattr(timestamp, 'isoformat'):
    #         return timestamp.isoformat()
    #     return str(timestamp)

    # COMMENTED OUT - REDUNDANT: Not used anywhere in the codebase
    # def _prepare_plot_for_response(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Convert Firestore document data to response format."""
    #     # Convert Firestore timestamps to strings for JSON serialization
    #     if 'allocatedDate' in doc_data:
    #         doc_data['allocatedDate'] = self._convert_firestore_timestamp(doc_data['allocatedDate'])
    #     if 'expiryDate' in doc_data:
    #         doc_data['expiryDate'] = self._convert_firestore_timestamp(doc_data['expiryDate'])
    #     
    #     return doc_data

    def get_available_plots(
        self, 
        query_params: PlotQueryParams,
        user_zone: Optional[str] = None,
        is_zone_admin: bool = False
    ) -> tuple[List[PlotResponse], dict]:
        """
        Query plots from Firestore with cursor-based pagination and filtering.
        Uses {country} -> {zoneCode} -> {phase} collection structure.
        
        Performance Optimizations:
        - Uses static country-zone mapping for O(1) collection resolution
        - Firebase limit() for controlled batch sizes (default: 50)
        - Cursor-based pagination with startAfter() for efficient navigation
        - Direct path to plots collection: {country}/{zoneCode}/{phase}
        
        Args:
            query_params: Query filters and pagination parameters (country, zoneCode, phase required)
            user_zone: User's assigned zone (for zone_admin filtering)
            is_zone_admin: Whether user is zone_admin (affects filtering)
            
        Returns:
            tuple: (plots_list, pagination_metadata)
        """
        
        # Step 1: Validate country-zone mapping
        self.validate_country_zone_mapping(query_params.country, query_params.zoneCode)
        
        # Step 2: Check zone access for zone_admin
        if is_zone_admin and user_zone and user_zone != query_params.zoneCode:
            raise PermissionError(f"Access denied: You can only access plots in zone {user_zone}")
        
        # Step 3: Get collection reference using static mapping
        collection_path = self.get_plot_collection_path(
            query_params.country, 
            query_params.zoneCode, 
            query_params.phase
        )
        plots_collection = self.db.collection(collection_path)
        
        print(f"🔍 GET request: Querying collection: {collection_path}")
        
        # Step 4: Build Firebase query with pagination
        # Order by document ID for consistent pagination
        query = plots_collection.order_by('__name__')
        
        # Apply cursor pagination if provided
        if query_params.cursor:
            try:
                cursor_doc = plots_collection.document(query_params.cursor).get()
                if cursor_doc.exists:
                    query = query.start_after(cursor_doc)
            except Exception:
                # Invalid cursor - ignore and start from beginning
                pass
        
        # Apply limit (add 1 to check if there are more pages)
        limit = query_params.limit or 50
        query = query.limit(limit + 1)
        
        # Step 5: Execute query
        docs = list(query.stream())
        
        # Step 6: Check if there are more pages
        has_next_page = len(docs) > limit
        if has_next_page:
            docs = docs[:-1]  # Remove the extra document used for pagination check
        
        # Step 7: Prepare pagination metadata
        next_cursor = docs[-1].id if docs and has_next_page else None
        pagination_meta = {
            "limit": limit,
            "hasNextPage": has_next_page,
            "nextCursor": next_cursor,
            "totalReturned": 0  # Will be updated after filtering
        }
        
        # Step 8: Process documents with client-side filtering
        plots = []
        
        for doc in docs:
            try:
                data = doc.to_dict()
                
                # Apply category filter if specified
                if query_params.category:
                    doc_category = data.get('category', '').strip()
                    if doc_category != query_params.category.value:
                        continue
                
                # Convert to PlotResponse format
                plot_response = PlotResponse(
                    plotName=data.get('name', ''),
                    plotStatus=data.get('plotStatus', 'Available'),
                    category=data.get('category', 'Residential'),
                    phase=int(data.get('phase', 1)),
                    areaInSqm=Decimal(str(self._parse_area(data.get('areaInSqm', 0)))),
                    areaInHa=Decimal(str(self._parse_area(data.get('areaInHa', 0)))),
                    zoneCode=query_params.zoneCode,
                    country=query_params.country
                )
                plots.append(plot_response)
                
            except Exception as e:
                print(f"⚠️ Error processing plot document {doc.id}: {e}")
                continue
        
        # Update pagination metadata with actual returned count
        pagination_meta["totalReturned"] = len(plots)
        
        return plots, pagination_meta

    async def update_plot(self, request: PlotUpdateRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update plot information with business allocation details.
        Uses {country} -> {zoneCode} -> {phase} collection structure.
        
        Logic: 
        - Validates country-zone mapping using static mapping
        - Uses direct path to plot collection: {country}/{zoneCode}/{phase}
        - Finds plot by name field (matches actual DB schema)
        - Updates plot with business allocation details
        
        Args:
            request: Plot update request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found or invalid country-zone mapping
            PermissionError: If zone access denied
        """
        # Step 1: Validate country-zone mapping
        self.validate_country_zone_mapping(request.country, request.zoneCode)
        
        # Step 2: Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError(f"Access denied: You can only update plots in zone {user_zone}")
        
        # Step 3: Get collection reference using static mapping
        collection_path = self.get_plot_collection_path(
            request.country, 
            request.zoneCode, 
            request.phase
        )
        plots_collection = self.db.collection(collection_path)
        
        # Step 4: Find plot by name with debugging and flexible matching
        print(f"🔍 Searching for plot: '{request.plotName}' in collection: {collection_path}")
        
        # First try exact match
        query = plots_collection.where(filter=firestore.FieldFilter("name", "==", request.plotName))
        docs = list(query.stream())
        
        # If exact match fails, try flexible matching
        if not docs:
            print(f"🔍 Exact match failed, trying flexible matching...")
            all_docs = list(plots_collection.stream())
            
            # Normalize whitespace for comparison
            normalized_search = ' '.join(request.plotName.split())
            
            for doc in all_docs:
                data = doc.to_dict()
                db_name = data.get('name', '')
                normalized_db_name = ' '.join(db_name.split())
                
                if normalized_search.lower() == normalized_db_name.lower():
                    print(f"🔍 Found flexible match: '{db_name}' matches '{request.plotName}'")
                    docs = [doc]
                    break
        
        print(f"🔍 Found {len(docs)} matching documents")
        
        if not docs:
            # Debug: Let's see what plots are actually in this collection
            print(f"🔍 DEBUG: Searching for any plots in {collection_path}")
            debug_query = plots_collection.limit(5)
            debug_docs = list(debug_query.stream())
            print(f"🔍 DEBUG: Found {len(debug_docs)} total plots in collection")
            
            for i, doc in enumerate(debug_docs):
                data = doc.to_dict()
                plot_name = data.get('name', 'NO_NAME')
                print(f"🔍 DEBUG Plot {i+1}: Name='{plot_name}', ID='{doc.id}'")
                print(f"🔍 DEBUG Plot {i+1} Keys: {list(data.keys())}")
                
            # Show exact search vs available names
            available_names = [doc.to_dict().get('name', 'NO_NAME') for doc in debug_docs]
            print(f"🔍 DEBUG: Available plot names: {available_names}")
            print(f"🔍 DEBUG: Searching for: '{request.plotName}'")
            print(f"🔍 DEBUG: Exact match check: {request.plotName in available_names}")
            
            raise ValueError(f"Plot '{request.plotName}' not found in {collection_path}")
        
        plot_doc = docs[0]
        
        # Step 5: Get current plot data to check existing structure
        current_data = plot_doc.to_dict()
        current_details = current_data.get('details', {})
        
        # Step 6: Prepare update data for details object (only include non-None optional fields)
        details_updates = {}
        
        # Always update plotStatus in details
        details_updates["plotStatus"] = request.plotStatus.value
        
        # Add optional fields only if provided
        if request.category is not None:
            details_updates["category"] = request.category.value
        if request.areaInSqm is not None:
            details_updates["areaInSqm"] = request.areaInSqm
        if request.areaInHa is not None:
            details_updates["areaInHa"] = request.areaInHa
        
        # Create the update data structure
        update_data = {
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Update specific fields in details object using Firestore field path notation
        for field_name, field_value in details_updates.items():
            update_data[f"details.{field_name}"] = field_value
        
        print(f"🔄 Updating plot details with: {details_updates}")
        
        # Step 7: Update the document
        plot_doc.reference.update(update_data)
        
        return {
            "message": "Plot updated successfully",
            "plotName": request.plotName,
            "status": request.plotStatus.value
        }

    async def release_plot(self, request: PlotReleaseRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update plot status to Available or Occupied.
        Uses {country} -> {zoneCode} -> {phase} collection structure.
        
        Logic:
        - Validates country-zone mapping using static mapping
        - Uses direct path to plot collection: {country}/{zoneCode}/{phase}
        - Different from update_plot - only changes status and allocation data (PATCH semantics)
        - If status is set to Available, clears all business allocation fields
        - If status is set to Occupied, keeps existing allocation data
        
        Args:
            request: Plot status update request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found or invalid country-zone mapping
            PermissionError: If zone access denied
        """
        # Step 1: Validate country-zone mapping
        self.validate_country_zone_mapping(request.country, request.zoneCode)
        
        # Step 2: Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError(f"Access denied: You can only update plots in zone {user_zone}")
        
        # Step 3: Get collection reference using static mapping
        collection_path = self.get_plot_collection_path(
            request.country, 
            request.zoneCode, 
            request.phase
        )
        plots_collection = self.db.collection(collection_path)
        
        print(f"🔍 Searching for plot: {request.plotName} in {collection_path}")
        
        # Step 4: Find plot by name with debugging and flexible matching
        print(f"🔍 PATCH: Searching for plot: '{request.plotName}' in {collection_path}")
        
        # First try exact match
        query = plots_collection.where(filter=firestore.FieldFilter("name", "==", request.plotName))
        docs = list(query.stream())
        
        # If exact match fails, try flexible matching
        if not docs:
            print(f"🔍 Exact match failed, trying flexible matching...")
            all_docs = list(plots_collection.stream())
            
            # Normalize whitespace for comparison
            normalized_search = ' '.join(request.plotName.split())
            
            for doc in all_docs:
                data = doc.to_dict()
                db_name = data.get('name', '')
                normalized_db_name = ' '.join(db_name.split())
                
                if normalized_search.lower() == normalized_db_name.lower():
                    print(f"🔍 Found flexible match: '{db_name}' matches '{request.plotName}'")
                    docs = [doc]
                    break
        
        if not docs:
            # Debug: Let's see what plots are actually in this collection
            print(f"🔍 DEBUG: Searching for any plots in {collection_path}")
            debug_query = plots_collection.limit(5)
            debug_docs = list(debug_query.stream())
            print(f"🔍 DEBUG: Found {len(debug_docs)} total plots in collection")
            
            for i, doc in enumerate(debug_docs):
                data = doc.to_dict()
                plot_name = data.get('name', 'NO_NAME')
                print(f"🔍 DEBUG Plot {i+1}: Name='{plot_name}', ID='{doc.id}'")
                
            raise ValueError(f"Plot '{request.plotName}' not found in {collection_path}")
        
        plot_doc = docs[0]
        
        # Step 5: Get current plot data to check existing structure
        current_data = plot_doc.to_dict()
        current_details = current_data.get('details', {})
        
        # Step 6: Prepare update data for details object
        details_updates = {}
        
        # Always update plotStatus in details
        details_updates["plotStatus"] = request.plotStatus
        
        # If setting to Available, clear allocation data in details
        if request.plotStatus.lower() == "available":
            details_updates.update({
                "companyName": "",
                "activity": "",
                "operationalStatus": "",
                "remark": ""
            })
            # Clear top-level fields that might be allocation-related
            update_data = {
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "expiryDate": None,
                "investmentAmount": None,
                "employmentGenerated": None
            }
        else:
            # Just update the timestamp if not clearing
            update_data = {
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
        
        # Update specific fields in details object using Firestore field path notation
        for field_name, field_value in details_updates.items():
            update_data[f"details.{field_name}"] = field_value
        
        print(f"🔄 Updating plot details with: {details_updates}")
        
        # Step 7: Update the document
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
            "zoneCode": request.zoneCode,
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

    async def get_plot_details(self, params: PlotDetailsQueryParams, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get simplified plot information for a specific zone with cursor-based pagination.
        Uses {country} -> {zoneCode} -> {phase} collection structure.
        
        Performance Optimizations:
        - Uses static country-zone mapping for O(1) collection resolution
        - Firebase limit() and startAfter() for efficient pagination
        - Direct path to plots collection: {country}/{zoneCode}/{phase}
        - Default limit: 50 items per request
        
        Args:
            params: Query parameters (country, zoneCode, phase, limit, cursor)
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Simplified plot information with metadata and pagination
            
        Raises:
            PermissionError: If zone access denied
            ValueError: If invalid country-zone mapping
        """
        try:
            # Step 1: Validate country-zone mapping
            self.validate_country_zone_mapping(params.country, params.zoneCode)
            
            # Step 2: Check zone access for zone_admin
            if user_zone and user_zone != params.zoneCode:
                raise PermissionError(f"Access denied: You can only access plots in zone {user_zone}")
            
            # Step 3: Get collection reference using static mapping
            collection_path = self.get_plot_collection_path(
                params.country, 
                params.zoneCode, 
                params.phase
            )
            plots_collection = self.db.collection(collection_path)
            
            print(f"🔍 GET plot-details: Querying collection: {collection_path}")
            
            # Step 4: Build Firebase query with pagination
            query = plots_collection.order_by('__name__')
            
            # Apply cursor pagination if provided
            if params.cursor:
                try:
                    cursor_doc = plots_collection.document(params.cursor).get()
                    if cursor_doc.exists:
                        query = query.start_after(cursor_doc)
                except Exception:
                    pass  # Invalid cursor, start from beginning
            
            # Apply limit (add 1 to check for next page)
            limit = params.limit or 50
            query = query.limit(limit + 1)
            
            # Step 5: Execute query
            docs = list(query.stream())
            
            # Step 6: Check pagination
            has_next_page = len(docs) > limit
            if has_next_page:
                docs = docs[:-1]
            
            next_cursor = docs[-1].id if docs and has_next_page else None
            
            # Step 7: Process plot data
            plot_items = []
            available_count = 0
            
            for doc in docs:
                try:
                    data = doc.to_dict()
                    
                    # Extract essential data with defaults
                    plot_name = data.get('name', f"Plot-{doc.id}")
                    status = data.get('plotStatus', 'Available')
                    category = data.get('category', 'Residential')
                    phase = str(data.get('phase', '1'))
                    area_sqm = self._parse_area(data.get('areaInSqm', '0'))
                    area_ha = self._parse_area(data.get('areaInHa', '0'))
                    
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
            
            # Step 8: Create metadata
            metadata = {
                "country": params.country,
                "zoneCode": params.zoneCode,
                "totalPlots": len(plot_items),
                "availablePlots": available_count
            }
            
            # Step 9: Create pagination metadata
            pagination_meta = {
                "limit": limit,
                "hasNextPage": has_next_page,
                "nextCursor": next_cursor,
                "totalReturned": len(plot_items)
            }
            
            return {
                "metadata": metadata,
                "plots": [item.__dict__ for item in plot_items],
                "pagination": pagination_meta
            }
            
        except Exception as e:
            print(f"❌ Error in get_plot_details: {e}")
            raise

    # COMMENTED OUT - REDUNDANT: Unused methods not called by any API endpoint
    # async def create_plot(self, plot_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Create a new plot in Firestore.
    #     
    #     Args:
    #         plot_data: Plot information to store
    #         
    #     Returns:
    #         Dict: Success response with plot ID
    #     """
    #     # Add timestamps
    #     plot_data["createdAt"] = firestore.SERVER_TIMESTAMP
    #     plot_data["updatedAt"] = firestore.SERVER_TIMESTAMP
    #     
    #     # Add plot to Firestore
    #     doc_ref = self.plots_collection.add(plot_data)
    #     
    #     return {
    #         "message": "Plot created successfully",
    #         "plotId": doc_ref[1].id,
    #         "plotName": plot_data.get("plotName")
    #     }

    # async def get_zones(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
    #     """
    #     Get all zones, optionally filtered by country.
    #     
    #     Args:
    #         country: Optional country filter
    #         
    #     Returns:
    #         List[Dict]: List of zone data
    #     """
    #     query = self.zones_collection
    #     
    #     if country:
    #         query = query.where("country", "==", country)
    #     
    #     docs = query.stream()
    #     zones = []
    #     
    #     for doc in docs:
    #         zone_data = doc.to_dict()
    #         zone_data["id"] = doc.id
    #         zones.append(zone_data)
    #     
    #     return zones


# Create a single instance to be used across the application
firestore_service = FirestoreService()
