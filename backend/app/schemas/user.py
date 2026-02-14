"""Pydantic schemas for user-related models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)
    captcha_token: str = Field(..., min_length=1)


class UserLogin(UserBase):
    """Schema for user login."""

    password: str
    captcha_token: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    """Schema for updating user settings."""

    max_token: str | None = Field(None, min_length=1)
    max_chat_id: int | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    email: str
    max_token_set: bool = Field(default=False, description="Whether max token is set (not the actual token)")
    max_chat_id: int | None = None
    connections_limit: int
    daily_posts_limit: int
    is_email_verified: bool
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class EmailVerifyRequest(BaseModel):
    """Schema for email verification."""

    token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr
    captcha_token: str = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    status: Literal["success", "error", "warning"] = "success"