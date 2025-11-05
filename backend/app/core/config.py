import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Environment variables
    OPENAI_API_KEY: Optional[str] = None
    DATABASE_URL: str = Field(default="sqlite:///./reports.db")
    SECRET_KEY: str = Field(default="dev-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: Optional[str] = None
    SPREADSHEET_ID: Optional[str] = None
    SHEET_NAME: Optional[str] = None
    ADMIN_USERNAME: str = Field(default="fluid")
    ADMIN_PASSWORD: str = Field(default="")
    ADMIN_EMAIL: str = Field(default="customengineeringreports@gmail.com")
    ADMIN_FULL_NAME: str = Field(default="Lefa-Molokwe")
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@engineeringreports.com")
    BASE_URL: str = Field(default="http://localhost:8501")
    SMTP_TIMEOUT: int = Field(default=30)
    ENVIRONMENT: str = Field(default="development")
    APP_NAME: str = Field(default="Engineering Report Deck")
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=3600)

    # CORS
    allowed_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8501"])

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }

    @field_validator('SECRET_KEY')
    @classmethod
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

    @field_validator('ADMIN_PASSWORD')
    @classmethod
    def validate_admin_password(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("ADMIN_PASSWORD must be set in production")
        return v

    @field_validator('allowed_origins', mode='before')
    @classmethod
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