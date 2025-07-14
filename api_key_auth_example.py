"""
API Key / Secret-Based Authentication Example
============================================

This shows how to use API keys or secret credentials for authentication.
Good for service-to-service communication or when passwords aren't suitable.
"""
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field


# 1. NEW SCHEMAS FOR API KEY AUTH
class ApiKeyLoginRequest(BaseModel):
    """Login request with userId and API key."""
    userId: str = Field(..., max_length=50, description="User identifier")
    apiKey: str = Field(..., min_length=32, max_length=128, description="User API key")
    # Optional: include role and zone, or derive from userId


class HashedSecretLoginRequest(BaseModel):
    """Login request with userId and hashed secret."""
    userId: str = Field(..., max_length=50)
    role: str = Field(..., description="Requested role")
    zone: str = Field(..., max_length=10)
    secretHash: str = Field(..., description="SHA-256 hash of secret + userId + timestamp")
    timestamp: int = Field(..., description="Unix timestamp (for replay protection)")


class UserApiKey(BaseModel):
    """User model with API key credentials."""
    userId: str
    apiKey: str  # Store securely, treat like password
    role: str
    zone: str
    isActive: bool = True
    createdDate: datetime


# 2. API KEY MANAGEMENT
class ApiKeyManager:
    """Manage API keys for users."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key."""
        return secrets.token_urlsafe(32)  # 256-bit key
    
    @staticmethod
    def hash_secret(secret: str, userId: str, timestamp: int) -> str:
        """Create hash for secret-based auth."""
        data = f"{secret}{userId}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()


# 3. API KEY AUTHENTICATION SERVICE  
class ApiKeyAuthService:
    """Authentication using API keys."""
    
    # In production: store in secure database
    _user_keys: Dict[str, UserApiKey] = {}
    _api_key_to_user: Dict[str, str] = {}  # apiKey -> userId mapping
    
    @classmethod
    def create_user_with_api_key(cls, userId: str, role: str, zone: str) -> UserApiKey:
        """Create user with generated API key."""
        
        api_key = ApiKeyManager.generate_api_key()
        
        user = UserApiKey(
            userId=userId,
            apiKey=api_key,
            role=role,
            zone=zone,
            createdDate=datetime.utcnow()
        )
        
        cls._user_keys[userId] = user
        cls._api_key_to_user[api_key] = userId
        
        return user
    
    @classmethod
    def authenticate_with_api_key(cls, userId: str, apiKey: str) -> Optional[UserApiKey]:
        """Authenticate user with API key."""
        
        # Find user
        user = cls._user_keys.get(userId)
        if not user or not user.isActive:
            return None
            
        # Verify API key
        if user.apiKey != apiKey:
            return None
            
        return user
    
    @classmethod
    def authenticate_with_secret_hash(cls, request: HashedSecretLoginRequest, master_secret: str) -> Optional[UserApiKey]:
        """Authenticate using hashed secret (more secure)."""
        
        # Check timestamp (prevent replay attacks)
        current_time = int(datetime.utcnow().timestamp())
        if abs(current_time - request.timestamp) > 300:  # 5 minute window
            return None
            
        # Verify hash
        expected_hash = ApiKeyManager.hash_secret(master_secret, request.userId, request.timestamp)
        if request.secretHash != expected_hash:
            return None
            
        # Find user (or create if authorized)
        user = cls._user_keys.get(request.userId)
        if not user:
            # Auto-create user if hash is valid (for first-time auth)
            user = cls.create_user_with_api_key(request.userId, request.role, request.zone)
            
        return user


# 4. SECURE API ENDPOINTS
router = APIRouter(prefix="/auth", tags=["API Key Authentication"])

@router.post("/login-with-api-key")
async def login_with_api_key(request: ApiKeyLoginRequest):
    """Login using userId and API key."""
    
    user = ApiKeyAuthService.authenticate_with_api_key(request.userId, request.apiKey)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_API_KEY",
                "message": "Invalid userId or API key"
            }
        )
    
    # Create JWT token after successful authentication
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


@router.post("/login-with-secret")
async def login_with_secret_hash(request: HashedSecretLoginRequest):
    """Login using hashed secret (most secure)."""
    
    # This would come from environment variable
    MASTER_SECRET = "your-super-secret-key-from-env"
    
    user = ApiKeyAuthService.authenticate_with_secret_hash(request, MASTER_SECRET)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_SECRET_HASH",
                "message": "Invalid secret hash or expired timestamp"
            }
        )
    
    # Create JWT token
    return {
        "access_token": "jwt_token_here",
        "token_type": "bearer",
        "expires_in": 86400
    }


@router.post("/generate-api-key")
async def generate_user_api_key(userId: str, role: str, zone: str):
    """Generate API key for a user (admin only)."""
    
    user = ApiKeyAuthService.create_user_with_api_key(userId, role, zone)
    
    return {
        "userId": user.userId,
        "apiKey": user.apiKey,  # Return once, store securely!
        "role": user.role,
        "zone": user.zone,
        "message": "Store this API key securely. It won't be shown again."
    }


# 5. EXAMPLE USAGE
"""
Method 1: API Key Authentication
================================

1. Generate API key (admin action):
POST /auth/generate-api-key?userId=admin001&role=super_admin&zone=GSEZ

Response:
{
    "userId": "admin001",
    "apiKey": "xl7YzDVwF6QCz8N5hKpLxWd_8jF3nRoA9mB1eT2vU4s",
    "role": "super_admin",
    "zone": "GSEZ"
}

2. Login with API key:
POST /auth/login-with-api-key
{
    "userId": "admin001",
    "apiKey": "xl7YzDVwF6QCz8N5hKpLxWd_8jF3nRoA9mB1eT2vU4s"
}


Method 2: Hashed Secret Authentication (Most Secure)
===================================================

1. Client calculates hash:
secret = "master-secret-from-env"
userId = "admin001" 
timestamp = 1720972800
hash = sha256(secret + userId + timestamp)

2. Login with hash:
POST /auth/login-with-secret
{
    "userId": "admin001",
    "role": "super_admin", 
    "zone": "GSEZ",
    "secretHash": "a1b2c3d4e5f6...",
    "timestamp": 1720972800
}

Benefits:
- Secret never transmitted over network
- Timestamp prevents replay attacks
- Hash is unique per request
"""
