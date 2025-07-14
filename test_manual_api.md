# Manual API Testing Guide

## Prerequisites
1. Start the FastAPI server:
```bash
cd /home/user/Desktop/arise_fastapi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Server should be running on: http://localhost:8000
3. API docs available at: http://localhost:8000/docs

---

## 🔐 1. Authentication Tests

### Test 1.1: Valid Token Generation (super_admin)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "admin001",
    "role": "super_admin",
    "zone": "GSEZ"
  }'
```

**Expected Response (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Test 1.2: Valid Token Generation (zone_admin)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "zone_admin001",
    "role": "zone_admin",
    "zone": "OSEZ"
  }'
```

### Test 1.3: Valid Token Generation (normal_user)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user001",
    "role": "normal_user",
    "zone": "GABON"
  }'
```

### Test 1.4: Invalid Role
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user001",
    "role": "invalid_role",
    "zone": "GSEZ"
  }'
```

**Expected Response (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "role"],
      "msg": "value is not a valid enumeration member",
      "type": "value_error.enum"
    }
  ]
}
```

### Test 1.5: Invalid Zone
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user001",
    "role": "super_admin",
    "zone": "INVALID_ZONE"
  }'
```

**Expected Response (400)**:
```json
{
  "error_code": "INVALID_ZONE",
  "message": "Invalid zone code provided",
  "details": {"provided_zone": "INVALID_ZONE"}
}
```

---

## 👥 2. User Management Tests (super_admin only)

### Test 2.1: Create User (Success)
```bash
# First get super_admin token
SUPER_ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}' \
  | jq -r '.access_token')

# Create new user
curl -X POST "http://localhost:8000/api/v1/users/create_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "email": "newuser@example.com",
    "role": "zone_admin",
    "zone": "GSEZ"
  }'
```

**Expected Response (200)**:
```json
{
  "email": "newuser@example.com",
  "role": "zone_admin",
  "zone": "GSEZ",
  "createdDate": "2025-07-14T10:30:00Z",
  "lastModified": "2025-07-14T10:30:00Z"
}
```

### Test 2.2: Create User - Duplicate Email
```bash
# Try to create same user again
curl -X POST "http://localhost:8000/api/v1/users/create_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "email": "newuser@example.com",
    "role": "normal_user",
    "zone": "OSEZ"
  }'
```

**Expected Response (400)**:
```json
{
  "error_code": "USER_EXISTS",
  "message": "User with this email already exists",
  "details": {"email": "newuser@example.com"}
}
```

### Test 2.3: Create User - Invalid Zone
```bash
curl -X POST "http://localhost:8000/api/v1/users/create_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "email": "testuser@example.com",
    "role": "zone_admin",
    "zone": "INVALID"
  }'
```

**Expected Response (400)**:
```json
{
  "error_code": "INVALID_INPUT",
  "message": "Invalid zone: INVALID",
  "details": {"field": "zone"}
}
```

### Test 2.4: Create User - Insufficient Permissions (zone_admin trying)
```bash
# Get zone_admin token
ZONE_ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "zone001", "role": "zone_admin", "zone": "GSEZ"}' \
  | jq -r '.access_token')

# Try to create user with zone_admin token
curl -X POST "http://localhost:8000/api/v1/users/create_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ZONE_ADMIN_TOKEN" \
  -d '{
    "email": "forbidden@example.com",
    "role": "normal_user",
    "zone": "GSEZ"
  }'
```

**Expected Response (403)**:
```json
{
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "message": "Only super_admin can create users",
  "details": {"required_role": "super_admin", "current_role": "zone_admin"}
}
```

### Test 2.5: Update User (Success)
```bash
curl -X PUT "http://localhost:8000/api/v1/users/update_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "email": "newuser@example.com",
    "role": "normal_user",
    "zone": "OSEZ"
  }'
```

### Test 2.6: Update User - User Not Found
```bash
curl -X PUT "http://localhost:8000/api/v1/users/update_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "email": "nonexistent@example.com",
    "role": "normal_user"
  }'
```

**Expected Response (404)**:
```json
{
  "error_code": "USER_NOT_FOUND",
  "message": "User not found",
  "details": {"email": "nonexistent@example.com"}
}
```

### Test 2.7: List All Users
```bash
curl -X GET "http://localhost:8000/api/v1/users/list_users" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

**Expected Response (200)**:
```json
[
  {
    "email": "newuser@example.com",
    "role": "normal_user",
    "zone": "OSEZ",
    "createdDate": "2025-07-14T10:30:00Z",
    "lastModified": "2025-07-14T10:35:00Z"
  }
]
```

---

## 📊 3. Plot Management Tests

### Test 3.1: Get Available Plots (All)
```bash
curl -X GET "http://localhost:8000/api/v1/plots/available" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

### Test 3.2: Get Available Plots (Filtered by Country)
```bash
curl -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

### Test 3.3: Get Available Plots (Filtered by Zone - zone_admin)
```bash
curl -X GET "http://localhost:8000/api/v1/plots/available?zoneCode=GSEZ" \
  -H "Authorization: Bearer $ZONE_ADMIN_TOKEN"
```

