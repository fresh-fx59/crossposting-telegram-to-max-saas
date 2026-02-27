"""Application configuration using Pydantic Settings."""

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Telegram Crossposter SaaS"
    APP_VERSION: str = "1.0.1"
    ENV: Literal["development", "production", "test"] = "development"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://crossposter:password@localhost:5432/crossposter"
    )
    POSTGRES_PASSWORD: str = "password"

    # JWT
    JWT_SECRET_KEY: str = Field(min_length=32, default="dev-jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "telegram-crossposter@aiengineerhelper.com"
    SMTP_FROM_NAME: str = "Telegram Crossposter"
    SMTP_USE_TLS: bool = True

    # Email Verification & Reset
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # Cloudflare Turnstile (Captcha)
    CLOUDFLARE_TURNSTILE_SECRET: str = ""
    CLOUDFLARE_TURNSTILE_SITE_KEY: str = ""

    # Token Encryption (for storing bot tokens securely)
    ENCRYPTION_KEY: str = Field(
        min_length=32,
        default="32-byte-encryption-key-change-in-production"
    )

    # User Limits
    MAX_CONNECTIONS_PER_USER: int = 3
    MAX_POSTS_PER_DAY_PER_CONNECTION: int = 100
    POST_HISTORY_RETENTION_DAYS_SUCCESS: int = 30
    POST_HISTORY_RETENTION_DAYS_FAILED: int = 7

    # Frontend URL (for email links)
    FRONTEND_URL: str = "http://localhost:3000"

    # API Base URLs
    TELEGRAM_API_BASE: str = "https://api.telegram.org"
    MAX_API_BASE: str = "https://platform-api.max.ru"

    # Webhook
    WEBHOOK_BASE_URL: str = "http://localhost:8000"

    @field_validator("FRONTEND_URL")
    @classmethod
    def ensure_no_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from frontend URL."""
        return v.rstrip("/")

    @field_validator("WEBHOOK_BASE_URL")
    @classmethod
    def ensure_webhook_no_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from webhook base URL."""
        return v.rstrip("/")


# Global settings instance
settings = Settings()
