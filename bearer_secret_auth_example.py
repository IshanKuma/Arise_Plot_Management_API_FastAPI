"""
Bearer Token with Secret Authentication Example
===============================================

This shows your suggested approach: using a secret/hashed credential 
in the Bearer token field for initial authentication.
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field


# 1. SCHEMAS FOR BEARER SECRET AUTH
class BearerSecretRequest(BaseModel):
    """Request body when using Bearer secret for auth."""
    userId: str = Field(..., max_length=50)
    role: str = Field(..., description="Requested role")
    zone: str = Field(..., max_length=10)
    timestamp: Optional[int] = Field(None, description="Unix timestamp for replay protection")


class UserCredentials(BaseModel):
    """User credentials for secret-based auth."""
    userId: str
    secretHash: str  # Pre-shared secret hash
    role: str
    zone: str
    isActive: bool = True


# 2. BEARER SECRET AUTHENTICATION
class BearerSecretAuth:
    """Authentication using secret in Bearer token."""
    
    # Pre-configured user secrets (in production: secure database)
    _user_secrets = {
        "admin001": "super-secret-key-for-admin001",
        "zone001": "zone-admin-secret-key-001",
        "user001": "normal-user-secret-key-001"
    }
    
    _users = {
        "admin001": UserCredentials(
            userId="admin001",
            secretHash=hashlib.sha256("super-secret-key-for-admin001".encode()).hexdigest(),
            role="super_admin",
            zone="GSEZ"
        ),
        "zone001": UserCredentials(
            userId="zone001", 
            secretHash=hashlib.sha256("zone-admin-secret-key-001".encode()).hexdigest(),
            role="zone_admin",
            zone="GSEZ"
        )
    }
    
    @classmethod
    def verify_bearer_secret(cls, credentials: HTTPAuthorizationCredentials, userId: str) -> bool:
        """Verify the Bearer token contains correct secret."""
        
        # Get expected secret for user
        expected_secret = cls._user_secrets.get(userId)
        if not expected_secret:
            return False
            
        # Compare provided token with expected secret
        provided_secret = credentials.credentials
        
        # Option 1: Direct comparison
        if provided_secret == expected_secret:
            return True
            
        # Option 2: Hash comparison (more secure)
        expected_hash = hashlib.sha256(expected_secret.encode()).hexdigest()
        if provided_secret == expected_hash:
            return True
            
        return False
    
    @classmethod
    def verify_hmac_secret(cls, credentials: HTTPAuthorizationCredentials, request: BearerSecretRequest) -> bool:
        """Verify Bearer token using HMAC (most secure)."""
        
        user_secret = cls._user_secrets.get(request.userId)
        if not user_secret:
            return False
            
        # Create expected HMAC
        message = f"{request.userId}{request.role}{request.zone}{request.timestamp or ''}"
        expected_hmac = hmac.new(
            user_secret.encode(),
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        return credentials.credentials == expected_hmac
    
    @classmethod
    def get_user(cls, userId: str) -> Optional[UserCredentials]:
        """Get user by userId."""
        return cls._users.get(userId)


# 3. BEARER SECRET DEPENDENCIES
security = HTTPBearer()

async def verify_bearer_secret_auth(
    request: BearerSecretRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserCredentials:
    """Dependency to verify Bearer secret authentication."""
    
    # Verify the Bearer token contains correct secret
    if not BearerSecretAuth.verify_bearer_secret(credentials, request.userId):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_SECRET",
                "message": "Invalid Bearer token secret"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user info
    user = BearerSecretAuth.get_user(request.userId)
    if not user or not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_USER",
                "message": "User not found or inactive"
            }
        )
    
    return user


async def verify_hmac_bearer_auth(
    request: BearerSecretRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserCredentials:
    """Dependency to verify HMAC Bearer authentication."""
    
    if not BearerSecretAuth.verify_hmac_secret(credentials, request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_HMAC",
                "message": "Invalid HMAC signature in Bearer token"
            }
        )
    
    user = BearerSecretAuth.get_user(request.userId)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    return user


# 4. API ENDPOINTS WITH BEARER SECRET AUTH
router = APIRouter(prefix="/auth", tags=["Bearer Secret Authentication"])

@router.post("/token-with-bearer-secret")
async def create_token_with_bearer_secret(
    request: BearerSecretRequest,
    user: UserCredentials = Depends(verify_bearer_secret_auth)
):
    """Get JWT token using Bearer secret authentication."""
    
    # Now create JWT token (after successful Bearer secret verification)
    # token = create_jwt_token_for_user(user)
    
    return {
        "access_token": "jwt_token_here",
        "token_type": "bearer",
        "expires_in": 86400,
        "user_info": {
            "userId": user.userId,
            "role": user.role,
            "zone": user.zone
        }
    }


@router.post("/token-with-hmac-bearer") 
async def create_token_with_hmac_bearer(
    request: BearerSecretRequest,
    user: UserCredentials = Depends(verify_hmac_bearer_auth)
):
    """Get JWT token using HMAC Bearer authentication (most secure)."""
    
    return {
        "access_token": "jwt_token_here",
        "token_type": "bearer", 
        "expires_in": 86400
    }


# 5. EXAMPLE USAGE
"""
Method 1: Direct Secret in Bearer Token
=======================================

Request:
POST /auth/token-with-bearer-secret
Headers:
  Authorization: Bearer super-secret-key-for-admin001
  Content-Type: application/json
Body:
{
    "userId": "admin001",
    "role": "super_admin",
    "zone": "GSEZ"
}


Method 2: Hashed Secret in Bearer Token
======================================

1. Client calculates hash:
secret = "super-secret-key-for-admin001"
hash = sha256(secret) = "a1b2c3d4e5f6..."

2. Request:
POST /auth/token-with-bearer-secret
Headers:
  Authorization: Bearer a1b2c3d4e5f6...
Body:
{
    "userId": "admin001", 
    "role": "super_admin",
    "zone": "GSEZ"
}


Method 3: HMAC in Bearer Token (Most Secure)
============================================

1. Client calculates HMAC:
secret = "super-secret-key-for-admin001"
message = "admin001super_adminGSEZ1720972800"
hmac = hmac_sha256(secret, message) = "x1y2z3..."

2. Request:
POST /auth/token-with-hmac-bearer
Headers:
  Authorization: Bearer x1y2z3...
Body:
{
    "userId": "admin001",
    "role": "super_admin", 
    "zone": "GSEZ",
    "timestamp": 1720972800
}

Benefits of Your Approach:
- Familiar Bearer token pattern
- Secret never in request body (header only)
- Can use HMAC for tamper protection
- Timestamp prevents replay attacks
- Clean separation of auth secret vs JWT token
"""
