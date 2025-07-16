"""
JWT Security Implementation Best Practices
==========================================

Current Implementation Status: DEVELOPMENT READY
Production Readiness: NEEDS SECURITY HARDENING

IMPLEMENTED ✅:
- JWT signing with secret key
- Token expiration (24 hours)
- Role-based access control
- Permission validation
- Comprehensive error handling

MISSING - CRITICAL 🚨:
1. User authentication (no password verification)
2. Payload encryption (sensitive data exposed)
3. Token revocation mechanism
4. Rate limiting
5. Session management

MISSING - IMPORTANT ⚠️:
6. Key rotation strategy
7. Refresh tokens
8. IP-based restrictions
9. Request logging/monitoring
10. Multi-factor authentication

RECOMMENDED IMPLEMENTATION ROADMAP:
==================================

PHASE 1: IMMEDIATE SECURITY FIXES
---------------------------------

1. **Add User Authentication**
```python
# app/services/auth.py - Add password verification
@classmethod
def authenticate_user(cls, email: str, password: str) -> Optional[UserModel]:
    user = cls.get_user_by_email(email)
    if user and cls.verify_password(password, user.password_hash):
        return user
    return None

@classmethod
def hash_password(cls, password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

@classmethod
def verify_password(cls, password: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

2. **Implement Opaque Tokens**
```python
# app/services/token_service.py
import redis
import uuid
import json

class TokenService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def create_session_token(self, user_data: dict) -> str:
        session_id = str(uuid.uuid4())
        
        # Store user data server-side
        self.redis_client.setex(
            f"session:{session_id}",
            24 * 3600,  # 24 hours
            json.dumps(user_data)
        )
        
        # JWT only contains session ID
        payload = {
            "session_id": session_id,
            "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    def get_session_data(self, session_id: str) -> Optional[dict]:
        data = self.redis_client.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    def revoke_session(self, session_id: str):
        self.redis_client.delete(f"session:{session_id}")
```

3. **Add Rate Limiting**
```python
# app/middleware/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# In main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In endpoints
@limiter.limit("5/minute")  # 5 requests per minute
@router.post("/auth/token")
async def create_token(request: Request, ...):
    ...
```

PHASE 2: ENHANCED SECURITY
-------------------------

4. **Switch to RS256 with Key Rotation**
```python
# app/services/key_service.py
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class KeyService:
    @staticmethod
    def generate_key_pair():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def create_rs256_token(payload: dict, private_key: bytes) -> str:
        return jwt.encode(
            payload=payload,
            key=private_key,
            algorithm="RS256"
        )
    
    @staticmethod
    def verify_rs256_token(token: str, public_key: bytes) -> Optional[dict]:
        try:
            return jwt.decode(
                jwt=token,
                key=public_key,
                algorithms=["RS256"]
            )
        except jwt.InvalidTokenError:
            return None
```

5. **Add Refresh Tokens**
```python
# app/schemas/auth.py
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# app/services/auth.py
@classmethod
def create_token_pair(cls, user: UserModel) -> TokenResponse:
    # Short-lived access token (15 minutes)
    access_payload = {
        "user_id": user.email,
        "type": "access",
        "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
    }
    
    # Long-lived refresh token (7 days)
    refresh_payload = {
        "user_id": user.email,
        "type": "refresh",
        "exp": int((datetime.utcnow() + timedelta(days=7)).timestamp())
    }
    
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, "HS256")
    refresh_token = jwt.encode(refresh_payload, settings.JWT_REFRESH_SECRET, "HS256")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900  # 15 minutes
    )
```

PHASE 3: MONITORING & COMPLIANCE
-------------------------------

6. **Request Logging & Monitoring**
```python
# app/middleware/logging.py
import logging
from fastapi import Request
import time

logger = logging.getLogger("api_access")

async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}", extra={
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "path": request.url.path
    })
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code}", extra={
        "status_code": response.status_code,
        "process_time": process_time
    })
    
    return response
```

7. **Multi-Factor Authentication**
```python
# app/services/mfa_service.py
import pyotp
import qrcode

class MFAService:
    @staticmethod
    def generate_totp_secret(user_email: str) -> str:
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str) -> str:
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Arise Plot Management"
        )
        return totp_uri
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

CURRENT VULNERABILITIES TO FIX:
==============================

1. **JWT Payload Exposure** 🚨
   - Current: Anyone can decode payload
   - Fix: Use opaque tokens or JWE encryption

2. **No User Authentication** 🚨
   - Current: Anyone can request any role
   - Fix: Add password verification

3. **No Session Management** 🚨
   - Current: Tokens valid until expiry
   - Fix: Add revocation mechanism

4. **No Rate Limiting** ⚠️
   - Current: Unlimited requests
   - Fix: Add request throttling

5. **Weak Key Management** ⚠️
   - Current: Single static secret
   - Fix: Key rotation strategy

PRODUCTION-READY CHECKLIST:
===========================

Security:
□ User password authentication
□ Opaque tokens or JWE encryption
□ Rate limiting (per IP, per user)
□ Request logging and monitoring
□ Key rotation mechanism
□ Session revocation
□ HTTPS enforcement
□ Input validation hardening

Performance:
□ Redis for session storage
□ Database connection pooling
□ Caching for frequent queries
□ Async operations optimization

Compliance:
□ Audit logging
□ Data retention policies
□ GDPR compliance (if applicable)
□ Security headers
□ CORS configuration
□ API versioning strategy

Monitoring:
□ Health check endpoints
□ Metrics collection (Prometheus)
□ Error tracking (Sentry)
□ Performance monitoring (APM)
□ Alerting system

IMMEDIATE NEXT STEPS:
====================

1. **High Priority**: Implement user authentication with passwords
2. **High Priority**: Switch to opaque tokens for sensitive data
3. **Medium Priority**: Add rate limiting to auth endpoints
4. **Medium Priority**: Implement session revocation
5. **Low Priority**: Switch to RS256 for better key management

Remember: Security is a journey, not a destination! 🛡️
