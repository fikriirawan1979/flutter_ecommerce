"""
Hardened Application Configuration
Production-ready with security best practices
"""

import os
from typing import List, Optional
from functools import lru_cache

class Settings:
    """Production-hardened settings"""
    
    # Application
    APP_NAME: str = "DentalClinicOS API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security - CRITICAL: Never use default values in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    if ENVIRONMENT == "production" and (not SECRET_KEY or len(SECRET_KEY) < 32):
        raise ValueError("SECRET_KEY must be at least 32 characters in production")
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://dental_user:dental_pass@localhost:5432/dental_clinic"
    )
    
    # Redis (for caching, sessions, rate limiting)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # CORS - RESTRICTIVE in production
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:64298"
    ).split(",")
    
    if ENVIRONMENT == "production":
        # Remove localhost in production
        ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if "localhost" not in o]
    
    # File Storage (MinIO/S3)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "dental-clinic-uploads")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    UPLOAD_MAX_SIZE: int = int(os.getenv("UPLOAD_MAX_SIZE", "10485760"))  # 10MB
    UPLOAD_ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    if ENVIRONMENT == "production" and not STRIPE_SECRET_KEY.startswith("sk_live_"):
        raise ValueError("Production must use Stripe live keys")
    
    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    
    # AI Service
    AI_MODEL_PATH: str = os.getenv("AI_MODEL_PATH", "/app/models")
    AI_MAX_CONCURRENT_JOBS: int = int(os.getenv("AI_MAX_CONCURRENT_JOBS", "5"))
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    def validate(self) -> List[str]:
        """Validate all required settings"""
        errors = []
        
        required_production = [
            ("SECRET_KEY", self.SECRET_KEY),
            ("DATABASE_URL", self.DATABASE_URL),
            ("STRIPE_SECRET_KEY", self.STRIPE_SECRET_KEY),
            ("STRIPE_WEBHOOK_SECRET", self.STRIPE_WEBHOOK_SECRET),
        ]
        
        if self.is_production:
            for name, value in required_production:
                if not value:
                    errors.append(f"{name} is required in production")
        
        return errors

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    errors = settings.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    return settings

settings = get_settings()

# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "DEBUG": True,
    "LOG_LEVEL": "DEBUG",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
}

PRODUCTION_CONFIG = {
    "DEBUG": False,
    "LOG_LEVEL": "WARNING",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
    "RATE_LIMIT_REQUESTS": 60,
}