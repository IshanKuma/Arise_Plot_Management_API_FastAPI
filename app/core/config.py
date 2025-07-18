"""
Application configuration settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256" 
    JWT_EXPIRE_HOURS: int = 24
    
    # Authentication Secret Key (for token generation authorization)
    AUTH_SECRET_KEY: str = "arise-master-auth-secret-2025"
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"
    FIREBASE_CREDENTIALS_PATH: str = "/home/user/Desktop/arise_fastapi/credentials/firebase-service-account.json"
    FIREBASE_PRIVATE_KEY_ID: str = "your-private-key-id"
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    FIREBASE_CLIENT_X509_CERT_URL: str = ""
    
    # Application Settings
    APP_NAME: str = "Arise Plot Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Arise FastAPI Backend"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:3001"
    ]
    
    # Database Settings
    DATABASE_URL: str = "firestore"
    FIRESTORE_COLLECTION_PLOTS: str = "plots"
    FIRESTORE_COLLECTION_ZONES: str = "zones"
    FIRESTORE_COLLECTION_USERS: str = "users"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
