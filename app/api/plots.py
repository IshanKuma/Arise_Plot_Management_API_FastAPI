"""
Plots API routes for plot management operations.
Implements all plot-related endpoints as per API specifications.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from app.schemas.plots import (
    AvailablePlotsResponse, PlotQueryParams,
    PlotUpdateRequest, PlotUpdateResponse,
    PlotReleaseRequest, PlotReleaseResponse,
    PlotDetailsQueryParams, PlotDetailsResponse
)
from app.schemas.auth import JWTPayload
from app.utils.auth import require_plots_read, require_plots_write
from app.services.firestore import firestore_service

router = APIRouter(prefix="/plot", tags=["Plots"])
# Use the singleton firestore_service instance


@router.get(
    "/available",
    response_model=AvailablePlotsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {
            "description": "Unauthorized - Invalid or expired JWT token"
        },
        403: {
            "description": "Forbidden - Insufficient permissions"
        }
    },
    summary="Get Available Plots",
    description="""
    Retrieve available plots with optional filtering.
    
    **Flow 2: Available Plots Retrieval**
    
    This endpoint implements the complete flow from the diagram:
    1. **JWT Token Verification**: Validates Bearer token
    2. **Permission Check**: Ensures user has 'read' permission for plots
    3. **Role-Based Filtering**: 
       - `zone_admin`: Only sees plots in their assigned zone
       - `super_admin`/`normal_user`: Sees all plots (subject to query filters)
    4. **Query Filtering**: Apply optional filters (country, zoneCode, category, phase)
    5. **Firestore Query**: Retrieve matching plots from database
    6. **Response Formatting**: Return structured plot data
    
    **Query Parameters** (all optional):
    - `country`: Filter by country name
    - `zoneCode`: Filter by zone code (4-6 uppercase letters)
    - `category`: Filter by plot category (Residential, Commercial, Industrial)
    - `phase`: Filter by phase number (positive integer)
    - `limit`: Number of items per page (1-100, default: 50)
    - `cursor`: Cursor for pagination (document ID from previous page)
    
    **Role-Based Access**:
    - All roles need 'read' permission for plots
    - Zone admins automatically filtered to their assigned zone
    - Super admins and normal users see all zones (unless filtered)
    
    **Performance Optimization**:
    - Uses cursor-based pagination with Firebase limit() and startAfter()
    - Default limit: 50 items per request for optimal performance
    - Reduces database read costs and response times
    """
)
async def get_available_plots(
    country: Optional[str] = Query(None, max_length=50, description="Filter by country name"),
    zoneCode: Optional[str] = Query(None, max_length=10, description="Filter by zone code"),  
    category: Optional[str] = Query(None, description="Filter by category: Residential, Commercial, Industrial"),
    phase: Optional[int] = Query(None, ge=1, description="Filter by phase number"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page (1-100)"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (document ID from previous page)"),
    user: JWTPayload = Depends(require_plots_read)
) -> AvailablePlotsResponse:
    """
    Get available plots with filtering and role-based access control.
    
    **Sequence of Events (as per flowchart):**
    1. Verify JWT Token ✓ (handled by dependency)
    2. Extract User Payload ✓ (handled by dependency) 
    3. Check Read Permission ✓ (handled by dependency)
    4. Build Query Parameters
    5. Apply Role-Based Filtering
    6. Query Firestore Database
    7. Format and Return Response
    
    Args:
        country: Optional country filter
        zoneCode: Optional zone code filter
        category: Optional category filter  
        phase: Optional phase filter
        user: Authenticated user (injected by dependency)
        
    Returns:
        AvailablePlotsResponse: List of available plots
        
    Raises:
        HTTPException: 401/403 for auth errors (handled by dependencies)
    """
    
    # Step 4: Build Query Parameters
    # Validate category if provided
    valid_categories = ["Residential", "Commercial", "Industrial"]
    if category and category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_CATEGORY",
                "message": f"Invalid category. Must be one of: {', '.join(valid_categories)}",
                "details": {"provided_category": category}
            }
        )
    
    # Convert category string to enum if provided
    category_enum = None
    if category:
        from app.schemas.plots import PlotCategory
        category_enum = PlotCategory(category)
    
    # Create query parameters object with pagination
    query_params = PlotQueryParams(
        country=country,
        zoneCode=zoneCode,
        category=category_enum,
        phase=phase,
        limit=limit,
        cursor=cursor
    )
    
    # Step 5: Apply Role-Based Filtering (as per flowchart)
    is_zone_admin = user.role == "zone_admin"
    user_zone = user.zone if is_zone_admin else None
    
    # Step 6: Query Firestore Database with pagination
    try:
        plots, pagination_meta = firestore_service.get_available_plots(
            query_params=query_params,
            user_zone=user_zone,
            is_zone_admin=is_zone_admin
        )
        
        # Step 7: Format and Return Response with pagination
        from app.schemas.plots import PaginationMeta
        pagination = PaginationMeta(**pagination_meta)
        return AvailablePlotsResponse(plots=plots, pagination=pagination)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve plots",
                "details": {"error": str(e)}
            }
        )


@router.put(
    "/update-plot",
    response_model=PlotUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid or expired JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Plot not found"}
    },
    summary="Update Plot Information",
    description="""
    Update plot information with complete business allocation details.
    
    **Logic**: Complete resource update (PUT semantics) for plot allocation.
    Used when allocating a plot to a company with full business details.
    
    **Role-Based Access**:
    - Requires 'write' permission for plots
    - Zone admins can only update plots in their assigned zone
    - Super admins can update plots in any zone
    
    **Business Validation**:
    - Plot must exist in specified country and zone
    - Zone access enforced for zone_admin role
    - All optional business fields can be updated
    """
)
async def update_plot(
    request: PlotUpdateRequest,
    user: JWTPayload = Depends(require_plots_write)
) -> PlotUpdateResponse:
    """
    Update plot information with business allocation details.
    
    Args:
        request: Plot update request with all business details
        user: Authenticated user (injected by dependency)
        
    Returns:
        PlotUpdateResponse: Success response with plot details
        
    Raises:
        HTTPException: 404 if plot not found, 403 if zone access denied
    """
    try:
        user_zone = user.zone if user.role == "zone_admin" else None
        result = await firestore_service.update_plot(request, user_zone)
        return PlotUpdateResponse(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PLOT_NOT_FOUND",
                "message": str(e)
            }
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
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


@router.patch(
    "/update-plot", 
    response_model=PlotReleaseResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid or expired JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Plot not found"}
    },
    summary="Update Plot Status",
    description="""
    Update plot status with minimal request data.
    
    **Logic**: Partial resource update (PATCH semantics) for plot status changes.
    Different from PUT /update-plot - only changes status, doesn't update all business details.
    
    **Status Options**:
    - PATCH: Updates only plot status - can be 'Available' or 'Occupied'
    - PUT: Complete update - updates full business allocation details
    - Different business logic and validation requirements
    
    **Role-Based Access**:
    - Requires 'write' permission for plots  
    - Zone admins can only update plots in their assigned zone
    - Super admins can update plots in any zone
    """
)
async def update_plot_status(
    request: PlotReleaseRequest,
    user: JWTPayload = Depends(require_plots_write)
) -> PlotReleaseResponse:
    """
    Update plot status with minimal request data.
    
    Args:
        request: Plot status update request with minimal required fields
        user: Authenticated user (injected by dependency)
        
    Returns:
        PlotReleaseResponse: Success response with plot details
        
    Raises:
        HTTPException: 404 if plot not found, 403 if zone access denied
    """
    try:
        user_zone = user.zone if user.role == "zone_admin" else None
        result = await firestore_service.release_plot(request, user_zone)
        return PlotReleaseResponse(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PLOT_NOT_FOUND", 
                "message": str(e)
            }
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
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


@router.get(
    "/plot-detail",
    response_model=PlotDetailsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid or expired JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"}
    },
    summary="Get Plot Details",
    description="""
    Get detailed plot information for a specific zone.
    
    **Logic**: Returns comprehensive plot data including business allocation details.
    Provides metadata with summary statistics and detailed plot information.
    
    **Role-Based Access**:
    - Requires 'read' permission for plots
    - Zone admins can only access plots in their assigned zone
    - Super admins and normal users can access plots in any zone
    
    **Response Format**:
    - metadata: Summary statistics (total plots, available plots)
    - plots: Array of detailed plot information with business data
    """
)
async def get_plot_details(
    country: str = Query(..., max_length=50, description="Country name"),
    zoneCode: str = Query(..., max_length=10, description="Zone code"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page (1-100)"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (document ID from previous page)"),
    user: JWTPayload = Depends(require_plots_read)
) -> PlotDetailsResponse:
    """
    Get detailed plot information for a specific zone with pagination.
    
    Args:
        country: Country name (required)
        zoneCode: Zone code (required)
        limit: Number of items per page (1-100, default: 50)
        cursor: Cursor for pagination (document ID from previous page)
        user: Authenticated user (injected by dependency)
        
    Returns:
        PlotDetailsResponse: Detailed plot information with metadata and pagination
        
    Raises:
        HTTPException: 403 if zone access denied
    """
    try:
        params = PlotDetailsQueryParams(country=country, zoneCode=zoneCode, limit=limit, cursor=cursor)
        user_zone = user.zone if user.role == "zone_admin" else None
        result = await firestore_service.get_plot_details(params, user_zone)
        return result
    
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCESS_DENIED",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR", 
                "message": "Failed to retrieve plot details",
                "details": {"error": str(e)}
            }
        )
