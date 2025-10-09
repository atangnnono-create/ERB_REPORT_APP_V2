import os
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: str
    SPREADSHEET_ID: str
    SHEET_NAME: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    BASE_URL: str
    SMTP_TIMEOUT: int
    ENVIRONMENT: str
    REDIS_URL: str

    class Config:
        env_file = ".env"
        extra = "allow"



    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./reports.db")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.ethereal.email")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_timeout: int = int(os.getenv("SMTP_TIMEOUT", "30"))
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    app_name: str = os.getenv("APP_NAME", "Engineering Report Deck")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@engineeringreports.com")

    # OpenAI
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    # CORS
    allowed_origins: List[str] = []

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

    # Admin
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@engineeringreports.com")

    @validator('allowed_origins', pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or ["http://localhost:3000", "http://localhost:8501"]

    @validator('secret_key')
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

    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            print("⚠️  WARNING: OPENAI_API_KEY not set - AI features will be disabled")
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if "sqlite" not in v and "postgresql" not in v:
            raise ValueError("DATABASE_URL must be a SQLite or PostgreSQL connection string")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    class Config:
        case_sensitive = True
        env_file = ".env"


# Create global settings instance
settings = Settings()