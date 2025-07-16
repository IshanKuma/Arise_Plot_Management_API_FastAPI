# Secret Key Authentication Implementation Guide

## 🔐 Overview

Your JWT authentication system now requires a **secret key** parameter to verify user identity before issuing JWT tokens. This adds a crucial security layer that prevents unauthorized token generation.

## 🔄 New Authentication Flow

### Before (Insecure):
```json
POST /auth/token
{
  "userId": "admin001",
  "role": "super_admin", 
  "zone": "GSEZ"
}
```
☠️ **Anyone could claim to be any user!**

### After (Secure):
```json
POST /auth/token
{
  "userId": "admin001",
  "role": "super_admin",
  "zone": "GSEZ", 
  "secretKey": "admin-secret-key-2025"
}
```
✅ **Must provide valid secret key to get JWT token!**

## 🛡️ Security Implementation

### 1. Secret Key Storage
- Secret keys are **bcrypt hashed** before storage
- Plain text secrets are **never stored**
- Hash verification happens during authentication

### 2. Default User Secrets
| User ID | Default Secret | Role |
|---------|---------------|------|
| admin001 | admin-secret-key-2025 | super_admin |
| zone001 | zone-admin-secret-2025 | zone_admin |
| user001 | normal-user-secret-2025 | normal_user |

### 3. Validation Rules
- Secret key must be **minimum 8 characters**
- Bcrypt verification with stored hash
- Failed verification returns **401 Unauthorized**

## 📝 API Changes

### Updated Request Schema
```json
{
  "userId": "string (max 50 chars)",
  "role": "super_admin|zone_admin|normal_user", 
  "zone": "string (4-6 uppercase letters)",
  "secretKey": "string (8-128 chars)"
}
```

### New Error Response (401)
```json
{
  "error_code": "INVALID_SECRET_KEY",
  "message": "Invalid secret key for the specified user", 
  "details": {"userId": "admin001"}
}
```

## 🧪 Testing the Implementation

### Test 1: Valid Authentication
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "admin001",
    "role": "super_admin",
    "zone": "GSEZ",
    "secretKey": "admin-secret-key-2025"
  }'
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Test 2: Invalid Secret Key
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "admin001", 
    "role": "super_admin",
    "zone": "GSEZ",
    "secretKey": "wrong-secret"
  }'
```

**Expected Response (401):**
```json
{
  "error_code": "INVALID_SECRET_KEY",
  "message": "Invalid secret key for the specified user",
  "details": {"userId": "admin001"}
}
```

### Test 3: Non-existent User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "hacker123",
    "role": "super_admin", 
    "zone": "GSEZ",
    "secretKey": "any-secret"
  }'
```

**Expected Response (401):**
```json
{
  "error_code": "INVALID_SECRET_KEY", 
  "message": "Invalid secret key for the specified user",
  "details": {"userId": "hacker123"}
}
```

## 🔧 Managing User Secrets

### Using the Secret Key Manager
Run the utility script to manage secrets:
```bash
python secret_key_manager.py
```

Options:
1. **Generate default user secret hashes** - For initial setup
2. **Test existing secret verification** - Verify current hashes work
3. **Generate new user secret hash** - Add new users
4. **Exit**

### Adding New Users Programmatically
```python
from app.services.auth import AuthService

# Add a new user with secret
AuthService.add_user_secret("newuser123", "their-secret-key-2025")
```

### Manual Hash Generation
```python
import bcrypt

secret = "your-secret-key"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(secret.encode('utf-8'), salt)
print(hashed.decode('utf-8'))
```

## 🚀 Production Considerations

### 1. Secret Distribution
- **Secure channels**: Distribute secrets via encrypted email, secure messaging
- **One-time sharing**: Share secrets once during user onboarding
- **Documentation**: Document which users have which secrets

### 2. Secret Rotation
- **Regular rotation**: Change secrets every 90 days
- **Compromised secrets**: Immediate rotation if secret is compromised
- **Version tracking**: Keep track of secret versions

### 3. Storage Security
- **Database encryption**: Store hashed secrets in encrypted database
- **Access control**: Limit who can view/modify secrets
- **Audit logging**: Log all secret-related operations

### 4. Alternative Approaches
For enhanced security, consider:
- **HMAC signatures**: Time-based authentication codes
- **Certificate-based auth**: X.509 certificates for users
- **Multi-factor auth**: Combine secrets with TOTP codes

## 🔍 Security Benefits

### ✅ What This Fixes:
1. **Prevents impersonation**: Can't claim to be another user
2. **Adds authentication layer**: Must prove identity before JWT
3. **Bcrypt protection**: Secrets are properly hashed
4. **Audit trail**: Failed attempts are logged

### ⚠️ What This Doesn't Fix:
1. **JWT payload exposure**: Still visible to anyone with token
2. **Token revocation**: No way to invalidate tokens early
3. **Session management**: No server-side session tracking
4. **Rate limiting**: No protection against brute force

## 📋 Next Steps for Enhanced Security

1. **Implement opaque tokens** - Hide sensitive data in JWT payload
2. **Add rate limiting** - Prevent brute force attacks on secrets
3. **Session management** - Server-side token revocation
4. **Audit logging** - Track all authentication attempts
5. **Multi-factor auth** - Additional security layer

## 🎯 Summary

Your authentication system is now **significantly more secure**:
- ✅ Secret key required for JWT issuance
- ✅ Bcrypt hashing for secret storage
- ✅ Proper error handling for invalid secrets
- ✅ Existing API endpoints unchanged
- ✅ Easy secret management utilities

**Result**: Only users with valid secret keys can obtain JWT tokens, preventing unauthorized access to your API!
