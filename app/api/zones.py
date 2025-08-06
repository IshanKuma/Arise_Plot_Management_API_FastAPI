"""
Zones API routes for zone master data management.
Implements POST /country/zones endpoint as per API specifications.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.plots import ZoneCreateRequest, ZoneCreateResponse
from app.schemas.auth import JWTPayload
from app.utils.auth import require_zones_write
from app.services.firestore import firestore_service

router = APIRouter(prefix="/country", tags=["Zones"])
# Use the singleton firestore_service instance


@router.post(
    "/zone",
    response_model=ZoneCreateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid or expired JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        409: {"description": "Zone code already exists"}
    },
    summary="Create Zone Master Data",
    description="""
    Create or update zone master data for economic zones.
    
    **Logic**: Essential for establishing economic zones before creating plots.
    Zone master data provides the foundation for plot management within zones.
    
    **Role-Based Access**:
    - Requires 'write' permission for zones
    - Only super_admin and zone_admin can create zones
    - Zone admins typically create zones for their assigned areas
    
    **Business Validation**:
    - Zone code must be unique across the system
    - Zone code format: any zone identifier (e.g., GSEZ, PIA, BSEZ)
    - Zone type must be one of: SEZ, Industrial, Commercial
    - Land area must be positive value in hectares
    
    **Use Cases**:
    - Setting up new economic zones
    - Updating zone information
    - Preparing infrastructure for plot allocation
    """
)
async def create_zone(
    request: ZoneCreateRequest,
    user: JWTPayload = Depends(require_zones_write)
) -> ZoneCreateResponse:
    """
    Create or update zone master data.
    
    Args:
        request: Zone creation request with zone details
        user: Authenticated user (injected by dependency)
        
    Returns:
        ZoneCreateResponse: Success response with zone code
        
    Raises:
        HTTPException: 409 if zone exists, 400 for validation errors
    """
    try:
        result = await firestore_service.create_zone(request)
        return ZoneCreateResponse(**result)
    
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "ZONE_EXISTS",
                    "message": str(e),
                    "details": {
                        "zone_code": request.zoneCode,
                        "country": request.country
                    }
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_DATA",
                    "message": str(e)
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            }
        )
