"""
Authentication service for JWT token creation and validation.
Implements the exact logic as specified in Flow 1 requirements.
Enhanced with user management capabilities using Firestore.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import jwt
from google.cloud import firestore
from app.core.config import settings
from app.core.firebase import get_firestore_db
from app.schemas.auth import UserRole, JWTPayload, AuthTokenRequest, CreateUserRequest, UpdateUserRequest, UserModel, UserResponse


class AuthService:
    """Authentication service for handling JWT operations and user management with Firestore."""
    
    def __init__(self):
        """Initialize Firestore client for user management."""
        self.db = get_firestore_db()
        self.users_collection = self.db.collection(settings.FIRESTORE_COLLECTION_USERS)
    
    # Role-based permissions mapping as specified in the requirements
    PERMISSIONS_MAP = {
        "super_admin": {"read": ["plots", "zones", "users"], "write": ["plots", "zones", "users"]},
        "zone_admin": {"read": ["plots", "zones"], "write": ["plots", "zones"]}, 
        "normal_user": {"read": ["plots", "zones"], "write": []}
    }
    
    @classmethod
    def validate_request(cls, request: AuthTokenRequest, secret_key: str) -> Optional[str]:
        """
        Validate authentication request parameters including secret key.
        
        Args:
            request: Authentication request data
            secret_key: Secret key from Authorization header
            
        Returns:
            Optional[str]: Error code if validation fails, None if valid
        """
        # Check if secret key is valid
        if secret_key != settings.AUTH_SECRET_KEY:
            return "INVALID_SECRET_KEY"
            
        # Check if role is valid (already validated by Pydantic enum)
        if request.role not in [role.value for role in UserRole]:
            return "INVALID_ROLE"
            
        # No zone validation - users have freedom to specify any zone
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
    
    def create_user(self, request: CreateUserRequest) -> Optional[UserResponse]:
        """
        Create a new user in Firestore.
        
        Args:
            request: User creation request
            
        Returns:
            Optional[UserResponse]: Created user data or None if user exists
        """
        # Check if user already exists
        existing_query = self.users_collection.where("email", "==", request.email).limit(1)
        existing_docs = list(existing_query.stream())
        
        if existing_docs:
            return None
            
        # Create user document (no zone validation - users have freedom)
        now = datetime.utcnow()
        user_data = {
            "email": request.email,
            "role": request.role.value,
            "zone": request.zone,
            "createdDate": now,
            "lastModified": now,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add user to Firestore
        self.users_collection.add(user_data)
        
        return UserResponse(
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            zone=user_data["zone"],
            createdDate=user_data["createdDate"],
            lastModified=user_data["lastModified"]
        )
    
    def update_user(self, request: UpdateUserRequest) -> Optional[UserResponse]:
        """
        Update an existing user in Firestore.
        
        Args:
            request: User update request
            
        Returns:
            Optional[UserResponse]: Updated user data or None if user not found
        """
        # Find user document
        user_query = self.users_collection.where("email", "==", request.email).limit(1)
        docs = list(user_query.stream())
        
        if not docs:
            return None
            
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        
        # Prepare update data
        update_data = {}
        updated = False
        
        # Update role if provided
        if request.role is not None:
            update_data["role"] = request.role.value
            user_data["role"] = request.role.value
            updated = True
            
        # Update zone if provided (no validation - users have freedom)
        if request.zone is not None:
            update_data["zone"] = request.zone
            user_data["zone"] = request.zone
            updated = True
            
        # Update lastModified if any changes were made
        if updated:
            now = datetime.utcnow()
            update_data["lastModified"] = now
            update_data["updatedAt"] = firestore.SERVER_TIMESTAMP
            user_data["lastModified"] = now
            
            # Update the document
            user_doc.reference.update(update_data)
            
        return UserResponse(
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            zone=user_data["zone"],
            createdDate=user_data["createdDate"],
            lastModified=user_data["lastModified"]
        )
    
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by email from Firestore.
        
        Args:
            email: User email
            
        Returns:
            Optional[UserModel]: User data or None if not found
        """
        user_query = self.users_collection.where("email", "==", email.lower()).limit(1)
        docs = list(user_query.stream())
        
        if not docs:
            return None
            
        user_data = docs[0].to_dict()
        
        return UserModel(
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            zone=user_data["zone"],
            createdDate=user_data["createdDate"],
            lastModified=user_data["lastModified"]
        )
    
    def list_users(self) -> List[UserResponse]:
        """
        List all users from Firestore.
        
        Returns:
            List[UserResponse]: List of all users
        """
        docs = self.users_collection.stream()
        users = []
        
        for doc in docs:
            user_data = doc.to_dict()
            users.append(UserResponse(
                email=user_data["email"],
                role=UserRole(user_data["role"]),
                zone=user_data["zone"],
                createdDate=user_data["createdDate"],
                lastModified=user_data["lastModified"]
            ))
        
        return users


# Create a single instance to be used across the application
auth_service = AuthService()
