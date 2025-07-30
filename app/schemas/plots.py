"""
Plot-related Pydantic schemas for request/response validation.
Based on API specifications for plots endpoints.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from datetime import date
from enum import Enum


class PlotCategory(str, Enum):
    """Valid plot categories as per API specification."""
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial" 
    INDUSTRIAL = "Industrial"


class PlotStatus(str, Enum):
    """Valid plot status values as per API specification."""
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"


class PlotResponse(BaseModel):
    """
    Individual plot response schema for GET /plots/available endpoint.
    
    As per API specification:
    - All fields are mandatory in response
    - Matches the format specified in flowchart
    """
    plotName: str = Field(..., max_length=50, description="Unique plot identifier")
    plotStatus: PlotStatus = Field(..., description="Available, Occupied, Reserved")
    category: PlotCategory = Field(..., description="Residential, Commercial, Industrial")
    phase: int = Field(..., description="Phase number")
    areaInSqm: Decimal = Field(..., description="Area in square meters")
    areaInHa: Decimal = Field(..., description="Area in hectares")
    zoneCode: str = Field(..., max_length=10, description="Zone code")
    country: str = Field(..., max_length=50, description="Country name")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "plotName": "GSEZ-RES-001",
                "plotStatus": "Available",
                "category": "Residential", 
                "phase": 1,
                "areaInSqm": 1000.00,
                "areaInHa": 0.10,
                "zoneCode": "GSEZ",
                "country": "Gabon"
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata for paginated responses."""
    limit: int = Field(..., description="Items per page")
    hasNextPage: bool = Field(..., description="Whether there are more items")
    nextCursor: Optional[str] = Field(None, description="Cursor for next page (if hasNextPage is true)")
    totalReturned: int = Field(..., description="Number of items in current response")


class AvailablePlotsResponse(BaseModel):
    """
    Response schema for GET /plots/available endpoint.
    
    As per API specification:
    - plots: array of plot objects, mandatory
    - pagination: metadata for cursor-based pagination
    """
    plots: List[PlotResponse] = Field(..., description="Array of plot objects")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "plots": [
                    {
                        "plotName": "GSEZ-RES-001",
                        "plotStatus": "Available",
                        "category": "Residential",
                        "phase": 1,
                        "areaInSqm": 1000.00,
                        "areaInHa": 0.10,
                        "zoneCode": "GSEZ",
                        "country": "Gabon"
                    }
                ],
                "pagination": {
                    "limit": 50,
                    "hasNextPage": True,
                    "nextCursor": "plot_doc_id_456",
                    "totalReturned": 50
                }
            }
        }


class PlotQueryParams(BaseModel):
    """
    Query parameters for GET /plots/available endpoint.
    
    As per API specification:
    - All parameters are optional
    - Used for filtering plots
    - Pagination parameters added for performance optimization
    """
    country: Optional[str] = Field(None, max_length=50, description="Filter by country name")
    zoneCode: Optional[str] = Field(None, max_length=10, description="Filter by zone code")
    category: Optional[PlotCategory] = Field(None, description="Filter by plot category")
    phase: Optional[int] = Field(None, ge=1, description="Filter by phase number (positive integer)")
    
    # Pagination parameters
    limit: Optional[int] = Field(50, ge=1, le=100, description="Number of items per page (1-100, default: 50)")
    cursor: Optional[str] = Field(None, description="Cursor for pagination (document ID from previous page)")
    
    @validator('zoneCode')
    def validate_zone_code(cls, v):
        """Validate zone code format if provided."""
        if v and (not v.isalpha() or not v.isupper() or not (4 <= len(v) <= 6)):
            raise ValueError('Zone code must be 4-6 uppercase letters (e.g., GSEZ, OSEZ)')
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "country": "Gabon",
                "zoneCode": "GSEZ", 
                "category": "Residential",
                "phase": 2,
                "limit": 50,
                "cursor": "plot_doc_id_123"
            }
        }


class PlotUpdateRequest(BaseModel):
    """
    Request schema for PUT /update-plot endpoint.
    
    Logic: Simple plot update matching GET response format exactly.
    """
    plotName: str = Field(..., max_length=50, description="Plot identifier")
    plotStatus: PlotStatus = Field(..., description="Plot status")
    category: PlotCategory = Field(..., description="Plot category")
    phase: int = Field(..., description="Phase number")
    areaInSqm: str = Field(..., description="Area in square meters as string")
    areaInHa: str = Field(..., description="Area in hectares as string")
    zoneCode: str = Field(..., max_length=10, description="Zone code")
    country: str = Field(..., max_length=50, description="Country name")

    class Config:
        schema_extra = {
            "example": {
                "plotName": "C-4G  TEMPORARY",
                "plotStatus": "Available",
                "category": "Industrial", 
                "phase": 1,
                "areaInSqm": "0.0",
                "areaInHa": "0.0",
                "zoneCode": "UNKNOWN",
                "country": "Gabon"
            }
        }


class PlotUpdateResponse(BaseModel):
    """Response schema for PUT /update-plot endpoint."""
    message: str = Field(..., max_length=100)
    plotName: str = Field(..., max_length=50)
    status: str = Field(..., max_length=20)


