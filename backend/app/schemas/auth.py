"""Pydantic schemas for authentication."""

from typing import Literal

from pydantic import BaseModel

# Re-export from user module for convenience
from .user import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "EmailVerifyRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "TokenResponse",
]


class CaptchaValidateRequest(BaseModel):
    """Schema for captcha validation."""

    token: str
    remote_ip: str | None = None


class CaptchaValidateResponse(BaseModel):
    """Response for captcha validation."""

    success: bool
    message: str | None = None
    error_codes: list[str] | None = None
    status: Literal["success", "error"] = "success"