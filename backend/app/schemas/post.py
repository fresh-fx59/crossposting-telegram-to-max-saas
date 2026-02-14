"""Pydantic schemas for post-related models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PostBase(BaseModel):
    """Base post schema."""

    content_type: Literal["text", "photo", "unsupported"]
    status: Literal["success", "failed"]


class PostResponse(PostBase):
    """Schema for post response."""

    id: int
    connection_id: int
    telegram_message_id: int | None
    max_message_id: str | None
    error_message: str | None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class PostListResponse(BaseModel):
    """Response with list of posts."""

    posts: list[PostResponse]
    total: int
    page: int
    page_size: int