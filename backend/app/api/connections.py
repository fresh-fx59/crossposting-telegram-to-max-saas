"""Connection management API routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_async_session
from ..database.models import Connection, MaxChannel, TelegramConnection
from ..schemas.connection import (
    ConnectionCreate,
    ConnectionDetailResponse,
    ConnectionResponse,
    ConnectionUpdate,
    MaxChannelCreate,
    MaxChannelResponse,
    MaxChannelUpdate,
    TelegramConnectionCreate,
    TelegramConnectionResponse,
    TelegramConnectionUpdate,
    TestConnectionResponse,
)
from ..schemas.post import PostResponse
from ..services.crypto import decrypt_token, encrypt_token
from ..services.limit_service import (
    cleanup_old_post_counts,
    cleanup_old_posts,
    get_post_history,
    get_remaining_connections,
)
from ..services.max_service import send_test_message
from ..services.telegram_service import (
    delete_webhook,
    get_telegram_bot_info,
    get_webhook_info,
    set_webhook,
)

from .deps import CurrentUser, VerifiedUserOptional

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Telegram Connections ───────────────────────────────────────────


@router.post("/telegram", response_model=TelegramConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_telegram_connection(
    data: TelegramConnectionCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> TelegramConnectionResponse:
    """Create a new Telegram bot connection."""
    bot_info = await get_telegram_bot_info(data.bot_token)

    username = data.telegram_channel_username.lstrip("@")

    try:
        from ..services.telegram_service import get_channel_id_from_username
        channel_id = await get_channel_id_from_username(data.bot_token, username)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get channel info. Make sure the bot is an admin in @{username}: {str(e)}",
        ) from e

    from ..services.telegram_service import generate_webhook_secret
    webhook_secret = generate_webhook_secret()
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhook/telegram/{webhook_secret}"

    encrypted_token = encrypt_token(data.bot_token)

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
    result = await session.execute(
        select(TelegramConnection)
        .where(TelegramConnection.user_id == current_user.id)
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
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == telegram_connection_id,
            TelegramConnection.user_id == current_user.id,
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram connection not found",
        )

    if data.telegram_channel_username is not None:
        tg_connection.telegram_channel_username = data.telegram_channel_username.lstrip("@")
    if data.bot_token is not None:
        tg_connection.bot_token = encrypt_token(data.bot_token)
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
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == telegram_connection_id,
            TelegramConnection.user_id == current_user.id,
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram connection not found",
        )

    bot_token = decrypt_token(tg_connection.bot_token)
    try:
        await delete_webhook(bot_token)
    except Exception as e:
        logger.error("Failed to delete webhook: %s", e)

    await session.delete(tg_connection)
    await session.commit()


# ── Max Channels ───────────────────────────────────────────────────


@router.post("/max", response_model=MaxChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_max_channel(
    data: MaxChannelCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> MaxChannelResponse:
    """Create a new Max channel."""
    encrypted_token = encrypt_token(data.bot_token)

    channel = MaxChannel(
        user_id=current_user.id,
        bot_token=encrypted_token,
        chat_id=data.chat_id,
        name=data.name,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    return MaxChannelResponse(
        id=channel.id,
        chat_id=channel.chat_id,
        name=channel.name,
        bot_token_set=True,
        is_active=channel.is_active,
        created_at=channel.created_at,
    )


@router.get("/max", response_model=list[MaxChannelResponse])
async def list_max_channels(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> list[MaxChannelResponse]:
    """List all Max channels for the current user."""
    result = await session.execute(
        select(MaxChannel)
        .where(MaxChannel.user_id == current_user.id)
        .order_by(MaxChannel.created_at.desc())
    )
    channels = result.scalars().all()

    return [
        MaxChannelResponse(
            id=c.id,
            chat_id=c.chat_id,
            name=c.name,
            bot_token_set=bool(c.bot_token),
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in channels
    ]


@router.put("/max/{max_channel_id}", response_model=MaxChannelResponse)
async def update_max_channel(
    max_channel_id: int,
    data: MaxChannelUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> MaxChannelResponse:
    """Update a Max channel."""
    result = await session.execute(
        select(MaxChannel).where(
            MaxChannel.id == max_channel_id,
            MaxChannel.user_id == current_user.id,
        )
    )
    channel = result.scalar_one_or_none()

    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Max channel not found",
        )

    if data.bot_token is not None:
        channel.bot_token = encrypt_token(data.bot_token)
    if data.chat_id is not None:
        channel.chat_id = data.chat_id
    if data.name is not None:
        channel.name = data.name
    if data.is_active is not None:
        channel.is_active = data.is_active

    await session.commit()
    await session.refresh(channel)

    return MaxChannelResponse(
        id=channel.id,
        chat_id=channel.chat_id,
        name=channel.name,
        bot_token_set=bool(channel.bot_token),
        is_active=channel.is_active,
        created_at=channel.created_at,
    )


@router.delete("/max/{max_channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_max_channel(
    max_channel_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> None:
    """Delete a Max channel."""
    result = await session.execute(
        select(MaxChannel).where(
            MaxChannel.id == max_channel_id,
            MaxChannel.user_id == current_user.id,
        )
    )
    channel = result.scalar_one_or_none()

    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Max channel not found",
        )

    await session.delete(channel)
    await session.commit()


@router.post("/max/{max_channel_id}/test", response_model=TestConnectionResponse)
async def test_max_channel(
    max_channel_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
    test_message: str = "Test message from Telegram Crossposter",
) -> TestConnectionResponse:
    """Send a test message to a Max channel."""
    result = await session.execute(
        select(MaxChannel).where(
            MaxChannel.id == max_channel_id,
            MaxChannel.user_id == current_user.id,
        )
    )
    channel = result.scalar_one_or_none()

    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Max channel not found",
        )

    max_token = decrypt_token(channel.bot_token)

    try:
        await send_test_message(max_token, channel.chat_id, test_message)
        return TestConnectionResponse(success=True, message="Test message sent successfully")
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"Failed: {str(e)}")


# ── Connections (Links: Telegram → Max) ────────────────────────────


def _connection_response(connection: Connection) -> ConnectionResponse:
    """Build ConnectionResponse from a loaded Connection object."""
    return ConnectionResponse(
        id=connection.id,
        telegram_connection_id=connection.telegram_connection_id,
        telegram_channel_id=connection.telegram_connection.telegram_channel_id,
        telegram_channel_username=connection.telegram_connection.telegram_channel_username,
        max_channel_id=connection.max_channel_id,
        max_chat_id=connection.max_channel.chat_id,
        max_channel_name=connection.max_channel.name,
        name=connection.name,
        is_active=connection.is_active,
        created_at=connection.created_at,
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: VerifiedUserOptional,
) -> ConnectionResponse:
    """Create a new link (Telegram channel -> Max channel)."""
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required.",
        )

    remaining = await get_remaining_connections(session, current_user.id)
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Connection limit reached ({settings.MAX_CONNECTIONS_PER_USER}).",
        )

    # Verify Telegram connection belongs to user
    tg_result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.id == data.telegram_connection_id,
            TelegramConnection.user_id == current_user.id,
        )
    )
    if tg_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram connection not found")

    # Verify Max channel belongs to user
    max_result = await session.execute(
        select(MaxChannel).where(
            MaxChannel.id == data.max_channel_id,
            MaxChannel.user_id == current_user.id,
        )
    )
    if max_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Max channel not found")

    connection = Connection(
        user_id=current_user.id,
        telegram_connection_id=data.telegram_connection_id,
        max_channel_id=data.max_channel_id,
        name=data.name,
    )
    session.add(connection)
    await session.commit()

    # Reload with relationships
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.id == connection.id)
    )
    connection = result.scalar_one()

    return _connection_response(connection)


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> list[ConnectionResponse]:
    """List all connections for the current user."""
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.user_id == current_user.id)
        .order_by(Connection.created_at.desc())
    )
    connections = result.scalars().all()

    return [_connection_response(c) for c in connections]


@router.get("/{connection_id}", response_model=ConnectionDetailResponse)
async def get_connection(
    connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConnectionDetailResponse:
    """Get connection details with post history."""
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.id == connection_id, Connection.user_id == current_user.id)
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    offset = (page - 1) * page_size
    posts, total = await get_post_history(session, connection_id, page_size, offset)

    resp = _connection_response(connection)
    return ConnectionDetailResponse(
        **resp.model_dump(),
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
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.id == connection_id, Connection.user_id == current_user.id)
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    if data.max_channel_id is not None:
        # Verify new Max channel belongs to user
        max_result = await session.execute(
            select(MaxChannel).where(
                MaxChannel.id == data.max_channel_id,
                MaxChannel.user_id == current_user.id,
            )
        )
        if max_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Max channel not found")
        connection.max_channel_id = data.max_channel_id
    if data.name is not None:
        connection.name = data.name
    if data.is_active is not None:
        connection.is_active = data.is_active

    await session.commit()

    # Reload with relationships
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.id == connection.id)
    )
    connection = result.scalar_one()

    return _connection_response(connection)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> None:
    """Delete a connection."""
    result = await session.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    await session.delete(connection)
    await session.commit()


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connection_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
    test_message: str = "Test message from Telegram Crossposter",
) -> TestConnectionResponse:
    """Test sending a message to Max via the connection."""
    result = await session.execute(
        select(Connection)
        .options(selectinload(Connection.telegram_connection), selectinload(Connection.max_channel))
        .where(Connection.id == connection_id, Connection.user_id == current_user.id)
    )
    connection = result.scalar_one_or_none()

    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    max_channel = connection.max_channel
    max_token = decrypt_token(max_channel.bot_token)

    try:
        await send_test_message(max_token, max_channel.chat_id, test_message)
        success = True
        message = "Test message sent successfully"
    except Exception as e:
        success = False
        message = f"Failed to send test message: {str(e)}"

    # Get webhook info
    tg_connection = connection.telegram_connection
    webhook_info = None
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


# ── Cleanup ────────────────────────────────────────────────────────


@router.post("/cleanup", response_model=dict[str, int])
async def cleanup_old_data(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUser,
) -> dict[str, int]:
    """Clean up old post history and counters."""
    posts_deleted = await cleanup_old_posts(session)
    counters_deleted = await cleanup_old_post_counts(session)
    await session.commit()

    return {"posts_deleted": posts_deleted, "counters_deleted": counters_deleted}
