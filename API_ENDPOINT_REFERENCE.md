# 🚀 Arise Plot Management API - Complete Endpoint Reference

## 📡 API Base Configuration
- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`
- **Documentation**: 
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

---

## 🔐 AUTHENTICATION ENDPOINT

### POST `/api/v1/auth/token` - Generate JWT Token

**Purpose**: Generate JWT access token with dual-layer security authentication

#### 📤 Request Details
```http
POST /api/v1/auth/token
Content-Type: application/json
Authorization: Secret arise-master-auth-secret-2025
```

#### 📋 Request Headers
| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | ✅ Yes | JSON content type |
| `Authorization` | `Secret <secret-key>` | ✅ Yes | Authentication secret |

#### 📦 Request Body Schema
```json
{
  "userId": "string",     // Max 50 chars, required
  "role": "string",       // Enum: super_admin, zone_admin, normal_user
  "zone": "string"        // Max 10 chars, valid zone code
}
```

#### 🎯 Valid Input Values

**🔑 Secret Key (Authorization Header):**
- **Valid**: `arise-master-auth-secret-2025`
- **Format**: `Authorization: Secret arise-master-auth-secret-2025`

**👤 User ID (Body):**
- **Type**: String (max 50 characters)
- **Examples**: `"admin001"`, `"user123"`, `"manager_gsez"`
- **Pattern**: Any alphanumeric string

**🎭 Role (Body):**
- **Valid Values**: 
  - `"super_admin"` - Full access to all zones
  - `"zone_admin"` - Access to assigned zone only
  - `"normal_user"` - Read-only access
- **Invalid**: `"admin"`, `"user"`, `"manager"`

**🌍 Zone (Body):**
- **Valid Values**: `"GSEZ"`, `"OSEZ"`, `"GABON"`, `"TEST"`
- **Format**: 4-6 uppercase letters
- **Invalid**: `"gsez"`, `"zone1"`, `"INVALID"`

#### ✅ Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### ❌ Error Responses

**401 Unauthorized - Missing Authorization Header**
```json
{
  "detail": {
    "error_code": "MISSING_AUTHORIZATION",
    "message": "Authorization header is required",
    "details": {
      "expected_format": "Authorization: Secret <secret-key>"
    }
  }
}
```

**401 Unauthorized - Invalid Authorization Format**
```json
{
  "detail": {
    "error_code": "INVALID_AUTHORIZATION_FORMAT", 
    "message": "Invalid Authorization header format",
    "details": {
      "expected_format": "Authorization: Secret <secret-key>"
    }
  }
}
```

**401 Unauthorized - Invalid Secret Key**
```json
{
  "detail": {
    "error_code": "UNAUTHORIZED",
    "message": "Invalid authentication secret key",
    "details": {
      "reason": "Secret key mismatch"
    }
  }
}
```

**400 Bad Request - Invalid Zone**
```json
{
  "detail": {
    "error_code": "INVALID_ZONE",
    "message": "Invalid zone code. Must be a valid zone identifier (e.g., GSEZ, OSEZ)",
    "details": {
      "provided_zone": "INVALID"
    }
  }
}
```

**422 Unprocessable Entity - Invalid Role**
```json
{
  "detail": [
    {
      "loc": ["body", "role"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum",
      "ctx": {
        "enum_values": ["super_admin", "zone_admin", "normal_user"]
      }
    }
  ]
}
```

---

## 📊 PLOT MANAGEMENT ENDPOINTS

### GET `/api/v1/plots/available` - Get Available Plots

**Purpose**: Retrieve list of available plots with filtering

#### 📤 Request Details
```http
GET /api/v1/plots/available?country=Gabon&zoneCode=GSEZ
Authorization: Bearer <jwt_token>
```

#### 📋 Request Headers
| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Bearer <jwt_token>` | ✅ Yes | JWT token from auth endpoint |

#### 🔍 Query Parameters
| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `country` | string | ❌ No | Filter by country | `"Gabon"` |
| `zoneCode` | string | ❌ No | Filter by zone | `"GSEZ"`, `"OSEZ"`, `"GABON"`, `"TEST"` |
| `category` | string | ❌ No | Filter by category | `"Residential"`, `"Commercial"`, `"Industrial"` |
| `phase` | integer | ❌ No | Filter by phase | `1`, `2`, `3` |

#### ✅ Success Response (200 OK)
```json
{
  "plots": [
    {
      "plotName": "GSEZ-R-001",
      "plotStatus": "Available", 
      "category": "Residential",
      "phase": 1,
      "areaInSqm": "5000.0",
      "areaInHa": "0.5",
      "zoneCode": "GSEZ",
      "country": "Gabon"
    }
  ]
}
```

### PUT `/api/v1/plots/update-plot` - Update Plot

**Purpose**: Update plot allocation details

#### 📤 Request Details
```http
PUT /api/v1/plots/update-plot
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### 📦 Request Body Schema
```json
{
  "plotName": "GSEZ-C-002",
  "zoneCode": "GSEZ", 
  "country": "Gabon",
  "phase": 1,
  "plotStatus": "Allocated",
  "companyName": "TechCorp Ltd",
  "sector": "Technology",
  "activity": "Software Development",
  "investmentAmount": 500000.0,
  "employmentGenerated": 25,
  "allocatedDate": "2024-01-15",
  "expiryDate": "2029-01-15"
}
```

### PATCH `/api/v1/plots/release-plot` - Release Plot

**Purpose**: Release a plot (set to available status)

#### 📤 Request Details
```http
PATCH /api/v1/plots/release-plot
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### 📦 Request Body Schema
```json
{
  "plotName": "GSEZ-C-002",
  "zoneCode": "GSEZ",
  "country": "Gabon",
  "plotStatus": "Available"
}
```

### GET `/api/v1/plots/plot-details` - Get Plot Details

**Purpose**: Get detailed information about plots in a zone

#### 📤 Request Details
```http
GET /api/v1/plots/plot-details?country=Gabon&zoneCode=GSEZ
Authorization: Bearer <jwt_token>
```

#### 🔍 Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `country` | string | ✅ Yes | Country name |
| `zoneCode` | string | ✅ Yes | Zone code |

---

## 👥 USER MANAGEMENT ENDPOINTS

### POST `/api/v1/users/create_user` - Create User (Super Admin Only)

**Purpose**: Create a new user (requires super_admin role)

#### 📤 Request Details
```http
POST /api/v1/users/create_user
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### 📦 Request Body Schema
```json
{
  "email": "user@example.com",
  "role": "zone_admin", 
  "zone": "GSEZ"
}
```

### PUT `/api/v1/users/update_user` - Update User (Super Admin Only)

**Purpose**: Update user role/zone (requires super_admin role)

#### 📤 Request Details
```http
PUT /api/v1/users/update_user
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### 📦 Request Body Schema
```json
{
  "email": "user@example.com",
  "role": "normal_user",
  "zone": "OSEZ"
}
```

### GET `/api/v1/users/list_users` - List Users (Super Admin Only)

**Purpose**: List all users (requires super_admin role)

#### 📤 Request Details
```http
GET /api/v1/users/list_users
Authorization: Bearer <jwt_token>
```

---

## 🌍 ZONE MANAGEMENT ENDPOINTS

### POST `/api/v1/country/zones` - Create Zone

**Purpose**: Create zone master data

#### 📤 Request Details
```http
POST /api/v1/country/zones
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### 📦 Request Body Schema
```json
{
  "country": "Gabon",
  "zoneCode": "NSEZ",
  "phase": 1,
  "landArea": 150.0,
  "zoneName": "New Special Economic Zone",
  "zoneType": "SEZ",
  "establishedDate": "2024-07-16"
}
```

---

## 🧪 COMPLETE TESTING EXAMPLES

### 1. Authentication Flow Test

```bash
# Step 1: Get JWT Token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{
    "userId": "admin001",
    "role": "super_admin", 
    "zone": "GSEZ"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 86400
# }
```

### 2. Use JWT Token for Protected Endpoint

```bash
# Step 2: Use JWT Token
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 3. Test All Error Scenarios

```bash
# Missing Authorization Header
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}'

# Wrong Authorization Format  
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer arise-master-auth-secret-2025" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}'

# Invalid Secret Key
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret wrong-secret-key" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}'

# Invalid Zone
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "INVALID"}'

# Invalid Role (will return 422)
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{"userId": "admin001", "role": "invalid_role", "zone": "GSEZ"}'
```

---

## 🔒 Role-Based Access Control

### Permission Matrix
| Role | Read Plots | Write Plots | Read Zones | Write Zones | User Management |
|------|------------|-------------|------------|-------------|-----------------|
| `super_admin` | ✅ All zones | ✅ All zones | ✅ All zones | ✅ All zones | ✅ Full access |
| `zone_admin` | ✅ Assigned zone | ✅ Assigned zone | ✅ Assigned zone | ✅ Assigned zone | ❌ No access |
| `normal_user` | ✅ All zones | ❌ No access | ✅ All zones | ❌ No access | ❌ No access |

### Role Testing Examples

```bash
# Super Admin Token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{"userId": "admin001", "role": "super_admin", "zone": "GSEZ"}'

# Zone Admin Token  
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{"userId": "zone_manager", "role": "zone_admin", "zone": "GSEZ"}'

# Normal User Token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{"userId": "viewer001", "role": "normal_user", "zone": "GSEZ"}'
```

---

## 🚨 Common Error Codes

| HTTP Status | Error Code | Description | Solution |
|-------------|------------|-------------|----------|
| 401 | `MISSING_AUTHORIZATION` | No Authorization header | Add `Authorization: Secret <key>` |
| 401 | `INVALID_AUTHORIZATION_FORMAT` | Wrong header format | Use `Secret` not `Bearer` |
| 401 | `UNAUTHORIZED` | Invalid secret key | Use correct secret key |
| 400 | `INVALID_ZONE` | Invalid zone code | Use valid zone (GSEZ/OSEZ/GABON/TEST) |
| 400 | `INVALID_ROLE` | Invalid role | Use valid role (super_admin/zone_admin/normal_user) |
| 422 | Validation Error | Invalid request body | Check request schema |
| 403 | `FORBIDDEN` | Insufficient permissions | Use token with required role |

---

## 🔧 Development Tools

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Environment Variables Required
```bash
# .env file
JWT_SECRET_KEY=arise-plot-management-super-secret-key-change-in-production-2025
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
AUTH_SECRET_KEY=arise-master-auth-secret-2025
```

---

## 📝 Quick Reference Summary

**🔑 To get JWT token:**
1. Use `Authorization: Secret arise-master-auth-secret-2025` header
2. POST to `/api/v1/auth/token` with userId, role, zone in body
3. Get `access_token` from response

**🎫 To use JWT token:**
1. Use `Authorization: Bearer <access_token>` header  
2. Call any protected endpoint
3. Token expires in 24 hours

**🎭 Role hierarchy:**
- `super_admin` > `zone_admin` > `normal_user`
- Higher roles can access everything lower roles can access
