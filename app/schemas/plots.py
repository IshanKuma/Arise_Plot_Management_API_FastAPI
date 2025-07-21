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
    ALLOCATED = "Allocated"
    RESERVED = "Reserved"


class PlotResponse(BaseModel):
    """
    Individual plot response schema for GET /plots/available endpoint.
    
    As per API specification:
    - All fields are mandatory in response
    - Matches the format specified in flowchart
    """
    plotName: str = Field(..., max_length=50, description="Unique plot identifier")
    plotStatus: PlotStatus = Field(..., description="Available, Allocated, Reserved")
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


class AvailablePlotsResponse(BaseModel):
    """
    Response schema for GET /plots/available endpoint.
    
    As per API specification:
    - plots: array of plot objects, mandatory
    """
    plots: List[PlotResponse] = Field(..., description="Array of plot objects")

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
                    },
                    {
                        "plotName": "GSEZ-COM-002", 
                        "plotStatus": "Available",
                        "category": "Commercial",
                        "phase": 2,
                        "areaInSqm": 2500.50,
                        "areaInHa": 0.25,
                        "zoneCode": "GSEZ",
                        "country": "Gabon"
                    }
                ]
            }
        }


class PlotQueryParams(BaseModel):
    """
    Query parameters for GET /plots/available endpoint.
    
    As per API specification:
    - All parameters are optional
    - Used for filtering plots
    """
    country: Optional[str] = Field(None, max_length=50, description="Filter by country name")
    zoneCode: Optional[str] = Field(None, max_length=10, description="Filter by zone code")
    category: Optional[PlotCategory] = Field(None, description="Filter by plot category")
    phase: Optional[int] = Field(None, ge=1, description="Filter by phase number (positive integer)")

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
                "phase": 2
            }
        }


class PlotUpdateRequest(BaseModel):
    """
    Request schema for PUT /update-plot endpoint.
    
    Logic: Complete plot update with business allocation details.
    Used when allocating a plot to a company with full information.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Zone code")
    phase: int = Field(..., gt=0, description="Phase number (positive integer)")
    plotName: str = Field(..., max_length=50, description="Plot identifier")
    companyName: Optional[str] = Field(None, max_length=100, description="Company name for allocation")
    sector: Optional[str] = Field(None, max_length=50, description="Business sector")
    plotStatus: PlotStatus = Field(..., description="Plot status")
    activity: Optional[str] = Field(None, max_length=100, description="Business activity description")
    investmentAmount: Optional[float] = Field(None, ge=0, description="Investment amount in USD")
    employmentGenerated: Optional[int] = Field(None, ge=0, description="Number of jobs created")
    allocatedDate: Optional[date] = Field(None, description="Allocation date (YYYY-MM-DD)")
    expiryDate: Optional[date] = Field(None, description="Expiry date (YYYY-MM-DD)")

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
                "phase": 1,
                "plotName": "GSEZ-R-001",
                "companyName": "TechCorp Ltd",
                "sector": "Technology",
                "plotStatus": "Allocated",
                "activity": "Software Development",
                "investmentAmount": 1000000.0,
                "employmentGenerated": 50,
                "allocatedDate": "2024-07-04",
                "expiryDate": "2029-07-04"
            }
        }


class PlotUpdateResponse(BaseModel):
    """Response schema for PUT /update-plot endpoint."""
    message: str = Field(..., max_length=100)
    plotName: str = Field(..., max_length=50)
    status: str = Field(..., max_length=20)


class PlotReleaseRequest(BaseModel):
    """
    Request schema for PATCH /release-plot endpoint.
    
    Logic: Minimal request for releasing a plot back to available status.
    Different from PUT because it only changes status, doesn't update business details.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Zone code")
    plotName: str = Field(..., max_length=50, description="Plot identifier")
    plotStatus: str = Field(..., description="Must be 'available'")

    @validator('plotStatus')
    def validate_plot_status(cls, v):
        if v.lower() != 'available':
            raise ValueError('Plot status must be "available" for release operation')
        return v.lower()

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
                "plotName": "GSEZ-C-002",
                "plotStatus": "available"
            }
        }


class PlotReleaseResponse(BaseModel):
    """Response schema for PATCH /release-plot endpoint."""
    message: str = Field(..., max_length=100)
    plotName: str = Field(..., max_length=50)
    status: str = Field(..., max_length=20)


class ZoneCreateRequest(BaseModel):
    """
    Request schema for POST /country/zones endpoint.
    
    Logic: Creates or updates zone master data.
    Essential for establishing economic zones before creating plots.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Unique zone identifier")
    phase: int = Field(..., gt=0, description="Phase number (positive integer)")
    landArea: float = Field(..., gt=0, description="Total land area in hectares")
    zoneName: Optional[str] = Field(None, max_length=100, description="Descriptive zone name")
    zoneType: Optional[str] = Field(None, max_length=30, description="SEZ, Industrial, Commercial")
    establishedDate: Optional[date] = Field(None, description="Establishment date (YYYY-MM-DD)")

    @validator('zoneCode')
    def validate_zone_code(cls, v):
        if not v.isupper() or not (4 <= len(v) <= 6) or not v.isalpha():
            raise ValueError('Zone code must be 4-6 uppercase letters')
        return v

    @validator('zoneType')
    def validate_zone_type(cls, v):
        if v and v not in ['SEZ', 'Industrial', 'Commercial']:
            raise ValueError('Zone type must be one of: SEZ, Industrial, Commercial')
        return v

    class Config:
        schema_extra = {
            "example": {
                "country": "Gabon",
                "zoneCode": "NSEZ",
                "phase": 1,
                "landArea": 150.5,
                "zoneName": "New Special Economic Zone",
                "zoneType": "SEZ",
                "establishedDate": "2024-07-04"
            }
        }


class ZoneCreateResponse(BaseModel):
    """Response schema for POST /country/zones endpoint."""
    message: str = Field(..., max_length=100)
    zoneCode: str = Field(..., max_length=10)


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
    
    Logic: Simple country and zone filter for detailed plot information.
    """
    country: str = Field(..., max_length=50, description="Country name")
    zoneCode: str = Field(..., max_length=10, description="Zone code")

    @validator('zoneCode')
    def validate_zone_code(cls, v):
        if not v.isupper() or not (4 <= len(v) <= 6) or not v.isalpha():
            raise ValueError('Zone code must be 4-6 uppercase letters')
        return v


class PlotDetailsResponse(BaseModel):
    """Response schema for GET /plot-details endpoint."""
    metadata: PlotDetailsMetadata
    plots: List[PlotDetailsItem]

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
                ]
            }
        }
