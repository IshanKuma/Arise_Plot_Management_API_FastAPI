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
    Real Firebase Firestore integration.
    
    Logic: Maintains separate collections for plots and zones,
    with role-based access control for data operations.
    """
    
    def __init__(self):
        """Initialize Firestore client and collection references."""
        self.db = get_firestore_db()
        self.plots_collection = self.db.collection(settings.FIRESTORE_COLLECTION_PLOTS)
        self.zones_collection = self.db.collection(settings.FIRESTORE_COLLECTION_ZONES)
        self.users_collection = self.db.collection(settings.FIRESTORE_COLLECTION_USERS)

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
        Query plots from Firestore with filtering and role-based access.
        
        Implements the exact logic from flowchart:
        1. Apply query parameters (country, zoneCode, category, phase)
        2. Apply role-based filtering (zone_admin gets zone-specific data)
        3. Return filtered plot list
        
        Args:
            query_params: Query filters from request
            user_zone: User's assigned zone (for zone_admin filtering)
            is_zone_admin: Whether user is zone_admin (affects filtering)
            
        Returns:
            List[PlotResponse]: Filtered list of plots
        """
        
        # Start with base query
        query = self.plots_collection
        
        # Apply role-based filtering first (as per flowchart logic)
        if is_zone_admin and user_zone:
            # Zone admin only sees plots in their zone
            query = query.where("zoneCode", "==", user_zone)
        
        # Apply query parameter filters
        if query_params.country:
            query = query.where("country", "==", query_params.country)
        
        if query_params.zoneCode:
            query = query.where("zoneCode", "==", query_params.zoneCode)
            
        if query_params.category:
            query = query.where("category", "==", query_params.category.value)
            
        if query_params.phase:
            query = query.where("phase", "==", query_params.phase)
        
        # Execute query and convert to response format
        docs = query.stream()
        plots = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data = self._prepare_plot_for_response(doc_data)
            plots.append(PlotResponse(**doc_data))
        
        return plots

    async def update_plot(self, request: PlotUpdateRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update plot information with business allocation details.
        
        Logic: 
        - Validates plot exists and user has access
        - Updates all provided fields (complete resource update - PUT semantics)
        - Zone admin can only update plots in their zone
        
        Args:
            request: Plot update request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found
            PermissionError: If zone access denied
        """
        # Build query to find the plot
        query = (self.plots_collection
                .where("plotName", "==", request.plotName)
                .where("zoneCode", "==", request.zoneCode)
                .where("country", "==", request.country))
        
        docs = list(query.stream())
        
        if not docs:
            raise ValueError("Plot not found")
        
        plot_doc = docs[0]
        
        # Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Prepare update data
        update_data = {
            "phase": request.phase,
            "plotStatus": request.plotStatus.value,
            "companyName": request.companyName,
            "sector": request.sector,
            "activity": request.activity,
            "investmentAmount": request.investmentAmount,
            "employmentGenerated": request.employmentGenerated,
            "allocatedDate": request.allocatedDate,
            "expiryDate": request.expiryDate,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Remove None values to avoid overwriting with None
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update the document
        plot_doc.reference.update(update_data)
        
        return {
            "message": "Plot updated successfully",
            "plotName": request.plotName,
            "status": request.plotStatus.value
        }

    async def release_plot(self, request: PlotReleaseRequest, user_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        Release a plot by setting status to available and clearing allocation data.
        
        Logic:
        - Different from update_plot - only changes status (PATCH semantics)
        - Clears all business allocation fields
        - Zone admin can only release plots in their zone
        
        Args:
            request: Plot release request data
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            Dict: Success response with plot details
            
        Raises:
            ValueError: If plot not found
            PermissionError: If zone access denied
        """
        # Build query to find the plot
        query = (self.plots_collection
                .where("plotName", "==", request.plotName)
                .where("zoneCode", "==", request.zoneCode)
                .where("country", "==", request.country))
        
        docs = list(query.stream())
        
        if not docs:
            raise ValueError("Plot not found")
        
        plot_doc = docs[0]
        
        # Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Release the plot - clear allocation data
        release_data = {
            "plotStatus": "Available",
            "companyName": None,
            "allocatedDate": None,
            "expiryDate": None,
            "investmentAmount": None,
            "employmentGenerated": None,
            "activity": None,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Update the document
        plot_doc.reference.update(release_data)
        
        return {
            "message": "Plot released successfully",
            "plotName": request.plotName,
            "status": "available"
        }

    async def create_zone(self, request: ZoneCreateRequest) -> Dict[str, Any]:
        """
        Create or update zone master data.
        
        Logic:
        - Essential for establishing economic zones before creating plots
        - Validates zone code uniqueness
        - Only super_admin and zone_admin can create zones
        
        Args:
            request: Zone creation request data
            
        Returns:
            Dict: Success response with zone code
            
        Raises:
            ValueError: If zone code already exists
        """
        # Check if zone already exists (country + zoneCode combination)
        existing_query = (self.zones_collection
                         .where("zoneCode", "==", request.zoneCode)
                         .where("country", "==", request.country))
        
        existing_docs = list(existing_query.stream())
        
        if existing_docs:
            raise ValueError(f"Zone code '{request.zoneCode}' already exists in {request.country}")
        
        # Prepare zone data
        zone_data = {
            "country": request.country,
            "zoneCode": request.zoneCode,
            "phase": request.phase,
            "landArea": request.landArea,
            "zoneName": request.zoneName,
            "zoneType": request.zoneType,
            "establishedDate": request.establishedDate,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add new zone
        self.zones_collection.add(zone_data)
        
        return {
            "message": "Zone data saved successfully",
            "zoneCode": request.zoneCode
        }

    async def get_plot_details(self, params: PlotDetailsQueryParams, user_zone: Optional[str] = None) -> PlotDetailsResponse:
        """
        Get detailed plot information for a specific zone.
        
        Logic:
        - Returns comprehensive plot data including business details
        - Provides metadata with summary statistics
        - Zone admin can only access their assigned zone
        
        Args:
            params: Query parameters (country, zoneCode)
            user_zone: User's zone (for zone_admin access control)
            
        Returns:
            PlotDetailsResponse: Detailed plot information with metadata
            
        Raises:
            PermissionError: If zone access denied
        """
        # Check zone access for zone_admin
        if user_zone and user_zone != params.zoneCode:
            raise PermissionError("Access denied: zone not in your assigned zone")
        
        # Query plots by country and zone
        query = (self.plots_collection
                .where("country", "==", params.country)
                .where("zoneCode", "==", params.zoneCode))
        
        docs = list(query.stream())
        
        # Process plot data
        plot_items = []
        available_count = 0
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data = self._prepare_plot_for_response(doc_data)
            
            # Count available plots
            if doc_data.get("plotStatus") == "Available":
                available_count += 1
            
            # Convert to plot detail item
            allocated_date = None
            if doc_data.get("allocatedDate"):
                if isinstance(doc_data["allocatedDate"], str):
                    allocated_date = datetime.fromisoformat(doc_data["allocatedDate"]).date()
                elif hasattr(doc_data["allocatedDate"], 'date'):
                    allocated_date = doc_data["allocatedDate"].date()
            
            plot_item = PlotDetailsItem(
                plotName=doc_data.get("plotName"),
                category=doc_data.get("category"),
                areaInHa=doc_data.get("areaInHa"),
                sector=doc_data.get("sector"),
                activity=doc_data.get("activity"),
                plotStatus=doc_data.get("plotStatus"),
                companyName=doc_data.get("companyName"),
                allocatedDate=allocated_date,
                investmentAmount=doc_data.get("investmentAmount"),
                employmentGenerated=doc_data.get("employmentGenerated")
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
