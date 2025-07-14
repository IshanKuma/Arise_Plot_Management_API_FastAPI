"""
Authentication service for JWT token creation and validation.
Implements the exact logic as specified in Flow 1 requirements.
Enhanced with user management capabilities.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import jwt
from app.core.config import settings
from app.schemas.auth import UserRole, JWTPayload, AuthTokenRequest, CreateUserRequest, UpdateUserRequest, UserModel, UserResponse


class AuthService:
    """Authentication service for handling JWT operations and user management."""
    
    # In-memory user storage (replace with Firestore in production)
    _users: Dict[str, UserModel] = {}
    
    # Role-based permissions mapping as specified in the requirements
    PERMISSIONS_MAP = {
        "super_admin": {"read": ["plots", "zones", "users"], "write": ["plots", "zones", "users"]},
        "zone_admin": {"read": ["plots", "zones"], "write": ["plots", "zones"]}, 
        "normal_user": {"read": ["plots", "zones"], "write": []}
    }
    
    # Valid zone codes (can be extended based on requirements)
    VALID_ZONES = ["GSEZ", "OSEZ", "GABON", "TEST"]
    
    @classmethod
    def validate_request(cls, request: AuthTokenRequest) -> Optional[str]:
        """
        Validate authentication request parameters.
        
        Returns:
            Optional[str]: Error code if validation fails, None if valid
        """
        # Check if role is valid (already validated by Pydantic enum)
        if request.role not in [role.value for role in UserRole]:
            return "INVALID_ROLE"
            
        # Check if zone is valid
        if request.zone not in cls.VALID_ZONES:
            return "INVALID_ZONE"
            
        return None
    
    @classmethod
    def get_permissions_for_role(cls, role: str) -> Dict[str, List[str]]:
        """
        Get permissions based on user role.
        
        Args:
            role: User role (super_admin, zone_admin, normal_user)
            
        Returns:
            Dict[str, List[str]]: Permissions dictionary
        """
        return cls.PERMISSIONS_MAP.get(role, {"read": [], "write": []})
    
    @classmethod
    def create_jwt_token(cls, request: AuthTokenRequest) -> str:
        """
        Create JWT token with user information and permissions.
        
        Args:
            request: Validated authentication request
            
        Returns:
            str: Signed JWT token
        """
        # Current time and expiration
        now = datetime.utcnow()
        expiration = now + timedelta(hours=settings.JWT_EXPIRE_HOURS)
        
        # Get permissions for the role
        permissions = cls.get_permissions_for_role(request.role.value)
        
        # Create JWT payload
        payload = {
            "userId": request.userId,
            "role": request.role.value,
            "zone": request.zone,
            "permissions": permissions,
            "iat": int(now.timestamp()),
            "exp": int(expiration.timestamp())
        }
        
        # Sign the token using HS256 with secret key
        token = jwt.encode(
            payload=payload,
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return token
    
    @classmethod
    def verify_jwt_token(cls, token: str) -> Optional[JWTPayload]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[JWTPayload]: Decoded payload if valid, None if invalid
        """
        try:
            # For HS256, we use the same secret key for both signing and verification
            payload = jwt.decode(
                jwt=token,
                key=settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return JWTPayload(**payload)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @classmethod
    def get_token_expiry_seconds(cls) -> int:
        """
        Get token expiry time in seconds.
        
        Returns:
            int: Expiry time in seconds (24 hours = 86400 seconds)
        """
        return settings.JWT_EXPIRE_HOURS * 3600

    # User Management Methods
    
    @classmethod
    def create_user(cls, request: CreateUserRequest) -> Optional[UserResponse]:
        """
        Create a new user.
        
        Args:
            request: User creation request
            
        Returns:
            Optional[UserResponse]: Created user data or None if user exists
        """
        # Check if user already exists
        if request.email in cls._users:
            return None
            
        # Validate zone
        if request.zone not in cls.VALID_ZONES:
            raise ValueError(f"Invalid zone: {request.zone}")
            
        # Create user
        now = datetime.utcnow()
        user = UserModel(
            email=request.email,
            role=request.role,
            zone=request.zone,
            createdDate=now,
            lastModified=now
        )
        
        cls._users[request.email] = user
        
        return UserResponse(
            email=user.email,
            role=user.role,
            zone=user.zone,
            createdDate=user.createdDate,
            lastModified=user.lastModified
        )
    
    @classmethod
    def update_user(cls, request: UpdateUserRequest) -> Optional[UserResponse]:
        """
        Update an existing user.
        
        Args:
            request: User update request
            
        Returns:
            Optional[UserResponse]: Updated user data or None if user not found
        """
        # Check if user exists
        if request.email not in cls._users:
            return None
            
        user = cls._users[request.email]
        updated = False
        
        # Update role if provided
        if request.role is not None:
            user.role = request.role
            updated = True
            
        # Update zone if provided
        if request.zone is not None:
            if request.zone not in cls.VALID_ZONES:
                raise ValueError(f"Invalid zone: {request.zone}")
            user.zone = request.zone
            updated = True
            
        # Update lastModified if any changes were made
        if updated:
            user.lastModified = datetime.utcnow()
            
        return UserResponse(
            email=user.email,
            role=user.role,
            zone=user.zone,
            createdDate=user.createdDate,
            lastModified=user.lastModified
        )
    
    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[UserModel]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            Optional[UserModel]: User data or None if not found
        """
        return cls._users.get(email.lower())
    
    @classmethod
    def list_users(cls) -> List[UserResponse]:
        """
        List all users.
        
        Returns:
            List[UserResponse]: List of all users
        """
        return [
            UserResponse(
                email=user.email,
                role=user.role,
                zone=user.zone,
                createdDate=user.createdDate,
                lastModified=user.lastModified
            )
            for user in cls._users.values()
        ]
