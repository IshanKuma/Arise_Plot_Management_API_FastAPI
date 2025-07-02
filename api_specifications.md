# API Specifications - Request/Response Schema Documentation

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

## Common Business Validations

### Role-Based Permissions
- **super_admin**: Full read/write access to all zones
- **zone_admin**: Read/write access only to assigned zone
- **normal_user**: Read-only access to plots

### Zone Codes
- Must follow format: 4-6 uppercase letters (e.g., GSEZ, OSEZ)
- Must exist in the zone master data

### Plot Status Values
- **Available**: Plot is free for allocation
- **Allocated**: Plot is assigned to a company
- **Reserved**: Plot is temporarily held

### Date Format
- All dates must be in ISO 8601 format: YYYY-MM-DD
- Future dates validation where applicable

### Numeric Validations
- Areas must be positive decimal values
- Phase numbers must be positive integers
- Investment amounts must be non-negative
- Employment numbers must be non-negative integers

---

## Error Codes Reference

| Error Code | HTTP Status | Description |
|-----------|-------------|-------------|
| MISSING_PARAMETERS | 400 | Required parameters are missing |
| INVALID_ROLE | 400 | Role is not in allowed values |
| INVALID_ZONE | 400 | Zone code is invalid |
| UNAUTHORIZED | 401 | Invalid or expired JWT token |
| FORBIDDEN | 403 | Insufficient permissions |
| PLOT_NOT_FOUND | 404 | Plot does not exist |
| ZONE_EXISTS | 409 | Zone code already exists |
| INTERNAL_ERROR | 500 | Server internal error |
