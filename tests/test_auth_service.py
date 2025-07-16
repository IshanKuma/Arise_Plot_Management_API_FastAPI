"""
Unit tests for authentication service.
Tests JWT token creation, validation, and user management functions.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import jwt

from app.services.auth import AuthService
from app.schemas.auth import AuthTokenRequest, UserRole, CreateUserRequest, UpdateUserRequest
from app.core.config import settings


class TestAuthService:
    """Test AuthService class methods."""
    
    def setup_method(self):
        """Reset user storage before each test."""
        AuthService._users.clear()
    
    def test_validate_request_success(self):
        """Test successful request validation."""
        request = AuthTokenRequest(
            userId="test001",
            role=UserRole.SUPER_ADMIN,
            zone="GSEZ"
        )
        
        result = AuthService.validate_request(request)
        assert result is None  # No error
    
    def test_validate_request_invalid_zone(self):
        """Test request validation with invalid zone."""
        request = AuthTokenRequest(
            userId="test001",
            role=UserRole.SUPER_ADMIN,
            zone="INVALID"
        )
        
        result = AuthService.validate_request(request)
        assert result == "INVALID_ZONE"
    
    def test_get_permissions_for_role_super_admin(self):
        """Test permissions for super_admin role."""
        permissions = AuthService.get_permissions_for_role("super_admin")
        
        expected = {
            "read": ["plots", "zones", "users"],
            "write": ["plots", "zones", "users"]
        }
        assert permissions == expected
    
    def test_get_permissions_for_role_zone_admin(self):
        """Test permissions for zone_admin role."""
        permissions = AuthService.get_permissions_for_role("zone_admin")
        
        expected = {
            "read": ["plots", "zones"],
            "write": ["plots", "zones"]
        }
        assert permissions == expected
    
    def test_get_permissions_for_role_normal_user(self):
        """Test permissions for normal_user role."""
        permissions = AuthService.get_permissions_for_role("normal_user")
        
        expected = {
            "read": ["plots", "zones"],
            "write": []
        }
        assert permissions == expected
    
    def test_get_permissions_for_role_invalid(self):
        """Test permissions for invalid role."""
        permissions = AuthService.get_permissions_for_role("invalid_role")
        
        expected = {"read": [], "write": []}
        assert permissions == expected
    
    @patch('app.services.auth.datetime')
    def test_create_jwt_token(self, mock_datetime):
        """Test JWT token creation."""
        # Mock datetime for consistent testing
        mock_now = datetime(2025, 7, 14, 10, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        request = AuthTokenRequest(
            userId="test001",
            role=UserRole.SUPER_ADMIN,
            zone="GSEZ"
        )
        
        token = AuthService.create_jwt_token(request)
        
        # Verify token is a string and has JWT format
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # header.payload.signature
        
        # Decode and verify payload
        payload = jwt.decode(
            token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["userId"] == "test001"
        assert payload["role"] == "super_admin"
        assert payload["zone"] == "GSEZ"
        assert "permissions" in payload
        assert payload["iat"] == int(mock_now.timestamp())
        assert payload["exp"] == int((mock_now + timedelta(hours=24)).timestamp())
    
    def test_verify_jwt_token_valid(self):
        """Test JWT token verification with valid token."""
        request = AuthTokenRequest(
            userId="test001",
            role=UserRole.ZONE_ADMIN,
            zone="OSEZ"
        )
        
        token = AuthService.create_jwt_token(request)
        payload = AuthService.verify_jwt_token(token)
        
        assert payload is not None
        assert payload.userId == "test001"
        assert payload.role == UserRole.ZONE_ADMIN
        assert payload.zone == "OSEZ"
    
    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.jwt.token"
        
        payload = AuthService.verify_jwt_token(invalid_token)
        assert payload is None
    
    def test_verify_jwt_token_malformed(self):
        """Test JWT token verification with malformed token."""
        malformed_token = "not.a.valid.jwt.token.structure"
        
        payload = AuthService.verify_jwt_token(malformed_token)
        assert payload is None
    
    def test_get_token_expiry_seconds(self):
        """Test token expiry calculation."""
        expiry = AuthService.get_token_expiry_seconds()
        expected = 24 * 3600  # 24 hours in seconds
        assert expiry == expected
    
    def test_create_user_success(self):
        """Test successful user creation."""
        request = CreateUserRequest(
            email="test@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="GSEZ"
        )
        
        user = AuthService.create_user(request)
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.ZONE_ADMIN
        assert user.zone == "GSEZ"
        assert isinstance(user.createdDate, datetime)
        assert isinstance(user.lastModified, datetime)
        
        # Verify user is stored
        assert "test@example.com" in AuthService._users
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email."""
        request = CreateUserRequest(
            email="duplicate@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="GSEZ"
        )
        
        # Create first user
        user1 = AuthService.create_user(request)
        assert user1 is not None
        
        # Try to create duplicate
        user2 = AuthService.create_user(request)
        assert user2 is None
    
    def test_create_user_invalid_zone(self):
        """Test user creation with invalid zone."""
        request = CreateUserRequest(
            email="test@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="INVALID"
        )
        
        with pytest.raises(ValueError, match="Invalid zone"):
            AuthService.create_user(request)
    
    def test_update_user_success(self):
        """Test successful user update."""
        # Create user first
        create_request = CreateUserRequest(
            email="update@example.com",
            role=UserRole.NORMAL_USER,
            zone="GSEZ"
        )
        AuthService.create_user(create_request)
        
        # Update user
        update_request = UpdateUserRequest(
            email="update@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="OSEZ"
        )
        
        updated_user = AuthService.update_user(update_request)
        
        assert updated_user is not None
        assert updated_user.email == "update@example.com"
        assert updated_user.role == UserRole.ZONE_ADMIN
        assert updated_user.zone == "OSEZ"
    
    def test_update_user_not_found(self):
        """Test updating non-existent user."""
        update_request = UpdateUserRequest(
            email="nonexistent@example.com",
            role=UserRole.ZONE_ADMIN
        )
        
        result = AuthService.update_user(update_request)
        assert result is None
    
    def test_update_user_invalid_zone(self):
        """Test user update with invalid zone."""
        # Create user first
        create_request = CreateUserRequest(
            email="update@example.com",
            role=UserRole.NORMAL_USER,
            zone="GSEZ"
        )
        AuthService.create_user(create_request)
        
        # Try to update with invalid zone
        update_request = UpdateUserRequest(
            email="update@example.com",
            zone="INVALID"
        )
        
        with pytest.raises(ValueError, match="Invalid zone"):
            AuthService.update_user(update_request)
    
    def test_update_user_partial_update(self):
        """Test partial user update (only role or only zone)."""
        # Create user first
        create_request = CreateUserRequest(
            email="partial@example.com",
            role=UserRole.NORMAL_USER,
            zone="GSEZ"
        )
        original_user = AuthService.create_user(create_request)
        
        # Update only role
        update_request = UpdateUserRequest(
            email="partial@example.com",
            role=UserRole.ZONE_ADMIN
        )
        
        updated_user = AuthService.update_user(update_request)
        
        assert updated_user.role == UserRole.ZONE_ADMIN
        assert updated_user.zone == "GSEZ"  # Should remain unchanged
        assert updated_user.lastModified > original_user.lastModified
    
    def test_get_user_by_email_success(self):
        """Test getting user by email."""
        # Create user first
        create_request = CreateUserRequest(
            email="find@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="GSEZ"
        )
        AuthService.create_user(create_request)
        
        # Get user
        user = AuthService.get_user_by_email("find@example.com")
        
        assert user is not None
        assert user.email == "find@example.com"
        assert user.role == UserRole.ZONE_ADMIN
    
    def test_get_user_by_email_not_found(self):
        """Test getting non-existent user by email."""
        user = AuthService.get_user_by_email("nonexistent@example.com")
        assert user is None
    
    def test_get_user_by_email_case_insensitive(self):
        """Test getting user by email is case insensitive."""
        # Create user with lowercase email
        create_request = CreateUserRequest(
            email="case@example.com",
            role=UserRole.ZONE_ADMIN,
            zone="GSEZ"
        )
        AuthService.create_user(create_request)
        
        # Try to find with different case
        user = AuthService.get_user_by_email("CASE@EXAMPLE.COM")
        assert user is not None
        assert user.email == "case@example.com"
    
    def test_list_users_empty(self):
        """Test listing users when none exist."""
        users = AuthService.list_users()
        assert users == []
    
    def test_list_users_multiple(self):
        """Test listing multiple users."""
        # Create multiple users
        users_data = [
            ("user1@example.com", UserRole.SUPER_ADMIN, "GSEZ"),
            ("user2@example.com", UserRole.ZONE_ADMIN, "OSEZ"),
            ("user3@example.com", UserRole.NORMAL_USER, "GABON")
        ]
        
        for email, role, zone in users_data:
            request = CreateUserRequest(email=email, role=role, zone=zone)
            AuthService.create_user(request)
        
        # List users
        users = AuthService.list_users()
        
        assert len(users) == 3
        emails = [user.email for user in users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails


class TestAuthServiceValidation:
    """Test AuthService validation methods."""
    
    def test_valid_zones_constant(self):
        """Test VALID_ZONES constant contains expected zones."""
        expected_zones = ["GSEZ", "OSEZ", "GABON", "TEST"]
        assert AuthService.VALID_ZONES == expected_zones
    
    def test_permissions_map_structure(self):
        """Test PERMISSIONS_MAP has correct structure."""
        permissions_map = AuthService.PERMISSIONS_MAP
        
        # Check all roles exist
        assert "super_admin" in permissions_map
        assert "zone_admin" in permissions_map
        assert "normal_user" in permissions_map
        
        # Check each role has read and write permissions
        for role, perms in permissions_map.items():
            assert "read" in perms
            assert "write" in perms
            assert isinstance(perms["read"], list)
            assert isinstance(perms["write"], list)
        
        # Check super_admin has all permissions
        super_admin_perms = permissions_map["super_admin"]
        assert "users" in super_admin_perms["read"]
        assert "users" in super_admin_perms["write"]
        
        # Check normal_user has no write permissions
        normal_user_perms = permissions_map["normal_user"]
        assert len(normal_user_perms["write"]) == 0
