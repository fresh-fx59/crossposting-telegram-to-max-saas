"""Telegram webhook endpoint for receiving channel posts."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..database.models import Connection, Post, TelegramConnection
from ..services.limit_service import can_post_to_connection, increment_post_count
from ..services.max_service import MaxServiceError, forward_channel_post_to_max

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/telegram/{webhook_secret}", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    webhook_secret: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Handle incoming Telegram webhook updates.

    Processes channel posts and forwards them to connected Max chats.

    Args:
        webhook_secret: The webhook secret for the Telegram connection
        request: FastAPI request object
        session: Database session

    Returns:
        Success response
    """
    # Get update body
    try:
        update = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook body: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON") from e

    # Find Telegram connection by webhook secret
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.webhook_secret == webhook_secret,
            TelegramConnection.is_active.is_(True),
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        logger.warning("Webhook received with invalid secret: %s", webhook_secret)
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check if this is a channel_post update
    channel_post = update.get("channel_post")
    if not channel_post:
        logger.debug("Non-channel-post update received, ignoring")
        return {"status": "ignored", "reason": "not a channel post"}

    # Get channel ID from post
    telegram_channel_id = channel_post.get("chat", {}).get("id")
    if telegram_channel_id != tg_connection.telegram_channel_id:
        logger.warning(
            "Channel post from channel %d but expected %d",
            telegram_channel_id,
            tg_connection.telegram_channel_id,
        )
        return {"status": "ignored", "reason": "channel mismatch"}

    # Find all active connections for this Telegram connection
    result = await session.execute(
        select(Connection)
        .where(
            Connection.telegram_connection_id == tg_connection.id,
            Connection.is_active.is_(True),
        )
    )
    connections = result.scalars().all()

    if not connections:
        logger.info("No active connections for Telegram channel %d", telegram_channel_id)
        return {"status": "ok", "processed": 0}

    # Process each connection
    processed = 0
    for connection in connections:
        # Check daily limit
        can_post, remaining = await can_post_to_connection(session, connection.id)

        if not can_post:
            logger.warning(
                "Daily limit exceeded for connection %d (remaining: %d), skipping",
                connection.id,
                remaining,
            )
            # Log skipped post
            await _create_post_record(
                session,
                connection.id,
                channel_post.get("message_id"),
                None,
                _get_content_type(channel_post),
                "failed",
                f"Daily limit exceeded (remaining: {remaining})",
            )
            continue

        # Forward to Max
        try:
            max_message_id, error_message = await forward_channel_post_to_max(
                session, connection, channel_post
            )

            if error_message or max_message_id is None:
                # Failed
                await _create_post_record(
                    session,
                    connection.id,
                    channel_post.get("message_id"),
                    None,
                    _get_content_type(channel_post),
                    "failed",
                    error_message,
                )
                logger.error(
                    "Failed to forward post for connection %d: %s",
                    connection.id,
                    error_message,
                )
            else:
                # Success
                await _create_post_record(
                    session,
                    connection.id,
                    channel_post.get("message_id"),
                    max_message_id,
                    _get_content_type(channel_post),
                    "success",
                    None,
                )
                await increment_post_count(session, connection.id)
                processed += 1
                logger.info(
                    "Successfully forwarded post to Max for connection %d",
                    connection.id,
                )

        except Exception as e:
            logger.exception(
                "Error processing webhook for connection %d: %s", connection.id, e
            )
            await _create_post_record(
                session,
                connection.id,
                channel_post.get("message_id"),
                None,
                _get_content_type(channel_post),
                "failed",
                f"Unexpected error: {str(e)}",
            )

    await session.commit()

    return {
        "status": "ok",
        "processed": processed,
        "total": len(connections),
    }


@router.get("/telegram/{webhook_secret}/health", status_code=status.HTTP_200_OK)
async def telegram_webhook_health(
    webhook_secret: str,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Health check endpoint for webhooks.

    Useful for verifying that webhook URLs are accessible.
    """
    result = await session.execute(
        select(TelegramConnection).where(
            TelegramConnection.webhook_secret == webhook_secret
        )
    )
    tg_connection = result.scalar_one_or_none()

    if tg_connection is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "status": "healthy",
        "telegram_channel_id": str(tg_connection.telegram_channel_id),
        "is_active": "true" if tg_connection.is_active else "false",
    }


def _get_content_type(channel_post: dict) -> str:
    """Determine content type from Telegram channel post.

    Args:
        channel_post: Telegram channel post data

    Returns:
        Content type string
    """
    if channel_post.get("photo"):
        return "photo"
    elif channel_post.get("text"):
        return "text"
    elif channel_post.get("video"):
        return "video"
    elif channel_post.get("audio"):
        return "audio"
    elif channel_post.get("document"):
        return "document"
    else:
        return "unsupported"


async def _create_post_record(
    session: AsyncSession,
    connection_id: int,
    telegram_message_id: int | None,
    max_message_id: str | None,
    content_type: str,
    post_status: str,
    error_message: str | None,
) -> Post:
    """Create a post record in the database.

    Args:
        session: Database session
        connection_id: Connection ID
        telegram_message_id: Telegram message ID
        max_message_id: Max message ID
        content_type: Content type
        post_status: Post status (success/failed)
        error_message: Error message if failed

    Returns:
        Created Post object
    """
    post = Post(
        connection_id=connection_id,
        telegram_message_id=telegram_message_id,
        max_message_id=max_message_id,
        content_type=content_type,
        status=post_status,
        error_message=error_message,
    )
    session.add(post)
    await session.flush()
    return post