class PlotReleaseRequest(BaseModel):
    """
    Request schema for PATCH /update-plot endpoint.
    
    Logic: Minimal request for updating plot status.
    Can set status to either 'Available' or 'Occupied'.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: Optional[str] = Field(None, max_length=10, description="Zone code (optional - will be looked up)")
    plotName: str = Field(..., max_length=50, description="Plot identifier")
    plotStatus: str = Field(..., description="Plot status: 'Available' or 'Occupied'")

    @validator('plotStatus')
    def validate_plot_status(cls, v):
        valid_statuses = ['available', 'occupied']
        if v.lower() not in valid_statuses:
            raise ValueError('Plot status must be either "Available" or "Occupied"')
        return v.title()  # Convert to title case (Available/Occupied)

    @validator('zoneCode')
    def validate_zone_code(cls, v):
        if v and (not v.isupper() or not (4 <= len(v) <= 6) or not v.isalpha()):
            raise ValueError('Zone code must be 4-6 uppercase letters')
        return v

    class Config:
        schema_extra = {
            "example": {
                "country": "Gabon",
                "plotName": "C-4G  TEMPORARY", 
                "plotStatus": "Available"
            }
        }


class PlotReleaseResponse(BaseModel):
    """Response schema for PATCH /release-plot endpoint."""
    message: str = Field(..., max_length=100)
    plotName: str = Field(..., max_length=50)
    zoneCode: str = Field(..., max_length=10, description="Zone code of the released plot")
    status: str = Field(..., max_length=20)


class ZoneCreateRequest(BaseModel):
    """
    Request schema for POST /country/zones endpoint.
    
    Logic: Creates or updates zone master data.
    Essential for establishing economic zones before creating plots.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Unique zone identifier")
    phase: str = Field(..., description="Phase number as string")
    landArea: str = Field(..., description="Land area with unit (e.g., '120 Ha')")

    @validator('zoneCode')
    def validate_zone_code(cls, v):
        if not v.isupper() or not (4 <= len(v) <= 6) or not v.isalpha():
            raise ValueError('Zone code must be 4-6 uppercase letters')
        return v

    class Config:
        schema_extra = {
            "example": {
                "country": "Gabon",
                "zoneCode": "GSEZ",
                "phase": "1",
                "landArea": "120 Ha"
            }
        }


class ZoneCreateResponse(BaseModel):
    """Response schema for POST /country/zones endpoint."""
    country: str = Field(..., max_length=50)
    zoneCode: str = Field(..., max_length=10)
    phase: str = Field(..., description="Phase number as string")
    landArea: str = Field(..., description="Land area with unit")


class PlotDetailsMetadata(BaseModel):
    """
    Metadata section for plot details response.
    
    Logic: Provides summary statistics for the requested zone.
    """
    country: str = Field(..., max_length=50)
    zoneCode: str = Field(..., max_length=10)
    totalPlots: int = Field(..., ge=0)
    availablePlots: int = Field(..., ge=0)


class PlotDetailsItem(BaseModel):
    """
    Simplified plot item for plot details response.
    
    Logic: Returns only essential plot information without null-heavy fields.
    Focuses on core plot identification and basic characteristics.
    """
    plotName: str = Field(..., max_length=50, description="Plot identifier")
    status: str = Field(..., max_length=20, description="Plot status")
    category: str = Field(..., max_length=20, description="Plot category")
    phase: str = Field(..., max_length=10, description="Development phase")
    areaInSqm: float = Field(..., ge=0, description="Area in square meters")
    areaInHa: float = Field(..., ge=0, description="Area in hectares")
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Zone code")


class PlotDetailsQueryParams(BaseModel):
    """
    Query parameters for GET /plot-details endpoint.
    
    Logic: Country and zone filter with pagination for detailed plot information.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Zone code")
    
    # Pagination parameters
    limit: Optional[int] = Field(50, ge=1, le=100, description="Number of items per page (1-100, default: 50)")
    cursor: Optional[str] = Field(None, description="Cursor for pagination (document ID from previous page)")

    @validator('zoneCode')
    def validate_zone_code(cls, v):
        if not v.isupper() or not (4 <= len(v) <= 6) or not v.isalpha():
            raise ValueError('Zone code must be 4-6 uppercase letters')
        return v


class PlotDetailsResponse(BaseModel):
    """Response schema for GET /plot-details endpoint with pagination."""
    metadata: PlotDetailsMetadata
    plots: List[PlotDetailsItem]
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "country": "Gabon",
                    "zoneCode": "GSEZ",
                    "totalPlots": 10,
                    "availablePlots": 7
                },
                "plots": [
                    {
                        "plotName": "GSEZ-R-001",
                        "category": "Residential",
                        "areaInHa": 0.5,
                        "sector": "Housing",
                        "activity": None,
                        "plotStatus": "Available",
                        "companyName": None,
                        "allocatedDate": None,
                        "investmentAmount": None,
                        "employmentGenerated": None
                    }
                ],
                "pagination": {
                    "limit": 50,
                    "hasNextPage": False,
                    "nextCursor": None,
                    "totalReturned": 10
                }
            }
        }
