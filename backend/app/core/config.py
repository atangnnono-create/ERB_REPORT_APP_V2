import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Environment variables (Pydantic will auto-load these from .env)
    OPENAI_API_KEY: Optional[str] = None
    DATABASE_URL: str = "DATABASE_URL"
    SECRET_KEY: str = "SECRET_KEY"
    ALGORITHM: str = "ALGORITHM"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = "ACCESS_TOKEN_EXPIRE_MINUTES"
    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: Optional[str] = None
    SPREADSHEET_ID: Optional[str] = None
    SHEET_NAME: Optional[str] = None
    ADMIN_USERNAME: str = "ADMIN_USERNAME"
    ADMIN_PASSWORD: str = "ADMIN_PASSWORD"
    ADMIN_EMAIL: str = "ADMIN_EMAIL"
    ADMIN_FULL_NAME: str = "ADMIN_FULL_NAME"
    SMTP_SERVER: str = "SMTP_SERVER"
    SMTP_PORT: int = "SMTP_PORT"
    SMTP_USERNAME: str = "SMTP_USERNAME"
    SMTP_PASSWORD: str = "SMTP_PASSWORD"
    FROM_EMAIL: str = "noreply@engineeringreports.com"
    BASE_URL: str = "BASE_URL"
    SMTP_TIMEOUT: int = 30
    ENVIRONMENT: str = "ENVIRONMENT"
    APP_NAME: str = "Engineering Report Deck"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600

    # CORS - this needs special handling
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    # Pydantic V2 config
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or ["http://localhost:3000", "http://localhost:8501"]

    @field_validator('SECRET_KEY', mode='after')
    @classmethod
    def validate_secret_key(cls, v):
        default_key = "4f439ce8d87aff8d7f4af5096cf132cb90b79a04f6af7e2f7612983942bd0fae"
        if not v or v == default_key:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError(
                    "SECRET_KEY must be set in production environment. "
                    "Generate a secure key with: openssl rand -hex 32"
                )
            print("⚠️  WARNING: Using default secret key - not suitable for production")
        elif len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator('OPENAI_API_KEY', mode='after')
    @classmethod
    def validate_openai_key(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            print("⚠️  WARNING: OPENAI_API_KEY not set - AI features will be disabled")
        return v

    @field_validator('DATABASE_URL', mode='after')
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if "sqlite" not in v and "postgresql" not in v:
            raise ValueError("DATABASE_URL must be a SQLite or PostgreSQL connection string")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# Create global settings instance
settings = Settings()