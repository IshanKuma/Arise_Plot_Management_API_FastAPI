"""
Authentication dependencies for protected endpoints.
Handles JWT token verification and user permission checking.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth import AuthService
from app.schemas.auth import JWTPayload

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JWTPayload:
    """
    Dependency to verify JWT token and extract user payload.
    
    Used by protected endpoints to:
    1. Verify JWT token validity
    2. Extract user information (userId, role, zone, permissions)
    3. Return structured user payload
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        JWTPayload: Decoded user information and permissions
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid/expired
    """
    
    # Extract token from Authorization header
    token = credentials.credentials
    
    # Verify and decode JWT token
    payload = AuthService.verify_jwt_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Invalid or expired JWT token"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_permission(resource: str, action: str):
    """
    Dependency factory to check user permissions for specific resources.
    
    Args:
        resource: Resource type (e.g., "plots", "zones")
        action: Action type (e.g., "read", "write")
        
    Returns:
        Dependency function that checks permissions
    """
    
    def check_permission(user: JWTPayload = Depends(get_current_user)) -> JWTPayload:
        """
        Check if user has required permission for resource and action.
        
        Args:
            user: Current authenticated user
            
        Returns:
            JWTPayload: User payload if permission granted
            
        Raises:
            HTTPException: 403 Forbidden if insufficient permissions
        """
        
        # Check if user has required permission
        user_permissions = user.permissions.get(action, [])
        
        if resource not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "FORBIDDEN",
                    "message": f"Insufficient permissions for {action} access to {resource}"
                }
            )
        
        return user
    
    return check_permission


# Pre-configured permission dependencies for common use cases
require_plots_read = require_permission("plots", "read")
require_plots_write = require_permission("plots", "write") 
require_zones_read = require_permission("zones", "read")
require_zones_write = require_permission("zones", "write")
