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
                # Use service account JSON file (primary method)
                if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    print(f"🔥 Initializing Firebase with service account: {settings.FIREBASE_CREDENTIALS_PATH}")
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                else:
                    print(f"❌ Firebase service account file not found at: {settings.FIREBASE_CREDENTIALS_PATH}")
                    raise Exception(f"Firebase service account file not found at: {settings.FIREBASE_CREDENTIALS_PATH}")
            
            # Initialize Firestore client
            self._db = firestore.client()
            print(f"✅ Firebase initialized successfully for project: {settings.FIREBASE_PROJECT_ID}")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Credentials path: {settings.FIREBASE_CREDENTIALS_PATH}")
            print(f"File exists: {os.path.exists(settings.FIREBASE_CREDENTIALS_PATH)}")
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
