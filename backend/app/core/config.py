import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, validator

load_dotenv()

class Settings(BaseModel):
    # Environment variables - use os.getenv() to read from environment
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reports.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    SPREADSHEET_ID: Optional[str] = os.getenv("SPREADSHEET_ID")
    SHEET_NAME: Optional[str] = os.getenv("SHEET_NAME")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "fluid")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "customengineeringreports@gmail.com")
    ADMIN_FULL_NAME: str = os.getenv("ADMIN_FULL_NAME", "Lefa-Molokwe")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@engineeringreports.com")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8501")
    SMTP_TIMEOUT: int = int(os.getenv("SMTP_TIMEOUT", "30"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_NAME: str = "Engineering Report Deck"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

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