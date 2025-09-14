import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    # WHILSEYE API Configuration
    whilseye_api_url: str = os.getenv("WHILSEYE_API_URL", "https://api.whilseye.com/v1")
    whilseye_username: str = os.getenv("WHILSEYE_USERNAME", "")
    whilseye_password: str = os.getenv("WHILSEYE_PASSWORD", "")
    whilseye_api_key: str = os.getenv("WHILSEYE_API_KEY", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fleet_management")
    
    # Geofence Configuration
    geofence_lat: float = float(os.getenv("GEOFENCE_LAT", "40.7128"))
    geofence_lng: float = float(os.getenv("GEOFENCE_LNG", "-74.0060"))
    geofence_radius: float = float(os.getenv("GEOFENCE_RADIUS", "100"))
    
    # Firebase Configuration
    fcm_service_account_key: str = os.getenv("FCM_SERVICE_ACCOUNT_KEY", "")
    fcm_project_id: str = os.getenv("FCM_PROJECT_ID", "")
    
    # Slack Configuration
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # Application Settings
    polling_interval: int = int(os.getenv("POLLING_INTERVAL", "30"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    class Config:
        env_file = ".env"


settings = Settings()
