"""
Authentication API routes for JWT token generation.
Implements POST /auth/token endpoint as per Flow 1 specifications.
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
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
        },
        401: {
            "model": AuthErrorResponse,
            "description": "Unauthorized - Invalid secret key"
        }
    },
    summary="Generate JWT Token with Secret Key Authentication",
    description="""
    Generate a JWT token for authenticated API access with dual-layer security.
    
    **Flow 1: Authentication & Token Generation (Hybrid Security)**
    
    This endpoint requires:
    1. Valid user credentials (userId, role, zone)
    2. Authentication secret key for additional security
    
    **Security Model:**
    - **Layer 1**: Secret key validation via Authorization header ("Secret <key>")
    - **Layer 2**: JWT token signing using server-side secret (HS256)
    
    The returned JWT token contains:
    - User identity (userId, role, zone)
    - Role-based permissions (read/write access)
    - Token expiration (24 hours)
    
    **Authorization Header Format:**
    ```
    Authorization: Secret arise-master-auth-secret-2025
    ```
    
    **Role-based Permissions:**
    - `super_admin`: Full read/write access to all zones
    - `zone_admin`: Read/write access to assigned zone only  
    - `normal_user`: Read-only access to plots
    
    **Valid Zone Codes:** GSEZ, OSEZ, GABON (4-6 uppercase letters)
    """
)
async def create_access_token(
    request: AuthTokenRequest,
    authorization: Optional[str] = Header(None, description="Authorization header with secret key")
) -> AuthTokenResponse:
    """
    Create JWT access token for API authentication with dual-layer security.
    
    **Sequence of Events:**
    1. Extract and validate secret key from Authorization header
    2. Validate request parameters (userId, role, zone)
    3. Check role validity (super_admin, zone_admin, normal_user)
    4. Assign role-based permissions
    5. Create signed JWT token with server-side secret (24-hour expiry)
    6. Return token response
    
    **Security Model:**
    - Authorization header validates permission to generate tokens
    - JWT token is signed with separate server-side secret for verification
    
    **Header Format:**
    ```
    Authorization: Secret arise-master-auth-secret-2025
    ```
    
    Args:
        request: Authentication request with userId, role, and zone
        authorization: Authorization header containing "Secret <secret-key>"
        
    Returns:
        AuthTokenResponse: JWT token with expiry information
        
    Raises:
        HTTPException: 401 Unauthorized for missing/invalid secret key
        HTTPException: 400 Bad Request for validation errors
    """
    
    # Step 1: Extract and validate secret key from Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "MISSING_AUTHORIZATION",
                "message": "Authorization header is required",
                "details": {"expected_format": "Authorization: Secret <secret-key>"}
            }
        )
    
    # Parse Authorization header (expected format: "Secret <secret-key>")
    auth_parts = authorization.split(" ", 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "secret":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_AUTHORIZATION_FORMAT",
                "message": "Invalid Authorization header format",
                "details": {"expected_format": "Authorization: Secret <secret-key>"}
            }
        )
    
    secret_key = auth_parts[1]
    
    # Step 2: Validate request parameters including secret key
    validation_error = AuthService.validate_request(request, secret_key)
    
    if validation_error == "INVALID_SECRET_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Invalid authentication secret key",
                "details": {"reason": "Secret key mismatch"}
            }
        )
    
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
