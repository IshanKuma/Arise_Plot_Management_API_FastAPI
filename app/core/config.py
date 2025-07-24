"""
Application configuration settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "arise-plot-management-super-secret-key-change-in-production-2025"
    JWT_ALGORITHM: str = "HS256" 
    JWT_EXPIRE_HOURS: int = 24
    
    # Authentication Secret Key (for token generation authorization)
    AUTH_SECRET_KEY: str = "arise-master-auth-secret-2025"
    
    # Firebase Configuration - Using Service Account JSON File
    FIREBASE_PROJECT_ID: str = "arise-ipp"
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    
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
    FIRESTORE_COLLECTION_ZONES: str = "zone-master"
    FIRESTORE_COLLECTION_USERS: str = "admin-access"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
