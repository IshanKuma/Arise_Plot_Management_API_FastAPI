"""
Password-Based Authentication Example
====================================

This shows how to add secure password authentication to your JWT system.
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field


# 1. NEW SCHEMAS FOR PASSWORD AUTH
class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: str = Field(..., max_length=100, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")


class RegisterRequest(BaseModel):
    """User registration with email, password, role, zone."""
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., description="User role")
    zone: str = Field(..., max_length=10)


class UserModel(BaseModel):
    """User model with hashed password."""
    email: str
    password_hash: str  # Store hashed password, never plain text
    role: str
    zone: str
    created_date: datetime
    is_active: bool = True


# 2. PASSWORD HASHING UTILITIES
class PasswordManager:
    """Secure password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


# 3. SECURE AUTHENTICATION SERVICE
class SecureAuthService:
    """Secure authentication with password verification."""
    
    # In production: replace with database
    _users = {}  # email -> UserModel
    
    @classmethod
    def register_user(cls, request: RegisterRequest) -> Optional[UserModel]:
        """Register a new user with hashed password."""
        
        # Check if user already exists
        if request.email.lower() in cls._users:
            return None
            
        # Hash the password
        password_hash = PasswordManager.hash_password(request.password)
        
        # Create user
        user = UserModel(
            email=request.email.lower(),
            password_hash=password_hash,
            role=request.role,
            zone=request.zone,
            created_date=datetime.utcnow()
        )
        
        cls._users[user.email] = user
        return user
    
    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Optional[UserModel]:
        """Authenticate user with email and password."""
        
        # Find user
        user = cls._users.get(email.lower())
        if not user:
            return None
            
        # Check if account is active
        if not user.is_active:
            return None
            
        # Verify password
        if not PasswordManager.verify_password(password, user.password_hash):
            return None
            
        return user
    
    @classmethod
    def create_jwt_token(cls, user: UserModel) -> str:
        """Create JWT token for authenticated user."""
        # Your existing JWT creation logic here
        # But now it's called AFTER password verification
        pass


# 4. SECURE API ENDPOINTS
router = APIRouter(prefix="/auth", tags=["Secure Authentication"])

@router.post("/register")
async def register_user(request: RegisterRequest):
    """Register a new user with password."""
    
    user = SecureAuthService.register_user(request)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "USER_EXISTS",
                "message": "User with this email already exists"
            }
        )
    
    return {
        "message": "User registered successfully",
        "email": user.email,
        "role": user.role
    }


@router.post("/login")
async def login_user(request: LoginRequest):
    """Login with email and password to get JWT token."""
    
    # STEP 1: Verify credentials (this is what was missing!)
    user = SecureAuthService.authenticate_user(request.email, request.password)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS", 
                "message": "Invalid email or password"
            }
        )
    
    # STEP 2: Create JWT token (only after successful authentication)
    token = SecureAuthService.create_jwt_token(user)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user_info": {
            "email": user.email,
            "role": user.role,
            "zone": user.zone
        }
    }


# 5. EXAMPLE USAGE
"""
Register a user:
POST /auth/register
{
    "email": "admin@arise.com",
    "password": "SecurePassword123!",
    "role": "super_admin", 
    "zone": "GSEZ"
}

Login to get JWT:
POST /auth/login  
{
    "email": "admin@arise.com",
    "password": "SecurePassword123!"
}

Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
}
"""
