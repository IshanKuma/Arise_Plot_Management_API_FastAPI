# Firebase Firestore Integration Guide

## 🔥 Firebase Credentials Required

### 1. Firebase Service Account JSON File
Download from Firebase Console > Project Settings > Service Accounts > Generate new private key

Required fields in the JSON:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id", 
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project.iam.gserviceaccount.com"
}
```

### 2. Environment Variables Needed

Update your .env file with these Firebase-specific variables:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-service-account.json
# OR use individual fields:
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id

# Firestore Collections (customize as needed)
FIRESTORE_COLLECTION_PLOTS=plots
FIRESTORE_COLLECTION_ZONES=zones  
FIRESTORE_COLLECTION_USERS=users
```

### 3. Firebase Project Setup Steps

1. **Create Firebase Project**:
   - Go to https://console.firebase.google.com/
   - Create new project or select existing
   - Enable Firestore Database

2. **Enable Firestore**:
   - Go to Firestore Database
   - Create database (start in test mode, configure rules later)
   - Choose location (preferably close to your users)

3. **Create Service Account**:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Download JSON file securely

4. **Set Firestore Rules** (for production):
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Only authenticated requests can access
       match /{document=**} {
         allow read, write: if request.auth != null;
       }
     }
   }
   ```

## 📦 Complete Dependencies List

### Production Dependencies:
```pip-requirements
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
PyJWT[cryptography]>=2.8.0
python-multipart>=0.0.6
firebase-admin>=6.2.0
google-cloud-firestore>=2.11.1
google-auth>=2.17.3
google-cloud-core>=2.3.3
httpx>=0.25.0
```

### Development Dependencies:
```pip-requirements
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.7.0
```

## 🏗️ Firestore Collections Structure

### 1. Plots Collection (`plots`)
```javascript
{
  plotId: "GSEZ-R-001",
  plotName: "GSEZ-R-001", 
  plotStatus: "Available", // Available, Allocated, Reserved
  category: "Residential", // Residential, Commercial, Industrial
  phase: 1,
  areaInSqm: 5000.0,
  areaInHa: 0.5,
  zoneCode: "GSEZ",
  country: "Gabon",
  sector: "Housing", // Optional
  activity: "Residential Development", // Optional
  companyName: null, // Optional
  allocatedDate: null, // Date or null
  expiryDate: null, // Date or null  
  investmentAmount: null, // Number or null
  employmentGenerated: null, // Number or null
  createdAt: timestamp,
  updatedAt: timestamp
}
```

### 2. Zones Collection (`zones`)
```javascript
{
  zoneId: "GSEZ",
  country: "Gabon",
  zoneCode: "GSEZ",
  phase: 1,
  landArea: 100.5,
  zoneName: "Gabon Special Economic Zone",
  zoneType: "SEZ", // SEZ, Industrial, Commercial
  establishedDate: "2020-01-01",
  createdAt: timestamp,
  updatedAt: timestamp
}
```

### 3. Users Collection (`users`) 
```javascript
{
  userId: "auto-generated-id",
  email: "user@example.com",
  role: "super_admin", // super_admin, zone_admin, normal_user
  zone: "GSEZ", 
  createdDate: timestamp,
  lastModified: timestamp,
  isActive: true
}
```

## 🔒 Security Considerations

1. **Service Account Security**:
   - Store JSON file securely (not in git)
   - Use environment variables for sensitive data
   - Rotate keys periodically

2. **Firestore Rules**:
   - Implement proper security rules
   - Validate user permissions server-side
   - Use indexed queries for performance

3. **Environment Variables**:
   - Never commit .env files
   - Use different configs for dev/staging/prod
   - Validate all required env vars on startup
