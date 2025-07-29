"""
User management API endpoints.
Requires super_admin role for all operations.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from app.schemas.auth import (
    CreateUserRequest, 
    UpdateUserRequest, 
    UserResponse, 
    AuthErrorResponse,
    JWTPayload
)
from app.services.auth import auth_service
from app.utils.auth import require_permissions

router = APIRouter(prefix="/user", tags=["User Management"])


@router.post(
    "/create_user",
    response_model=UserResponse,
    responses={
        400: {"model": AuthErrorResponse, "description": "Bad Request - User already exists or validation error"},
        401: {"model": AuthErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        403: {"model": AuthErrorResponse, "description": "Forbidden - Insufficient permissions"},
        500: {"model": AuthErrorResponse, "description": "Internal Server Error"}
    },
    summary="Create New User",
    description="Create a new user with specified email, role, and zone. Only accessible by super_admin."
)
async def create_user(
    request: CreateUserRequest,
    current_user: JWTPayload = Depends(require_permissions(["write"], ["users"]))
):
    """
    Create a new user (super_admin only).
    
    - **email**: Valid email address (will be used as identifier)
    - **role**: User role (super_admin, zone_admin, normal_user)
    - **zone**: Valid zone code (e.g., GSEZ, OSEZ, GABON, TEST)
    
    **Requirements:**
    - JWT token with super_admin role
    - Valid email format
    - Valid zone code
    - Email must not already exist
    """
    # Additional check: only super_admin can create users
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Only super_admin can create users",
                "details": {"required_role": "super_admin", "current_role": current_user.role}
            }
        )
    
    try:
        # Create the user
        user = auth_service.create_user(request)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "USER_ALREADY_EXISTS",
                    "message": f"User with email {request.email} already exists",
                    "details": {"email": request.email}
                }
            )
            
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_INPUT",
                "message": str(e),
                "details": {"field": "zone" if "zone" in str(e) else "unknown"}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to create user",
                "details": {"error": str(e)}
            }
        )


@router.put(
    "/update_user",
    response_model=UserResponse,
    responses={
        400: {"model": AuthErrorResponse, "description": "Bad Request - Validation error"},
        401: {"model": AuthErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        403: {"model": AuthErrorResponse, "description": "Forbidden - Insufficient permissions"},
        404: {"model": AuthErrorResponse, "description": "Not Found - User not found"},
        500: {"model": AuthErrorResponse, "description": "Internal Server Error"}
    },
    summary="Update User",
    description="Update user role and/or zone by email. Only accessible by super_admin."
)
async def update_user(
    request: UpdateUserRequest,
    current_user: JWTPayload = Depends(require_permissions(["write"], ["users"]))
):
    """
    Update an existing user (super_admin only).
    
    - **email**: Email address of user to update
    - **role**: New user role (optional)
    - **zone**: New zone code (optional)
    
    **Requirements:**
    - JWT token with super_admin role
    - Valid email format
    - Valid zone code (if provided)
    - User must exist
    - At least one field (role or zone) must be provided
    """
    # Additional check: only super_admin can update users
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Only super_admin can update users",
                "details": {"required_role": "super_admin", "current_role": current_user.role}
            }
        )
    
    # Validate that at least one field is provided for update
    if request.role is None and request.zone is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "NO_UPDATE_FIELDS",
                "message": "At least one field (role or zone) must be provided for update",
                "details": {"provided_fields": {"role": request.role, "zone": request.zone}}
            }
        )
    
    try:
        # Update the user
        user = auth_service.update_user(request)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": f"User with email {request.email} not found",
                    "details": {"email": request.email}
                }
            )
            
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_INPUT",
                "message": str(e),
                "details": {"field": "zone" if "zone" in str(e) else "unknown"}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to update user",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/list_user",
    response_model=List[UserResponse],
    responses={
        401: {"model": AuthErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        403: {"model": AuthErrorResponse, "description": "Forbidden - Insufficient permissions"},
        500: {"model": AuthErrorResponse, "description": "Internal Server Error"}
    },
    summary="List All Users",
    description="List all users in the system. Only accessible by super_admin."
)
async def list_user(
    current_user: JWTPayload = Depends(require_permissions(["read"], ["users"]))
):
    """
    List all users (super_admin only).
    
    **Requirements:**
    - JWT token with super_admin role
    
    **Returns:**
    - List of all users with their details
    """
    # Additional check: only super_admin can list users
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Only super_admin can list users",
                "details": {"required_role": "super_admin", "current_role": current_user.role}
            }
        )
    
    try:
        users = auth_service.list_users()
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list users",
                "details": {"error": str(e)}
            }
        )
