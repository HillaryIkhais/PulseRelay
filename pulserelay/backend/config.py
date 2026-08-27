"""Configuration for cloud deployment."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    # GCP Project
    GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "pulserelay-506715")
    
    # Firestore
    FIRESTORE_DATABASE: str = os.environ.get("FIRESTORE_DATABASE", "(default)")
    
    # Pub/Sub
    PUBSUB_TOPIC: str = os.environ.get("PUBSUB_TOPIC", "pulse-observations")
    PUBSUB_SUBSCRIPTION: str = os.environ.get("PUBSUB_SUBSCRIPTION", "pulse-observations-sub")
    
    # Gemini
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    
    # Server
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8080"))
    
    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    
    @classmethod
    def is_cloud(cls) -> bool:
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def get_store(cls):
        if cls.is_cloud():
            from ..state.firestore_store import FirestorePatientStateStore
            return FirestorePatientStateStore(project_id=cls.GCP_PROJECT_ID)
        else:
            from ..state.store import PatientStateStore
            return PatientStateStore()
