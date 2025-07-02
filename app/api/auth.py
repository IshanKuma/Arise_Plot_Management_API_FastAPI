"""
Authentication API routes for JWT token generation.
Implements POST /auth/token endpoint as per Flow 1 specifications.
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import AuthTokenRequest, AuthTokenResponse, AuthErrorResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "model": AuthErrorResponse,
            "description": "Bad Request - Invalid parameters"
        }
    },
    summary="Generate JWT Token",
    description="""
    Generate a JWT token for authenticated API access.
    
    **Flow 1: Authentication & Token Generation**
    
    This endpoint validates user credentials and returns a signed JWT token containing:
    - User identity (userId, role, zone)
    - Role-based permissions (read/write access)
    - Token expiration (24 hours)
    
    **Role-based Permissions:**
    - `super_admin`: Full read/write access to all zones
    - `zone_admin`: Read/write access to assigned zone only  
    - `normal_user`: Read-only access to plots
    
    **Valid Zone Codes:** GSEZ, OSEZ, GABON (4-6 uppercase letters)
    """
)
async def create_access_token(request: AuthTokenRequest) -> AuthTokenResponse:
    """
    Create JWT access token for API authentication.
    
    **Sequence of Events:**
    1. Validate request parameters (userId, role, zone)
    2. Check role validity (super_admin, zone_admin, normal_user)
    3. Assign role-based permissions
    4. Create signed JWT token with 24-hour expiry
    5. Return token response
    
    Args:
        request: Authentication request with userId, role, and zone
        
    Returns:
        AuthTokenResponse: JWT token with expiry information
        
    Raises:
        HTTPException: 400 Bad Request for validation errors
    """
    
    # Step 1: Validate request parameters
    validation_error = AuthService.validate_request(request)
    
    if validation_error == "INVALID_ROLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ROLE",
                "message": "Invalid role provided. Must be one of: super_admin, zone_admin, normal_user",
                "details": {"provided_role": request.role.value}
            }
        )
    
    if validation_error == "INVALID_ZONE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ZONE", 
                "message": "Invalid zone code. Must be a valid zone identifier (e.g., GSEZ, OSEZ)",
                "details": {"provided_zone": request.zone}
            }
        )
    
    # Step 2: Create JWT token with permissions
    try:
        access_token = AuthService.create_jwt_token(request)
        expires_in = AuthService.get_token_expiry_seconds()
        
        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to create access token",
                "details": {"error": str(e)}
            }
        )
