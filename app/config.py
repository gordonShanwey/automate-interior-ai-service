"""Configuration settings for the Interior AI Service."""

from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Application settings
    app_name: str = Field(default="Interior AI Service", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Google Cloud settings
    google_cloud_project: str = Field(..., description="Google Cloud Project ID")
    google_application_credentials: Optional[str] = Field(
        default=None, 
        description="Path to Google Cloud service account key file"
    )
    
    # Vertex AI / Gen AI settings
    vertex_ai_location: str = Field(default="us-central1", description="Vertex AI location")
    genai_model: str = Field(default="gemini-1.5-pro", description="Google Gen AI model to use")
    
    # Pub/Sub settings
    pubsub_topic: str = Field(default="client-form-data", description="Pub/Sub topic name")
    pubsub_subscription: str = Field(default="client-form-processor", description="Pub/Sub subscription name")
    pubsub_push_endpoint: Optional[str] = Field(
        default=None, 
        description="Pub/Sub push endpoint URL (auto-generated for Cloud Run)"
    )
    
    # Email settings
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    designer_email: str = Field(..., description="Interior designer email address")
    
    # Cloud Run settings
    cloud_run_service_name: str = Field(default="interior-ai-service", description="Cloud Run service name")
    cloud_run_region: str = Field(default="us-central1", description="Cloud Run region")
    cloud_run_url: Optional[str] = Field(default=None, description="Cloud Run service URL")
    
    # Health check settings
    health_check_timeout: int = Field(default=30, description="Health check timeout in seconds")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")
    
    # Processing settings
    max_retry_attempts: int = Field(default=3, description="Maximum retry attempts for failed operations")
    retry_delay_seconds: int = Field(default=5, description="Delay between retry attempts")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level value."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        """Validate SMTP port value."""
        if not (1 <= v <= 65535):
            raise ValueError("SMTP port must be between 1 and 65535")
        return v
    
    @field_validator("health_check_timeout", "health_check_interval")
    @classmethod
    def validate_positive_integer(cls, v: int) -> int:
        """Validate that integer values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @field_validator("max_retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts value."""
        if not (0 <= v <= 10):
            raise ValueError("Max retry attempts must be between 0 and 10")
        return v
    
    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Convenience function for getting settings
def get_config() -> Settings:
    """Get application configuration."""
    return get_settings()


# Environment-specific configuration helpers
def is_development() -> bool:
    """Check if running in development environment."""
    return get_settings().environment == "development"


def is_production() -> bool:
    """Check if running in production environment."""
    return get_settings().environment == "production"


def is_staging() -> bool:
    """Check if running in staging environment."""
    return get_settings().environment == "staging"


def get_log_level() -> str:
    """Get configured log level."""
    return get_settings().log_level


def get_google_cloud_project() -> str:
    """Get Google Cloud Project ID."""
    return get_settings().google_cloud_project


def get_vertex_ai_location() -> str:
    """Get Vertex AI location."""
    return get_settings().vertex_ai_location


def get_genai_model() -> str:
    """Get Gen AI model name."""
    return get_settings().genai_model


def get_pubsub_topic() -> str:
    """Get Pub/Sub topic name."""
    return get_settings().pubsub_topic


def get_pubsub_subscription() -> str:
    """Get Pub/Sub subscription name."""
    return get_settings().pubsub_subscription


def get_smtp_config() -> dict:
    """Get SMTP configuration."""
    settings = get_settings()
    return {
        "server": settings.smtp_server,
        "port": settings.smtp_port,
        "username": settings.smtp_username,
        "password": settings.smtp_password,
        "use_tls": settings.smtp_use_tls,
    }


def get_designer_email() -> str:
    """Get interior designer email address."""
    return get_settings().designer_email


# Configuration validation
def validate_configuration() -> bool:
    """Validate that all required configuration is present."""
    try:
        settings = get_settings()
        
        # Check required fields
        required_fields = [
            "google_cloud_project",
            "smtp_username", 
            "smtp_password",
            "designer_email"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(settings, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration...")
    if validate_configuration():
        settings = get_settings()
        print(f"Environment: {settings.environment}")
        print(f"Google Cloud Project: {settings.google_cloud_project}")
        print(f"Vertex AI Location: {settings.vertex_ai_location}")
        print(f"Pub/Sub Topic: {settings.pubsub_topic}")
        print(f"SMTP Server: {settings.smtp_server}")
        print(f"Designer Email: {settings.designer_email}")
    else:
        print("Configuration validation failed!")
        exit(1)
