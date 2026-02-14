"""User management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..database.models import User
from ..schemas.auth import UserResponse
from ..schemas.user import MessageResponse, UserUpdate
from ..services.crypto import encrypt_optional_token
from ..services.max_service import send_test_message

router = APIRouter()


@router.put("/me", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends("deps:get_current_user")],
) -> UserResponse:
    """Update current user's settings (Max credentials)."""
    from ..api.deps import get_current_user

    current_user_obj = await current_user

    # Encrypted Max token
    encrypted_token = encrypt_optional_token(user_data.max_token)

    # Update user
    current_user_obj.max_token = encrypted_token
    if user_data.max_chat_id is not None:
        current_user_obj.max_chat_id = user_data.max_chat_id

    await session.commit()
    await session.refresh(current_user_obj)

    return UserResponse(
        id=current_user_obj.id,
        email=current_user_obj.email,
        max_token_set=bool(current_user_obj.max_token),
        max_chat_id=current_user_obj.max_chat_id,
        connections_limit=current_user_obj.connections_limit,
        daily_posts_limit=current_user_obj.daily_posts_limit,
        is_email_verified=current_user_obj.is_email_verified,
        created_at=current_user_obj.created_at,
    )


@router.post("/me/test-max", response_model=MessageResponse)
async def test_max_connection(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends("deps:get_current_user")],
    test_message: str = "Test message from Telegram Crossposter",
) -> MessageResponse:
    """Send a test message to verify Max credentials work."""
    from ..api.deps import get_current_user
    from ..services.crypto import decrypt_token

    current_user_obj = await current_user

    if not current_user_obj.max_token or not current_user_obj.max_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max credentials not configured",
        )

    max_token = decrypt_token(current_user_obj.max_token)

    try:
        await send_test_message(max_token, current_user_obj.max_chat_id, test_message)
        await session.refresh(current_user_obj)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}",
        ) from e

    return MessageResponse(message="Test message sent successfully")