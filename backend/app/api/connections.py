"""Connection management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_async_session
from ..database.models import Connection, TelegramConnection, User
from ..schemas.connection import (
    ConnectionCreate,
    ConnectionDetailResponse,
    ConnectionResponse,
    TelegramConnectionCreate,
    TelegramConnectionResponse,
    TelegramConnectionUpdate,
    TestConnectionResponse,
)
from ..schemas.post import PostListResponse, PostResponse
from ..services.crypto import decrypt_token, encrypt_token
from ..services.limit_service import (
    can_post_to_connection,
    cleanup_old_post_counts,
    cleanup_old_posts,
    get_remaining_connections,
    get_post_history,
)
from ..services.max_service import send_test_message
from ..services.telegram_service import (
    delete_webhook,
    get_telegram_bot_info,
    get_webhook_info,
    set_webhook,
)

from .deps import CurrentUser, VerifiedUserOptional

router = APIRouter()


# Telegram Connections
@router.post("/telegram", response_model=TelegramConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_telegram_connection(
    data: TelegramConnectionCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> TelegramConnectionResponse:
    """Create a new Telegram bot connection."""
    # Validate bot token with Telegram API
    bot_info = await get_telegram_bot_info(data.bot_token)

    # Get channel ID from username
    channel_id = await get_telegram_bot_info(data.bot_token)
    # For channel posts, we need the channel ID
    # The username is stored for reference
    username = data.telegram_channel_username.lstrip("@")

    try:
        channel_info = await get_telegram_bot_info(data.bot_token)
        # bot_info gives bot's info, we assume channel_id comes from the username
        # In real implementation, would call getChat with username
        channel_id = 100  # Placeholder - would be actual channel ID from getChat
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get channel info: {str(e)}",
        ) from e

    # Generate webhook secret
    from ..services.telegram_service import generate_webhook_secret

    webhook_secret = generate_webhook_secret()
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhook/telegram/{webhook_secret}"

    # Encrypt bot token
    encrypted_token = encrypt_token(data.bot_token)

    # Create Telegram connection
    tg_connection = TelegramConnection(
        user_id=current_user.id,
        telegram_channel_id=channel_id,
        telegram_channel_username=username,
        bot_token=encrypted_token,
        webhook_secret=webhook_secret,
        webhook_url=webhook_url,
    )
    session.add(tg_connection)
    await session.flush()

    # Set up webhook with Telegram
    try:
        await set_webhook(data.bot_token, webhook_url)
        tg_connection.webhook_url = webhook_url
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set webhook: {str(e)}",
        ) from e

    await session.commit()
    await session.refresh(tg_connection)

    return TelegramConnectionResponse(
        id=tg_connection.id,
        telegram_channel_id=tg_connection.telegram_channel_id,
        telegram_channel_username=tg_connection.telegram_channel_username,
        webhook_url=tg_connection.webhook_url,
        is_active=tg_connection.is_active,
        created_at=tg_connection.created_at,
    )


@router.get("/telegram", response_model=list[TelegramConnectionResponse])
async def list_telegram_connections(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> list[TelegramConnectionResponse]:
    """List all Telegram connections for the current user."""

    current_user_obj = current_user

    result = await session.execute(
        select(TelegramConnection)
        .where(TelegramConnection.user_id == current_user_obj.id)
        .order_by(TelegramConnection.created_at.desc())
    )
    connections = result.scalars().all()

    return [
        TelegramConnectionResponse(
            id=c.id,
            telegram_channel_id=c.telegram_channel_id,
            telegram_channel_username=c.telegram_channel_username,
            webhook_url=c.webhook_url,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in connections
    ]


@router.put("/telegram/{telegram_connection_id}", response_model=TelegramConnectionResponse)
async def update_telegram_connection(
    telegram_connection_id: int,
    data: TelegramConnectionUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> TelegramConnectionResponse:
    """Update a Telegram connection."""

    current_user_obj = current_user

    # Find connection
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == telegram_connection_id,
            TelegramConnection.user_id == current_user_obj.id,
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram connection not found",
        )

    # Update fields
    if data.telegram_channel_username is not None:
        tg_connection.telegram_channel_username = data.telegram_channel_username.lstrip("@")
    if data.bot_token is not None:
        encrypted_token = encrypt_token(data.bot_token)
        tg_connection.bot_token = encrypted_token
    if data.is_active is not None:
        tg_connection.is_active = data.is_active

    await session.commit()
    await session.refresh(tg_connection)

    return TelegramConnectionResponse(
        id=tg_connection.id,
        telegram_channel_id=tg_connection.telegram_channel_id,
        telegram_channel_username=tg_connection.telegram_channel_username,
        webhook_url=tg_connection.webhook_url,
        is_active=tg_connection.is_active,
        created_at=tg_connection.created_at,
    )


@router.delete("/telegram/{telegram_connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_telegram_connection(
    telegram_connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> None:
    """Delete a Telegram connection and remove webhook."""

    current_user_obj = current_user

    # Find connection
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == telegram_connection_id,
            TelegramConnection.user_id == current_user_obj.id,
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram connection not found",
        )

    # Decrypt token and delete webhook
    bot_token = decrypt_token(tg_connection.bot_token)
    try:
        await delete_webhook(bot_token)
    except Exception as e:
        logger.error("Failed to delete webhook: %s", e)

    # Delete connection (cascades to Connection, Post, etc.)
    await session.delete(tg_connection)
    await session.commit()


# Connections (Telegram -> Max mappings)
@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, VerifiedUserOptional],
) -> ConnectionResponse:
    """Create a new connection (Telegram channel -> Max chat mapping)."""

    current_user_obj = current_user

    # Check email verification
    if not current_user_obj.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )

    # Check connection limit
    remaining = await get_remaining_connections(session, current_user_obj.id)
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Connection limit reached. Maximum {settings.MAX_CONNECTIONS_PER_USER} connections allowed.",
        )

    # Verify Telegram connection exists and belongs to user
    tg_result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == data.telegram_connection_id,
            TelegramConnection.user_id == current_user_obj.id,
        )
    )
    tg_connection = tg_result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram connection not found",
        )

    # Create connection
    connection = Connection(
        user_id=current_user_obj.id,
        telegram_connection_id=data.telegram_connection_id,
        max_chat_id=data.max_chat_id,
        name=data.name,
    )
    session.add(connection)
    await session.commit()
    await session.refresh(connection)

    return ConnectionResponse(
        id=connection.id,
        telegram_connection_id=connection.telegram_connection_id,
        telegram_channel_id=tg_connection.telegram_channel_id,
        telegram_channel_username=tg_connection.telegram_channel_username,
        max_chat_id=connection.max_chat_id,
        name=connection.name,
        is_active=connection.is_active,
        created_at=connection.created_at,
    )


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> list[ConnectionResponse]:
    """List all connections for the current user."""

    current_user_obj = current_user

    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection))
        .where(Connection.user_id == current_user_obj.id)
        .order_by(Connection.created_at.desc())
    )
    connections = result.scalars().all()

    return [
        ConnectionResponse(
            id=c.id,
            telegram_connection_id=c.telegram_connection_id,
            telegram_channel_id=c.telegram_connection.telegram_channel_id,
            telegram_channel_username=c.telegram_connection.telegram_channel_username,
            max_chat_id=c.max_chat_id,
            name=c.name,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in connections
    ]


@router.get("/{connection_id}", response_model=ConnectionDetailResponse)
async def get_connection(
    connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConnectionDetailResponse:
    """Get connection details with post history."""

    current_user_obj = current_user

    # Find connection
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection))
        .where(
            Connection.id == connection_id,
            Connection.user_id == current_user_obj.id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Get post history
    offset = (page - 1) * page_size
    posts, total = await get_post_history(session, connection_id, page_size, offset)

    return ConnectionDetailResponse(
        id=connection.id,
        telegram_connection_id=connection.telegram_connection_id,
        telegram_channel_id=connection.telegram_connection.telegram_channel_id,
        telegram_channel_username=connection.telegram_connection.telegram_channel_username,
        max_chat_id=connection.max_chat_id,
        name=connection.name,
        is_active=connection.is_active,
        created_at=connection.created_at,
        posts=[
            PostResponse(
                id=p.id,
                connection_id=p.connection_id,
                telegram_message_id=p.telegram_message_id,
                max_message_id=p.max_message_id,
                content_type=p.content_type,
                status=p.status,
                error_message=p.error_message,
                created_at=p.created_at,
            )
            for p in posts
        ],
    )


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    data: ConnectionUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> ConnectionResponse:
    """Update a connection."""

    current_user_obj = current_user

    # Find connection
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection))
        .where(
            Connection.id == connection_id,
            Connection.user_id == current_user_obj.id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Update fields
    if data.max_chat_id is not None:
        connection.max_chat_id = data.max_chat_id
    if data.name is not None:
        connection.name = data.name
    if data.is_active is not None:
        connection.is_active = data.is_active

    await session.commit()
    await session.refresh(connection)

    tg_connection = connection.telegram_connection

    return ConnectionResponse(
        id=connection.id,
        telegram_connection_id=connection.telegram_connection_id,
        telegram_channel_id=tg_connection.telegram_channel_id,
        telegram_channel_username=tg_connection.telegram_channel_username,
        max_chat_id=connection.max_chat_id,
        name=connection.name,
        is_active=connection.is_active,
        created_at=connection.created_at,
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> None:
    """Delete a connection."""

    current_user_obj = current_user

    # Find connection
    result = await session.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.user_id == current_user_obj.id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Delete connection (cascades to Post, DailyPostCount)
    await session.delete(connection)
    await session.commit()


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connection_id: int,
    test_message: str = "Test message from Telegram Crossposter",
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> TestConnectionResponse:
    """Test sending a message to Max via the connection."""

    current_user_obj = current_user

    # Check if Max credentials are set
    if not current_user_obj.max_token or not current_user_obj.max_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max credentials not configured. Please add your Max bot token and chat ID first.",
        )

    # Find connection
    result = await session.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.user_id == current_user_obj.id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Send test message
    max_token = decrypt_token(current_user_obj.max_token)

    try:
        await send_test_message(max_token, connection.max_chat_id, test_message)
        success = True
        message = "Test message sent successfully"
    except Exception as e:
        success = False
        message = f"Failed to send test message: {str(e)}"

    # Get webhook info
    tg_result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == connection.telegram_connection_id
        )
    )
    tg_connection = tg_result.scalar_one_or_none()
    webhook_info = None

    if tg_connection:
        bot_token = decrypt_token(tg_connection.bot_token)
        try:
            webhook_info = await get_webhook_info(bot_token)
        except Exception:
            pass

    return TestConnectionResponse(
        success=success,
        message=message,
        telegram_webhook_info=webhook_info,
    )


# Cleanup endpoint (cron job usage)
@router.post("/cleanup", response_model=dict[str, int])
async def cleanup_old_data(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
    # Only allow admin users - simplified for now
) -> dict[str, int]:
    """Clean up old post history and counters."""

    posts_deleted = await cleanup_old_posts(session)
    counters_deleted = await cleanup_old_post_counts(session)

    await session.commit()

    return {
        "posts_deleted": posts_deleted,
        "counters_deleted": counters_deleted,
    }