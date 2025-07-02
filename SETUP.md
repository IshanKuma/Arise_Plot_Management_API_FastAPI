# Arise FastAPI Project Setup Commands

## 1. Virtual Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Activate virtual environment (Windows)
# venv\Scripts\activate

# Check if venv is activated
echo $VIRTUAL_ENV
which python

# Deactivate virtual environment
deactivate

# Purpose: Isolates project dependencies from system Python packages
```

## 2. Install Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes production)
pip install -r requirements-dev.txt

# Purpose: Installs all required packages for the FastAPI application
```

## 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Purpose: Sets up environment variables for configuration
```

## 4. Firebase Setup
```bash
# Create Firebase service account key directory
mkdir -p app/config/firebase

# Purpose: Stores Firebase service account credentials securely
```

## 5. Development Server
```bash
# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Purpose: Starts FastAPI development server with auto-reload
```

## 6. Code Quality Tools
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Purpose: Maintains code quality and consistency
```

## 7. Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Purpose: Ensures code functionality and reliability
```

## 8. Database Operations
```bash
# Initialize Firestore (done programmatically)
# No migrations needed for NoSQL

# Purpose: Firestore is schema-less, no migration setup required
```

## Dependencies Explanation

### Core Framework
- **fastapi**: Modern, fast web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI applications
- **pydantic**: Data validation and serialization

### Authentication & Security
- **python-jose**: JWT token creation and validation
- **passlib**: Password hashing utilities
- **python-multipart**: Handle form data and file uploads

### Database
- **firebase-admin**: Official Firebase Admin SDK
- **google-cloud-firestore**: Direct Firestore client library

### Development
- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Code linting
- **isort**: Import sorting

### Configuration
- **python-dotenv**: Environment variable management
- **pydantic-settings**: Settings management

### Production
- **gunicorn**: Production WSGI server
- **structlog**: Structured logging
