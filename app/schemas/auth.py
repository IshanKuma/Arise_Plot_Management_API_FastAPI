"""
Authentication-related Pydantic schemas for request/response validation.
"""
import re
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """Valid user roles as per API specification."""
    SUPER_ADMIN = "super_admin"
    ZONE_ADMIN = "zone_admin"
    NORMAL_USER = "normal_user"


class AuthTokenRequest(BaseModel):
    """
    Request schema for POST /auth/token endpoint.
    
    As per API specification:
    - userId: string, max 50 chars, mandatory
    - role: string, max 20 chars, mandatory (super_admin, zone_admin, normal_user)  
    - zone: string, max 10 chars, mandatory (valid zone code)
    
    Note: Authentication secret is passed via Authorization header: "Secret <secret-key>"
    """
    userId: str = Field(..., max_length=50, description="Valid user identifier")
    role: UserRole = Field(..., description="User role: super_admin, zone_admin, or normal_user")
    zone: str = Field(..., max_length=10, description="Valid zone code (e.g., GSEZ, OSEZ)")
    
    @validator('zone')
    def validate_zone_code(cls, v):
        """Validate zone code format: 4-6 uppercase letters."""
        if not v.isalpha() or not v.isupper() or not (4 <= len(v) <= 6):
            raise ValueError('Zone code must be 4-6 uppercase letters (e.g., GSEZ, OSEZ)')
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "userId": "user_001",
                "role": "zone_admin",
                "zone": "GSEZ"
            }
        }


class AuthTokenResponse(BaseModel):
    """
    Successful response schema for POST /auth/token endpoint.
    
    As per API specification:
    - access_token: string, max 500 chars, mandatory (JWT token)
    - token_type: string, max 10 chars, mandatory (always "bearer")
    - expires_in: integer, mandatory (86400 seconds for 24 hours)
    """
    access_token: str = Field(..., max_length=500, description="JWT token with 24-hour expiry")
    token_type: str = Field(default="bearer", max_length=10, description="Always 'bearer'")
    expires_in: int = Field(..., description="Token expiry time in seconds (86400)")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer", 
                "expires_in": 86400
            }
        }


class AuthErrorResponse(BaseModel):
    """
    Error response schema for authentication failures.
    
    As per API specification:
    - error_code: string, max 50 chars, mandatory
    - message: string, max 200 chars, mandatory  
    - details: object, optional
    """
    error_code: str = Field(..., max_length=50, description="Error code identifier")
    message: str = Field(..., max_length=200, description="Human-readable error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "error_code": "INVALID_ROLE",
                "message": "Invalid role provided. Must be one of: super_admin, zone_admin, normal_user",
                "details": {"provided_role": "invalid_role"}
            }
        }


class JWTPayload(BaseModel):
    """
    JWT token payload structure.
    
    Internal model for JWT token creation and validation.
    """
    userId: str
    role: UserRole
    zone: str
    permissions: Dict[str, List[str]]
    iat: int  # Issued at time
    exp: int  # Expiration time

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "userId": "user_001",
                "role": "zone_admin",
                "zone": "GSEZ",
                "permissions": {
                    "read": ["plots", "zones"],
                    "write": ["plots", "zones"]
                },
                "iat": 1672531200,
                "exp": 1672617600
            }
        }


class CreateUserRequest(BaseModel):
    """
    Request schema for POST /create_user endpoint (super_admin only).
    
    As per API specification:
    - email: string, valid email format, mandatory
    - role: string, max 20 chars, mandatory (super_admin, zone_admin, normal_user)  
    - zone: string, max 10 chars, mandatory (valid zone code)
    """
    email: str = Field(..., max_length=100, description="Valid email address")
    role: UserRole = Field(..., description="User role: super_admin, zone_admin, or normal_user")
    zone: str = Field(..., max_length=10, description="Valid zone code (e.g., GSEZ, OSEZ)")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('zone')
    def validate_zone_code(cls, v):
        """Validate zone code format: 4-6 uppercase letters."""
        if not v.isalpha() or not v.isupper() or not (4 <= len(v) <= 6):
            raise ValueError('Zone code must be 4-6 uppercase letters (e.g., GSEZ, OSEZ)')
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "zone_admin",
                "zone": "GSEZ"
            }
        }


class UpdateUserRequest(BaseModel):
    """
    Request schema for PUT /update_user endpoint (super_admin only).
    
    As per API specification:
    - email: string, valid email format, mandatory (identifier)
    - role: string, max 20 chars, optional (super_admin, zone_admin, normal_user)  
    - zone: string, max 50 chars, optional (country name or zone identifier)
    """
    email: str = Field(..., max_length=100, description="Valid email address of user to update")
    role: Optional[UserRole] = Field(None, description="New user role: super_admin, zone_admin, or normal_user")
    zone: Optional[str] = Field(None, max_length=50, description="Zone or country name (e.g., 'Nigeria', 'Ghana')")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('zone')
    def validate_zone(cls, v):
        """Validate zone - accept country names or zone codes."""
        if v and len(v.strip()) == 0:
            raise ValueError('Zone cannot be empty')
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "normal_user",
                "zone": "Nigeria"
            }
        }


class UserResponse(BaseModel):
    """
    Response schema for user operations.
    
    Returns user information after create/update operations.
    """
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    zone: str = Field(..., description="User zone")
    createdDate: datetime = Field(..., description="User creation timestamp")
    lastModified: datetime = Field(..., description="Last modification timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "zone_admin",
                "zone": "GSEZ",
                "createdDate": "2024-01-01T10:00:00Z",
                "lastModified": "2024-01-01T10:00:00Z"
            }
        }


class UserModel(BaseModel):
    """
    Internal user model for storage.
    """
    email: str
    role: UserRole
    zone: str
    createdDate: datetime
    lastModified: datetime
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
