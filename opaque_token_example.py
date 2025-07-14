"""
Opaque Token Implementation Example for Arise API
================================================

This shows how to implement opaque tokens as a secure alternative to JWT payload exposure.
"""
import uuid
import json
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SessionData:
    """User session data structure."""
    user_id: str
    email: str
    role: str
    zone: str
    permissions: Dict[str, list]
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class OpaqueTokenService:
    """
    Service for managing opaque tokens with Redis backend.
    
    Benefits:
    - Payload completely hidden from clients
    - Instant token revocation
    - Session management capabilities
    - Better security than JWT payload exposure
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=0,
            decode_responses=True
        )
        self.token_prefix = "arise_session:"
        self.user_sessions_prefix = "user_sessions:"
    
    def create_session(
        self, 
        user_id: str, 
        email: str, 
        role: str, 
        zone: str,
        permissions: Dict[str, list],
        expires_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create a new opaque token session.
        
        Args:
            user_id: User identifier
            email: User email
            role: User role (super_admin, zone_admin, normal_user)
            zone: User zone
            permissions: User permissions dict
            expires_hours: Session expiry in hours
            ip_address: Client IP (for security tracking)
            user_agent: Client user agent
            
        Returns:
            str: Opaque token (UUID)
        """
        # Generate random opaque token
        token = str(uuid.uuid4())
        
        # Create session data
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expires_hours)
        
        session_data = SessionData(
            user_id=user_id,
            email=email,
            role=role,
            zone=zone,
            permissions=permissions,
            created_at=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store in Redis with expiration
        session_key = f"{self.token_prefix}{token}"
        session_json = json.dumps({
            "user_id": session_data.user_id,
            "email": session_data.email,
            "role": session_data.role,
            "zone": session_data.zone,
            "permissions": session_data.permissions,
            "created_at": session_data.created_at.isoformat(),
            "expires_at": session_data.expires_at.isoformat(),
            "ip_address": session_data.ip_address,
            "user_agent": session_data.user_agent
        })
        
        # Set with expiration
        self.redis_client.setex(
            session_key,
            int(timedelta(hours=expires_hours).total_seconds()),
            session_json
        )
        
        # Track user sessions (for logout all devices)
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        self.redis_client.sadd(user_sessions_key, token)
        self.redis_client.expire(user_sessions_key, int(timedelta(hours=expires_hours).total_seconds()))
        
        return token
    
    def get_session(self, token: str) -> Optional[SessionData]:
        """
        Retrieve session data by opaque token.
        
        Args:
            token: Opaque token string
            
        Returns:
            Optional[SessionData]: Session data if valid, None if expired/invalid
        """
        session_key = f"{self.token_prefix}{token}"
        session_json = self.redis_client.get(session_key)
        
        if not session_json:
            return None
        
        try:
            data = json.loads(session_json)
            return SessionData(
                user_id=data["user_id"],
                email=data["email"], 
                role=data["role"],
                zone=data["zone"],
                permissions=data["permissions"],
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"]),
                ip_address=data.get("ip_address"),
                user_agent=data.get("user_agent")
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def revoke_session(self, token: str) -> bool:
        """
        Revoke a specific session token.
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: True if token was revoked, False if not found
        """
        session_key = f"{self.token_prefix}{token}"
        
        # Get session data first to update user sessions
        session_data = self.get_session(token)
        if session_data:
            user_sessions_key = f"{self.user_sessions_prefix}{session_data.user_id}"
            self.redis_client.srem(user_sessions_key, token)
        
        # Delete the session
        return bool(self.redis_client.delete(session_key))
    
    def revoke_all_user_sessions(self, user_id: str) -> int:
        """
        Revoke all sessions for a specific user.
        
        Args:
            user_id: User to logout from all devices
            
        Returns:
            int: Number of sessions revoked
        """
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        tokens = self.redis_client.smembers(user_sessions_key)
        
        revoked_count = 0
        for token in tokens:
            if self.revoke_session(token):
                revoked_count += 1
        
        # Clean up user sessions set
        self.redis_client.delete(user_sessions_key)
        
        return revoked_count
    
    def refresh_session(self, token: str, expires_hours: int = 24) -> bool:
        """
        Extend session expiration time.
        
        Args:
            token: Token to refresh
            expires_hours: New expiry time in hours
            
        Returns:
            bool: True if refreshed, False if not found
        """
        session_data = self.get_session(token)
        if not session_data:
            return False
        
        # Update expiry time
        session_data.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Re-store with new expiration
        session_key = f"{self.token_prefix}{token}"
        session_json = json.dumps({
            "user_id": session_data.user_id,
            "email": session_data.email,
            "role": session_data.role,
            "zone": session_data.zone,
            "permissions": session_data.permissions,
            "created_at": session_data.created_at.isoformat(),
            "expires_at": session_data.expires_at.isoformat(),
            "ip_address": session_data.ip_address,
            "user_agent": session_data.user_agent
        })
        
        self.redis_client.setex(
            session_key,
            int(timedelta(hours=expires_hours).total_seconds()),
            session_json
        )
        
        return True
    
    def get_active_sessions_count(self, user_id: str) -> int:
        """
        Get number of active sessions for a user.
        
        Args:
            user_id: User to check
            
        Returns:
            int: Number of active sessions
        """
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        return self.redis_client.scard(user_sessions_key)
    
    def is_session_valid(self, token: str, ip_address: Optional[str] = None) -> bool:
        """
        Check if session is valid with optional IP verification.
        
        Args:
            token: Token to check
            ip_address: IP to verify against session IP
            
        Returns:
            bool: True if valid session
        """
        session_data = self.get_session(token)
        if not session_data:
            return False
        
        # Check expiry
        if datetime.utcnow() > session_data.expires_at:
            self.revoke_session(token)
            return False
        
        # Optional IP verification (for additional security)
        if ip_address and session_data.ip_address:
            if ip_address != session_data.ip_address:
                return False
        
        return True


# Example usage in your existing AuthService
class SecureAuthService(AuthService):
    """Enhanced AuthService with opaque tokens."""
    
    def __init__(self):
        self.token_service = OpaqueTokenService()
    
    @classmethod
    def create_secure_token(
        cls, 
        request: AuthTokenRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create opaque token instead of JWT.
        
        Args:
            request: Authentication request
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            str: Opaque token
        """
        # Get permissions
        permissions = cls.get_permissions_for_role(request.role.value)
        
        # Create opaque token session
        token_service = OpaqueTokenService()
        token = token_service.create_session(
            user_id=request.userId,
            email=f"{request.userId}@arise.com",  # Or lookup real email
            role=request.role.value,
            zone=request.zone,
            permissions=permissions,
            expires_hours=24,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return token
    
    @classmethod
    def verify_secure_token(cls, token: str, ip_address: Optional[str] = None) -> Optional[SessionData]:
        """
        Verify opaque token and return session data.
        
        Args:
            token: Opaque token
            ip_address: Client IP for verification
            
        Returns:
            Optional[SessionData]: Session data if valid
        """
        token_service = OpaqueTokenService()
        
        if not token_service.is_session_valid(token, ip_address):
            return None
        
        return token_service.get_session(token)


# FastAPI endpoint example
"""
# In your API endpoints, replace JWT verification with opaque token verification:

from fastapi import Request

async def get_current_user_secure(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> SessionData:
    # Extract token
    token = credentials.credentials
    
    # Get client IP
    ip_address = request.client.host
    
    # Verify opaque token
    session_data = SecureAuthService.verify_secure_token(token, ip_address)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_SESSION",
                "message": "Invalid or expired session token"
            }
        )
    
    return session_data

# Usage in protected endpoints:
@router.get("/plots/available")
async def get_plots(
    session: SessionData = Depends(get_current_user_secure)
):
    # Use session.role, session.permissions, etc.
    if "plots" not in session.permissions.get("read", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Your existing logic here...
"""


if __name__ == "__main__":
    # Example usage
    token_service = OpaqueTokenService()
    
    # Create session
    token = token_service.create_session(
        user_id="admin001",
        email="admin@arise.com",
        role="super_admin",
        zone="GSEZ",
        permissions={"read": ["plots", "zones", "users"], "write": ["plots", "zones", "users"]},
        ip_address="192.168.1.100"
    )
    
    print(f"Opaque Token: {token}")
    print(f"Token Length: {len(token)} characters")
    print("Token contains no readable information!")
    
    # Retrieve session
    session = token_service.get_session(token)
    if session:
        print(f"User: {session.email}")
        print(f"Role: {session.role}")
        print(f"Permissions: {session.permissions}")
    
    # Revoke token
    revoked = token_service.revoke_session(token)
    print(f"Token revoked: {revoked}")