### Test 3.4: Update Plot (Success)
```bash
curl -X PUT "http://localhost:8000/api/v1/plots/update-plot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "country": "Gabon",
    "zoneCode": "GSEZ",
    "phase": 1,
    "plotName": "GSEZ-R-001",
    "companyName": "Test Company Ltd",
    "sector": "Technology",
    "plotStatus": "Allocated",
    "activity": "Software Development",
    "investmentAmount": 250000.0,
    "employmentGenerated": 15,
    "allocatedDate": "2025-07-14",
    "expiryDate": "2030-07-14"
  }'
```

### Test 3.5: Release Plot
```bash
curl -X PATCH "http://localhost:8000/api/v1/plots/release-plot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "country": "Gabon",
    "zoneCode": "GSEZ",
    "plotName": "GSEZ-R-001",
    "plotStatus": "available"
  }'
```

### Test 3.6: Get Plot Details
```bash
curl -X GET "http://localhost:8000/api/v1/plots/plot-details?country=Gabon&zoneCode=GSEZ" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"
```

### Test 3.7: Unauthorized Access (No Token)
```bash
curl -X GET "http://localhost:8000/api/v1/plots/available"
```

**Expected Response (401)**:
```json
{
  "detail": "Not authenticated"
}
```

---

## 🌍 4. Zone Management Tests

### Test 4.1: Create Zone (Success)
```bash
curl -X POST "http://localhost:8000/api/v1/country/zones" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{
    "country": "Gabon",
    "zoneCode": "NSEZ",
    "phase": 3,
    "landArea": 150.5,
    "zoneName": "Northern Special Economic Zone",
    "zoneType": "Industrial",
    "establishedDate": "2025-07-14"
  }'
```

### Test 4.2: Create Zone - Insufficient Permissions (normal_user)
```bash
NORMAL_USER_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "user001", "role": "normal_user", "zone": "GABON"}' \
  | jq -r '.access_token')

curl -X POST "http://localhost:8000/api/v1/country/zones" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NORMAL_USER_TOKEN" \
  -d '{
    "country": "Gabon",
    "zoneCode": "TESTZ",
    "phase": 1,
    "landArea": 50.0
  }'
```

**Expected Response (403)**:
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions for write access to zones"
}
```

---

## 🚀 5. Health Check Tests

### Test 5.1: Root Endpoint
```bash
curl -X GET "http://localhost:8000/"
```

**Expected Response (200)**:
```json
{
  "message": "Arise Plot Management API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### Test 5.2: Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

**Expected Response (200)**:
```json
{
  "status": "healthy",
  "service": "Arise Plot Management API",
  "version": "1.0.0"
}
```

---

## 🔧 Helper Scripts

### Get and Store Tokens
```bash
# Store tokens for reuse
echo "Getting tokens..."

SUPER_ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}' \
  | jq -r '.access_token')

ZONE_ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "zone001", "role": "zone_admin", "zone": "GSEZ"}' \
  | jq -r '.access_token')

NORMAL_USER_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "user001", "role": "normal_user", "zone": "GABON"}' \
  | jq -r '.access_token')

echo "Super Admin Token: $SUPER_ADMIN_TOKEN"
echo "Zone Admin Token: $ZONE_ADMIN_TOKEN"
echo "Normal User Token: $NORMAL_USER_TOKEN"
```

### Decode JWT Payload (Security Testing)
```bash
# Extract and decode JWT payload
echo $SUPER_ADMIN_TOKEN | cut -d. -f2 | base64 -d | jq
```

### Test Complete User Flow
```bash
#!/bin/bash
echo "=== Complete API Test Flow ==="

# 1. Get super_admin token
echo "1. Getting super_admin token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}' \
  | jq -r '.access_token')

# 2. Create a user
echo "2. Creating a new user..."
curl -s -X POST "http://localhost:8000/api/v1/users/create_user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email": "testflow@example.com", "role": "zone_admin", "zone": "GSEZ"}' \
  | jq

# 3. List users
echo "3. Listing all users..."
curl -s -X GET "http://localhost:8000/api/v1/users/list_users" \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# 4. Get available plots
echo "4. Getting available plots..."
curl -s -X GET "http://localhost:8000/api/v1/plots/available" \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# 5. Create a zone
echo "5. Creating a new zone..."
curl -s -X POST "http://localhost:8000/api/v1/country/zones" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"country": "Gabon", "zoneCode": "TESTZ", "phase": 1, "landArea": 100.0}' \
  | jq

echo "=== Test Flow Complete ==="
```

---

## 📝 Notes for Testing

1. **jq Required**: Install `jq` for JSON formatting: `sudo apt install jq`
2. **Token Expiry**: Tokens expire in 24 hours (86400 seconds)
3. **CORS**: API allows requests from localhost:3000, :8080, :3001
4. **Mock Data**: Currently using in-memory storage (resets on restart)
5. **Security**: Remember these are development tests - production needs authentication

Save this file and run tests step by step to verify all API functionality!
