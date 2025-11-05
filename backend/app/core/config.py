import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, validator

load_dotenv()


class Settings(BaseModel):
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

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        default_key = "dev-key-change-in-production"
        if not v or v == default_key:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError(
                    "SECRET_KEY must be set in production. Generate with: openssl rand -hex 32"
                )
            print("⚠️  WARNING: Using default secret key - not suitable for production")
        elif len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @validator('ADMIN_PASSWORD')
    def validate_admin_password(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("ADMIN_PASSWORD must be set in production")
        return v

    @validator('allowed_origins', pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v or []

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# Create global settings instance
settings = Settings()