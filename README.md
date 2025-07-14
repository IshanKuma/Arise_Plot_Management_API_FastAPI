# Arise Plot Management API

A robust FastAPI backend for managing land plots and economic zones with JWT-based authentication and role-based access control.

## 🚀 Features

- **JWT Authentication** with role-based permissions
- **Plot Management** (create, update, release, query)
- **Zone Master Data** management
- **Role-Based Access Control** (super_admin, zone_admin, normal_user)
- **Auto-Generated API Documentation** (Swagger UI & ReDoc)
- **Input Validation** with Pydantic schemas
- **Mock Data Support** for development (Firestore ready)

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Authentication & Permissions](#authentication--permissions)
- [Request/Response Schemas](#requestresponse-schemas)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Future Roadmap](#future-roadmap)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd arise_fastapi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/token` | Generate JWT token | No |

### Plot Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/plots/available` | Get available plots | Read plots |
| PUT | `/api/v1/plots/update-plot` | Update plot allocation | Write plots |
| PATCH | `/api/v1/plots/release-plot` | Release plot | Write plots |
| GET | `/api/v1/plots/plot-details` | Get detailed plot info | Read plots |

### User Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/users/create_user` | Create new user | Super admin only |
| PUT | `/api/v1/users/update_user` | Update user role/zone | Super admin only |
| GET | `/api/v1/users/list_users` | List all users | Super admin only |

### Zone Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/country/zones` | Create zone master data | Write zones |

## 🔐 Authentication & Permissions

### JWT Implementation Details
- **Algorithm**: HS256 (HMAC with SHA-256) - symmetric key encryption
- **Secret Key**: Stored in `JWT_SECRET_KEY` environment variable
- **Token Expiry**: 24 hours (86400 seconds)
- **Payload**: Contains userId, role, zone, permissions, issued time, expiry time
- **Security**: Token is signed and verified using the same secret key

**Important Security Notes**:
- HS256 uses symmetric encryption (same key for signing and verification)
- Secret key must be kept secure and rotated regularly
- For production, consider RS256 (public/private key pair) for enhanced security
- Current setup is development-friendly but requires security hardening for production

### User Storage & Management
- **Current Storage**: In-memory dictionary (development only)
- **User Creation**: Only `super_admin` can create users
- **User Updates**: Only `super_admin` can modify user roles/zones
- **Access Control**: Role-based permissions with zone restrictions for `zone_admin`
- **Production Note**: Replace with Firestore for persistent user storage

### User Roles
- **super_admin**: Full access to all zones and operations
- **zone_admin**: Access limited to assigned zone
- **normal_user**: Read-only access to plots

### Permission Matrix
| Role | Read Plots | Write Plots | Read Zones | Write Zones |
|------|------------|-------------|------------|-------------|
| super_admin | ✅ All zones | ✅ All zones | ✅ All zones | ✅ All zones |
| zone_admin | ✅ Assigned zone | ✅ Assigned zone | ✅ Assigned zone | ✅ Assigned zone |
| normal_user | ✅ All zones | ❌ | ✅ All zones | ❌ |

### Authentication Flow
1. **Request Token**: POST `/auth/token` with userId, role, zone
2. **Get JWT**: Receive 24-hour JWT token
3. **Use Token**: Include `Authorization: Bearer <token>` in requests
4. **Access Control**: Automatic permission and zone validation

## 📝 Request/Response Schemas

### Authentication

#### POST /auth/token
**Request:**
```json
{
  "userId": "admin001",
  "role": "super_admin",
  "zone": "GSEZ"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error (400):**
```json
{
  "error_code": "INVALID_ROLE",
  "message": "Invalid role provided",
  "details": {...}
}
```

### Plot Management

#### GET /plots/available
**Query Parameters:**
- `country` (optional): Filter by country
- `zoneCode` (optional): Filter by zone
- `category` (optional): Residential, Commercial, Industrial
- `phase` (optional): Phase number

**Response:**
```json
{
  "plots": [
    {
      "plotName": "GSEZ-R-001",
      "plotStatus": "Available",
      "category": "Residential",
      "phase": 1,
      "areaInSqm": 5000.0,
      "areaInHa": 0.5,
      "zoneCode": "GSEZ",
      "country": "Gabon"
    }
  ]
}
```

#### PUT /plots/update-plot
**Request:**
```json
{
  "country": "Gabon",
  "zoneCode": "GSEZ",
  "phase": 1,
  "plotName": "GSEZ-R-001",
  "companyName": "TechCorp Ltd",
  "sector": "Technology",
  "plotStatus": "Allocated",
  "activity": "Software Development",
  "investmentAmount": 1000000,
  "employmentGenerated": 50,
  "allocatedDate": "2024-07-04",
  "expiryDate": "2029-07-04"
}
```

**Response:**
```json
{
  "message": "Plot updated successfully",
  "plotName": "GSEZ-R-001",
  "status": "Allocated"
}
```

#### PATCH /plots/release-plot
**Request:**
```json
{
  "country": "Gabon",
  "zoneCode": "GSEZ",
  "plotName": "GSEZ-R-001",
  "plotStatus": "available"
}
```

**Response:**
```json
{
  "message": "Plot released successfully",
  "plotName": "GSEZ-R-001",
  "status": "available"
}
```

#### GET /plots/plot-details
**Query Parameters:**
- `country` (required): Country name
- `zoneCode` (required): Zone code

**Response:**
```json
{
  "metadata": {
    "country": "Gabon",
    "zoneCode": "GSEZ",
    "totalPlots": 10,
    "availablePlots": 7
  },
  "plots": [
    {
      "plotName": "GSEZ-R-001",
      "category": "Residential",
      "areaInHa": 0.5,
      "sector": "Housing",
      "activity": "Residential Development",
      "plotStatus": "Available",
      "companyName": null,
      "allocatedDate": null,
      "investmentAmount": null,
      "employmentGenerated": null
    }
  ]
}
```

### Zone Management

#### POST /country/zones
**Request:**
```json
{
  "country": "Gabon",
  "zoneCode": "NSEZ",
  "phase": 1,
  "landArea": 150.5,
  "zoneName": "New Special Economic Zone",
  "zoneType": "SEZ",
  "establishedDate": "2024-07-04"
}
```

**Response:**
```json
{
  "message": "Zone data saved successfully",
  "zoneCode": "NSEZ"
}
```

## 🛠️ Development Setup

### Project Structure
```
arise_fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/                    # API routes
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── plots.py           # Plot management endpoints
│   │   └── zones.py           # Zone management endpoints
│   ├── core/
│   │   └── config.py          # Application settings
│   ├── schemas/               # Pydantic models
│   │   ├── auth.py           # Authentication schemas
│   │   └── plots.py          # Plot/Zone schemas
│   ├── services/              # Business logic
│   │   ├── auth.py           # Authentication service
│   │   └── firestore.py      # Database service
│   └── utils/
│       └── auth.py           # Authentication utilities
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

### Environment Variables
Copy `.env.example` to `.env` and configure:

- **JWT_SECRET_KEY**: Secret key for JWT signing (HS256 symmetric encryption)
- **JWT_ALGORITHM**: JWT algorithm (HS256 - HMAC with SHA-256)
- **JWT_EXPIRE_HOURS**: Token expiry (24 hours)
- **FIREBASE_PROJECT_ID**: Firebase project ID
- **APP_NAME**: Application name
- **DEBUG**: Debug mode (True/False)

**Security Note**: The current implementation uses HS256 (symmetric key) for development. For production, consider RS256 (asymmetric key) for enhanced security.

### Code Quality
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking (if mypy installed)
mypy app/
```

## 🧪 Testing

### Manual Testing with curl

1. **Get JWT Token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "admin001",
    "role": "super_admin",
    "zone": "GSEZ"
  }'
```

2. **Test Protected Endpoint:**
```bash
curl -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Automated Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🚀 Deployment

### Current Support
- **Local Development**: uvicorn server
- **Traditional Hosting**: Any Python-compatible hosting
- **Docker**: Containerization ready

### Future Deployment Options
- **AWS Lambda**: Serverless deployment with Mangum
- **AWS Elastic Beanstalk**: Platform-as-a-Service
- **Vercel**: Serverless functions
- **Railway**: Simple deployment platform
- **Heroku**: Cloud platform

## 🔮 Future Roadmap

### Phase 1: Database Integration
- [ ] Replace mock data with real Firestore integration
- [ ] Add database connection pooling
- [ ] Implement data persistence

### Phase 2: API Enhancements
- [ ] Unify PUT/PATCH endpoints for plot updates
- [ ] Add bulk operations support
- [ ] Implement pagination for large datasets
- [ ] Add search and filtering capabilities

### Phase 3: Security & Performance
- [ ] Add rate limiting
- [ ] Implement refresh tokens
- [ ] Add request logging and monitoring
- [ ] Performance optimization

### Phase 4: Additional Features
- [ ] Email notifications
- [ ] File upload support
- [ ] Advanced reporting
- [ ] Multi-language support

### Phase 5: Deployment & DevOps
- [ ] Docker containerization
- [ ] AWS Lambda deployment
- [ ] CI/CD pipeline setup
- [ ] Infrastructure as Code (Terraform)
- [ ] Monitoring and alerting

## 📊 Current Implementation Status

### ✅ Completed Features
- JWT-based authentication system
- Role-based access control
- Plot CRUD operations
- Zone management
- API documentation (Swagger/ReDoc)
- Request/response validation
- Error handling
- Mock data service

### 🔄 In Progress
- Database integration planning
- Deployment strategy

### 📋 Pending
- Real Firestore integration
- Production deployment
- Comprehensive testing suite
- Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For questions or support, please contact the development team or create an issue in the repository.

---

**Version**: 1.0.0  
**Last Updated**: July 4, 2025  
**FastAPI Version**: 0.115.14  
**Python Version**: 3.8+
