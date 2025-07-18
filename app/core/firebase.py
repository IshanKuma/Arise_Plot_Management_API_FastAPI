"""
Firebase Firestore client initialization and configuration.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcp_firestore
from app.core.config import settings
import os
from typing import Optional


class FirebaseClient:
    """Firebase client singleton for Firestore operations."""
    
    _instance: Optional['FirebaseClient'] = None
    _db: Optional[gcp_firestore.Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._db is None:
            self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK and Firestore client."""
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                # Method 1: Use service account JSON file (recommended)
                if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID
                    })
                
                # Method 2: Use individual environment variables
                elif settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
                    cred_dict = {
                        "type": "service_account",
                        "project_id": settings.FIREBASE_PROJECT_ID,
                        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                        "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                        "client_email": settings.FIREBASE_CLIENT_EMAIL,
                        "client_id": settings.FIREBASE_CLIENT_ID,
                        "auth_uri": settings.FIREBASE_AUTH_URI,
                        "token_uri": settings.FIREBASE_TOKEN_URI,
                        "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
                        "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL
                    }
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                
                # Method 3: Use default credentials (for Cloud environments)
                else:
                    firebase_admin.initialize_app()
            
            # Initialize Firestore client
            self._db = firestore.client()
            print(f"✅ Firebase initialized successfully for project: {settings.FIREBASE_PROJECT_ID}")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {str(e)}")
            raise
    
    @property
    def db(self) -> gcp_firestore.Client:
        """Get Firestore database client."""
        if self._db is None:
            self._initialize_firebase()
        return self._db


# Global Firebase client instance
firebase_client = FirebaseClient()


def get_firestore_db() -> gcp_firestore.Client:
    """Get Firestore database client instance."""
    return firebase_client.db
