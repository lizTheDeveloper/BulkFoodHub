"""
Core configuration module for BulkFoodHub.
Handles environment variables and application settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Configuration
    app_name: str = "BulkFoodHub"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # Database Configuration
    database_url: str = "postgresql://annhoward@localhost:5432/bulkfoodhub_dev"
    database_url_test: str = "postgresql://annhoward@localhost:5432/bulkfoodhub_test"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT Configuration
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email Configuration
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@bulkfoodhub.com"
    
    # Payment Configuration
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "bulkfoodhub-images"
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the appropriate database URL based on environment."""
    if settings.is_testing:
        return settings.database_url_test
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL."""
    return settings.redis_url
