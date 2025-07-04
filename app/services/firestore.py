"""
Firestore database service for plot and zone data management.
Currently uses mock data - will be replaced with actual Firestore integration.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
from app.schemas.plots import (
    PlotResponse, PlotQueryParams, PlotCategory, PlotStatus,
    PlotUpdateRequest, PlotReleaseRequest, ZoneCreateRequest,
    PlotDetailsQueryParams, PlotDetailsResponse, PlotDetailsMetadata, PlotDetailsItem
)


class FirestoreService:
    """
    Service for Firestore database operations.
    Currently uses mock data for development/testing.
    
    Logic: Maintains separate collections for plots and zones,
    with role-based access control for data operations.
    """
    
    def __init__(self):
        """Initialize with mock data collections"""
        # Mock plot data - simulates Firestore plots collection
        self.plots_data = [
            {
                "plotName": "GSEZ-R-001",
                "plotStatus": "Available",
                "category": "Residential",
                "phase": 1,
                "areaInSqm": 5000.0,
                "areaInHa": 0.5,
                "zoneCode": "GSEZ",
                "country": "Gabon",
                "sector": "Housing",
                "activity": "Residential Development",
                "companyName": None,
                "allocatedDate": None,
                "expiryDate": None,
                "investmentAmount": None,
                "employmentGenerated": None
            },
            {
                "plotName": "GSEZ-C-002",
                "plotStatus": "Allocated",
                "category": "Commercial",
                "phase": 1,
                "areaInSqm": 10000.0,
                "areaInHa": 1.0,
                "zoneCode": "GSEZ",
                "country": "Gabon",
                "sector": "Technology",
                "activity": "Software Development",
                "companyName": "TechCorp Ltd",
                "allocatedDate": "2024-01-15",
                "expiryDate": "2029-01-15",
                "investmentAmount": 500000.0,
                "employmentGenerated": 25
            },
            {
                "plotName": "OSEZ-I-001",
                "plotStatus": "Available",
                "category": "Industrial",
                "phase": 2,
                "areaInSqm": 20000.0,
                "areaInHa": 2.0,
                "zoneCode": "OSEZ",
                "country": "Gabon",
                "sector": "Manufacturing",
                "activity": None,
                "companyName": None,
                "allocatedDate": None,
                "expiryDate": None,
                "investmentAmount": None,
                "employmentGenerated": None
            }
        ]
        
        # Mock zone data - simulates Firestore zones collection
        self.zones_data = [
            {
                "country": "Gabon",
                "zoneCode": "GSEZ",
                "phase": 1,
                "landArea": 100.5,
                "zoneName": "Gabon Special Economic Zone",
                "zoneType": "SEZ",
                "establishedDate": "2020-01-01"
            },
            {
                "country": "Gabon",
                "zoneCode": "OSEZ",
                "phase": 2,
                "landArea": 250.0,
                "zoneName": "Owendo Special Economic Zone",
                "zoneType": "Industrial",
                "establishedDate": "2021-06-01"
            }
        ]

    # Update this method to use instance method
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
        
        # Start with all plots
        filtered_plots = self.plots_data.copy()
        
        # Apply role-based filtering first (as per flowchart logic)
        if is_zone_admin and user_zone:
            # Zone admin only sees plots in their zone
            filtered_plots = [
                plot for plot in filtered_plots 
                if plot["zoneCode"] == user_zone
            ]
        
        # Apply query parameter filters
        if query_params.country:
            filtered_plots = [
                plot for plot in filtered_plots
                if plot["country"].lower() == query_params.country.lower()
            ]
        
        if query_params.zoneCode:
            filtered_plots = [
                plot for plot in filtered_plots
                if plot["zoneCode"] == query_params.zoneCode
            ]
            
        if query_params.category:
            filtered_plots = [
                plot for plot in filtered_plots
                if plot["category"] == query_params.category.value
            ]
            
        if query_params.phase:
            filtered_plots = [
                plot for plot in filtered_plots
                if plot["phase"] == query_params.phase
            ]
        
        # Convert to Pydantic models for API response
        return [PlotResponse(**plot) for plot in filtered_plots]

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
        # Find the plot
        plot_index = None
        for i, plot in enumerate(self.plots_data):
            if (plot["plotName"] == request.plotName and 
                plot["zoneCode"] == request.zoneCode and 
                plot["country"] == request.country):
                plot_index = i
                break
        
        if plot_index is None:
            raise ValueError("Plot not found")
        
        # Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Update plot data with all provided fields
        plot = self.plots_data[plot_index]
        plot.update({
            "phase": request.phase,
            "plotStatus": request.plotStatus.value,
            "companyName": request.companyName,
            "sector": request.sector,
            "activity": request.activity,
            "investmentAmount": request.investmentAmount,
            "employmentGenerated": request.employmentGenerated,
            "allocatedDate": request.allocatedDate.isoformat() if request.allocatedDate else None,
            "expiryDate": request.expiryDate.isoformat() if request.expiryDate else None
        })
        
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
        # Find the plot
        plot_index = None
        for i, plot in enumerate(self.plots_data):
            if (plot["plotName"] == request.plotName and 
                plot["zoneCode"] == request.zoneCode and 
                plot["country"] == request.country):
                plot_index = i
                break
        
        if plot_index is None:
            raise ValueError("Plot not found")
        
        # Check zone access for zone_admin
        if user_zone and user_zone != request.zoneCode:
            raise PermissionError("Access denied: plot not in your assigned zone")
        
        # Release the plot - clear allocation data
        plot = self.plots_data[plot_index]
        plot.update({
            "plotStatus": "Available",
            "companyName": None,
            "allocatedDate": None,
            "expiryDate": None,
            "investmentAmount": None,
            "employmentGenerated": None,
            "activity": None
        })
        
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
        # Check if zone already exists
        for zone in self.zones_data:
            if zone["zoneCode"] == request.zoneCode:
                raise ValueError("Zone code already exists")
        
        # Add new zone
        new_zone = {
            "country": request.country,
            "zoneCode": request.zoneCode,
            "phase": request.phase,
            "landArea": request.landArea,
            "zoneName": request.zoneName,
            "zoneType": request.zoneType,
            "establishedDate": request.establishedDate.isoformat() if request.establishedDate else None
        }
        
        self.zones_data.append(new_zone)
        
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
        
        # Filter plots by country and zone
        filtered_plots = [
            plot for plot in self.plots_data 
            if plot["country"] == params.country and plot["zoneCode"] == params.zoneCode
        ]
        
        # Calculate metadata
        total_plots = len(filtered_plots)
        available_plots = len([plot for plot in filtered_plots if plot["plotStatus"] == "Available"])
        
        metadata = PlotDetailsMetadata(
            country=params.country,
            zoneCode=params.zoneCode,
            totalPlots=total_plots,
            availablePlots=available_plots
        )
        
        # Format plot details
        plot_items = []
        for plot in filtered_plots:
            plot_item = PlotDetailsItem(
                plotName=plot["plotName"],
                category=plot["category"],
                areaInHa=plot["areaInHa"],
                sector=plot["sector"],
                activity=plot["activity"],
                plotStatus=plot["plotStatus"],
                companyName=plot["companyName"],
                allocatedDate=datetime.fromisoformat(plot["allocatedDate"]).date() if plot["allocatedDate"] else None,
                investmentAmount=plot["investmentAmount"],
                employmentGenerated=plot["employmentGenerated"]
            )
            plot_items.append(plot_item)
        
        return PlotDetailsResponse(metadata=metadata, plots=plot_items)

