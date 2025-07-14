# API Specifications - Request/Response Schema Documentation

## JWT Implementation Details

### JWT Token Structure
The API uses HS256 (HMAC with SHA-256) symmetric encryption for JWT tokens:

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "userId": "user_001",
    "role": "super_admin",
    "zone": "GSEZ",
    "permissions": {
      "read": ["plots", "zones", "users"],
      "write": ["plots", "zones", "users"]
    },
    "iat": 1720972800,
    "exp": 1721059200
  },
  "signature": "HMAC-SHA256-signature-here"
}
```

### Security Implementation
- **Secret Key**: Retrieved from `JWT_SECRET_KEY` environment variable
- **Algorithm**: HS256 (symmetric key - same key for signing and verification)
- **Expiry**: 24 hours (86400 seconds)
- **Verification**: All API endpoints verify token signature using the same secret key

---

## 1. Authentication API - POST /auth/token

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| userId | string | 50 | Mandatory | Must be a valid user identifier |
| role | string | 20 | Mandatory | Must be one of: `super_admin`, `zone_admin`, `normal_user` |
| zone | string | 10 | Mandatory | Must be a valid zone code (e.g., GSEZ, OSEZ) |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| access_token | string | 500 | Mandatory | JWT token with 24-hour expiry |
| token_type | string | 10 | Mandatory | Always "bearer" |
| expires_in | integer | - | Mandatory | Token expiry time in seconds (86400) |

### Response Schema - Error (400)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | MISSING_PARAMETERS, INVALID_ROLE, INVALID_ZONE |
| message | string | 200 | Mandatory | Human-readable error description |
| details | object | - | Optional | Additional error context |

---

## 2. Available Plots API - GET /plots/available

### Request Parameters (Query String)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| country | string | 50 | Optional | Must be a valid country name |
| zoneCode | string | 10 | Optional | Must be a valid zone code |
| category | string | 20 | Optional | Must be one of: Residential, Commercial, Industrial |
| phase | integer | - | Optional | Must be a positive integer |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| plots | array | - | Mandatory | Array of plot objects |
| plots[].plotName | string | 50 | Mandatory | Unique plot identifier |
| plots[].plotStatus | string | 20 | Mandatory | Available, Allocated, Reserved |
| plots[].category | string | 20 | Mandatory | Residential, Commercial, Industrial |
| plots[].phase | integer | - | Mandatory | Phase number |
| plots[].areaInSqm | decimal | - | Mandatory | Area in square meters |
| plots[].areaInHa | decimal | - | Mandatory | Area in hectares |
| plots[].zoneCode | string | 10 | Mandatory | Zone code |
| plots[].country | string | 50 | Mandatory | Country name |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, FORBIDDEN |
| message | string | 200 | Mandatory | Error description |

---

## 3. Plot Update API - PUT /update-plot

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| country | string | 50 | Mandatory | Must be a valid country name |
| zoneCode | string | 10 | Mandatory | Must be a valid zone code |
| phase | integer | - | Mandatory | Must be a positive integer |
| plotName | string | 50 | Mandatory | Must exist in the system |
| companyName | string | 100 | Optional | Company name for allocation |
| sector | string | 50 | Optional | Business sector |
| plotStatus | string | 20 | Mandatory | Available, Allocated, Reserved |
| activity | string | 100 | Optional | Business activity description |
| investmentAmount | decimal | - | Optional | Investment amount in USD |
| employmentGenerated | integer | - | Optional | Number of jobs created |
| allocatedDate | string | 10 | Optional | Date in YYYY-MM-DD format |
| expiryDate | string | 10 | Optional | Date in YYYY-MM-DD format |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| message | string | 100 | Mandatory | "Plot updated successfully" |
| plotName | string | 50 | Mandatory | Updated plot name |
| status | string | 20 | Mandatory | Updated status |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, FORBIDDEN, PLOT_NOT_FOUND |
| message | string | 200 | Mandatory | Error description |

---

## 4. Plot Release API - PATCH /release-plot

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| country | string | 50 | Mandatory | Must be a valid country name |
| zoneCode | string | 10 | Mandatory | Must be a valid zone code |
| plotName | string | 50 | Mandatory | Must exist in the system |
| plotStatus | string | 20 | Mandatory | Must be "available" |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| message | string | 100 | Mandatory | "Plot released successfully" |
| plotName | string | 50 | Mandatory | Released plot name |
| status | string | 20 | Mandatory | "available" |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, FORBIDDEN, PLOT_NOT_FOUND |
| message | string | 200 | Mandatory | Error description |

---

## 5. Zone Master API - POST /country/zones

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| country | string | 50 | Mandatory | Must be a valid country name |
| zoneCode | string | 10 | Mandatory | Must be unique zone identifier |
| phase | integer | - | Mandatory | Must be a positive integer |
| landArea | decimal | - | Mandatory | Total land area in hectares |
| zoneName | string | 100 | Optional | Descriptive zone name |
| zoneType | string | 30 | Optional | SEZ, Industrial, Commercial |
| establishedDate | string | 10 | Optional | Date in YYYY-MM-DD format |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| message | string | 100 | Mandatory | "Zone data saved successfully" |
| zoneCode | string | 10 | Mandatory | Created/updated zone code |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, FORBIDDEN, ZONE_EXISTS |
| message | string | 200 | Mandatory | Error description |

---

## 6. Open API - GET /plot-details

### Request Parameters (Query String)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| country | string | 50 | Mandatory | Must be a valid country name |
| zoneCode | string | 10 | Mandatory | Must be a valid zone code |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| metadata | object | - | Mandatory | Zone metadata information |
| metadata.country | string | 50 | Mandatory | Country name |
| metadata.zoneCode | string | 10 | Mandatory | Zone code |
| metadata.totalPlots | integer | - | Mandatory | Total number of plots |
| metadata.availablePlots | integer | - | Mandatory | Number of available plots |
| plots | array | - | Mandatory | Array of detailed plot objects |
| plots[].plotName | string | 50 | Mandatory | Plot identifier |
| plots[].category | string | 20 | Mandatory | Plot category |
| plots[].areaInHa | decimal | - | Mandatory | Area in hectares |
| plots[].sector | string | 50 | Optional | Business sector |
| plots[].activity | string | 100 | Optional | Business activity |
| plots[].plotStatus | string | 20 | Mandatory | Current status |
| plots[].companyName | string | 100 | Optional | Allocated company name |
| plots[].allocatedDate | string | 10 | Optional | Allocation date |
| plots[].investmentAmount | decimal | - | Optional | Investment amount |
| plots[].employmentGenerated | integer | - | Optional | Jobs created |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, FORBIDDEN |
| message | string | 200 | Mandatory | Error description |

---

## 7. User Management API - POST /users/create_user

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| email | string | 100 | Mandatory | Must be valid email format |
| role | string | 20 | Mandatory | Must be one of: super_admin, zone_admin, normal_user |
| zone | string | 10 | Mandatory | Must be valid zone code (GSEZ, OSEZ, GABON, TEST) |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" with super_admin role |

### Response Schema - Success (201)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| email | string | 100 | Mandatory | User email address |
| role | string | 20 | Mandatory | Assigned user role |
| zone | string | 10 | Mandatory | Assigned zone code |
| createdDate | string | 30 | Mandatory | ISO 8601 timestamp |
| lastModified | string | 30 | Mandatory | ISO 8601 timestamp |

### Response Schema - Error (400/401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | USER_EXISTS, INVALID_INPUT, INSUFFICIENT_PERMISSIONS |
| message | string | 200 | Mandatory | Error description |
| details | object | - | Optional | Additional error context |

---

## 8. User Management API - PUT /users/update_user

### Request Schema
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| email | string | 100 | Mandatory | Must be valid email of existing user |
| role | string | 20 | Optional | Must be one of: super_admin, zone_admin, normal_user |
| zone | string | 10 | Optional | Must be valid zone code (GSEZ, OSEZ, GABON, TEST) |

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" with super_admin role |

### Response Schema - Success (200)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| email | string | 100 | Mandatory | User email address |
| role | string | 20 | Mandatory | Updated user role |
| zone | string | 10 | Mandatory | Updated zone code |
| createdDate | string | 30 | Mandatory | Original creation timestamp |
| lastModified | string | 30 | Mandatory | Updated modification timestamp |

### Response Schema - Error (400/401/403/404)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | USER_NOT_FOUND, NO_UPDATE_FIELDS, INSUFFICIENT_PERMISSIONS |
| message | string | 200 | Mandatory | Error description |
| details | object | - | Optional | Additional error context |

---

## 9. User Management API - GET /users/list_users

### Request Parameters
No query parameters required.

### Request Headers
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| Authorization | string | 600 | Mandatory | Format: "Bearer {jwt_token}" with super_admin role |

### Response Schema - Success (200)
Response is an array of user objects:

| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| [].email | string | 100 | Mandatory | User email address |
| [].role | string | 20 | Mandatory | User role |
| [].zone | string | 10 | Mandatory | User zone code |
| [].createdDate | string | 30 | Mandatory | Creation timestamp |
| [].lastModified | string | 30 | Mandatory | Last modification timestamp |

### Response Schema - Error (401/403)
| Message Element | Data Type | Max Length | Mandatory/Optional | Business Validation |
|----------------|-----------|------------|-------------------|-------------------|
| error_code | string | 50 | Mandatory | UNAUTHORIZED, INSUFFICIENT_PERMISSIONS |
| message | string | 200 | Mandatory | Error description |

---

## User Storage Implementation

### Current Implementation (Development)
- **Storage**: In-memory Python dictionary
- **Key**: User email address (lowercase)
- **Value**: UserModel object with email, role, zone, timestamps
- **Persistence**: Data lost on server restart
- **Concurrency**: Not thread-safe

### Data Structure
```python
_users: Dict[str, UserModel] = {
    "user@example.com": UserModel(
        email="user@example.com",
        role="zone_admin",
        zone="GSEZ",
        createdDate=datetime(2024, 1, 1, 10, 0, 0),
        lastModified=datetime(2024, 1, 1, 10, 0, 0)
    )
}
```

### Production Requirements
- **Storage**: Firestore collection "users"
- **Indexing**: Email (unique), role, zone
- **Security**: Firestore security rules
- **Backup**: Automatic Firestore backups
- **Concurrency**: Firestore handles concurrent access

---

## Security & Access Control

### Role-Based Permission Matrix
| Operation | super_admin | zone_admin | normal_user |
|-----------|-------------|------------|-------------|
| Create Users | ✅ | ❌ | ❌ |
| Update Users | ✅ | ❌ | ❌ |
| List Users | ✅ | ❌ | ❌ |
| Read All Plots | ✅ | ✅ (zone only) | ✅ |
| Write Plots | ✅ | ✅ (zone only) | ❌ |
| Read Zones | ✅ | ✅ (zone only) | ✅ |
| Write Zones | ✅ | ✅ (zone only) | ❌ |

### JWT Security Considerations
- **Algorithm**: HS256 (symmetric) - development friendly
- **Secret Rotation**: Manual (requires restart)
- **Token Storage**: Client responsibility
- **Revocation**: Not implemented (tokens valid until expiry)
- **Production Recommendations**: 
  - Use RS256 (asymmetric keys)
  - Implement token blacklisting
  - Add refresh token mechanism
  - Store secrets in secure key management

---
