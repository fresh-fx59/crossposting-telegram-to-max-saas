"""Pydantic schemas for connection-related models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class TelegramConnectionCreate(BaseModel):
    """Schema for creating a Telegram connection."""

    telegram_channel_username: str = Field(..., min_length=1, max_length=255)
    bot_token: str = Field(..., min_length=1)


class TelegramConnectionUpdate(BaseModel):
    """Schema for updating a Telegram connection."""

    telegram_channel_username: str | None = Field(None, min_length=1, max_length=255)
    bot_token: str | None = Field(None, min_length=1)
    is_active: bool | None = None


class TelegramConnectionResponse(BaseModel):
    """Schema for Telegram connection response."""

    id: int
    telegram_channel_id: int
    telegram_channel_username: str | None
    webhook_url: str | None
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConnectionCreate(BaseModel):
    """Schema for creating a connection."""

    telegram_connection_id: int = Field(..., gt=0)
    max_chat_id: int = Field(..., gt=0)
    name: str | None = Field(None, min_length=1, max_length=255)


class ConnectionUpdate(BaseModel):
    """Schema for updating a connection."""

    max_chat_id: int | None = Field(None, gt=0)
    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None


class ConnectionResponse(BaseModel):
    """Schema for connection response."""

    id: int
    telegram_connection_id: int
    telegram_channel_id: int
    telegram_channel_username: str | None
    max_chat_id: int
    name: str | None
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConnectionDetailResponse(ConnectionResponse):
    """Detailed connection response with post history."""

    posts: list["PostResponse"] = []


class TestConnectionRequest(BaseModel):
    """Schema for testing a connection."""

    test_message: str = Field(default="Test message from Telegram Crossposter", min_length=1)


class TestConnectionResponse(BaseModel):
    """Response for connection test."""

    success: bool
    message: str
    telegram_webhook_info: dict | None = None