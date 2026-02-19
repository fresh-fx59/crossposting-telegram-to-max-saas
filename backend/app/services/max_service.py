"""Max API service for sending messages.

Reuses logic from original bot.py.
"""

import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import Connection
from ..services.limit_service import increment_post_count

logger = logging.getLogger(__name__)


class MaxServiceError(Exception):
    """Exception raised when Max API operations fail."""

    pass


async def send_max_text(
    token: str,
    chat_id: int,
    text: str,
) -> dict[str, Any]:
    """Send a text message to Max chat.

    Args:
        token: Max bot API token
        chat_id: Max chat ID
        text: Message text

    Returns:
        Response data from Max API

    Raises:
        MaxServiceError: If the API call fails
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers={"Authorization": token},
                json={"text": text},
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Sent text to Max chat %s: %s", chat_id, result)
            return result
    except httpx.HTTPError as e:
        logger.error("Failed to send text to Max: %s", e)
        raise MaxServiceError(f"Failed to send text to Max: {e}") from e


async def upload_max_photo(
    token: str,
    chat_id: int,
    photo_bytes: bytes,
) -> dict[str, Any]:
    """Upload a photo to Max.

    Args:
        token: Max bot API token
        chat_id: Max chat ID
        photo_bytes: Photo file bytes

    Returns:
        Upload response from Max API

    Raises:
        MaxServiceError: If the upload fails
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.MAX_API_BASE}/uploads",
                params={"chat_id": chat_id, "type": "photo"},
                content=photo_bytes,
                headers={
                    "Authorization": token,
                    "Content-Type": "image/jpeg",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Uploaded photo to Max chat %s: %s", chat_id, result)
            return result
    except httpx.HTTPError as e:
        logger.error("Failed to upload photo to Max: %s", e)
        raise MaxServiceError(f"Failed to upload photo to Max: {e}") from e


async def send_max_photo(
    token: str,
    chat_id: int,
    upload_result: dict[str, Any],
    caption: str | None = None,
) -> dict[str, Any]:
    """Send a message with an uploaded photo attachment to Max.

    Args:
        token: Max bot API token
        chat_id: Max chat ID
        upload_result: Result from upload_max_photo
        caption: Optional caption text

    Returns:
        Response data from Max API

    Raises:
        MaxServiceError: If the API call fails
    """
    try:
        body: dict[str, Any] = {
            "attachments": [
                {
                    "type": "image",
                    "payload": upload_result,
                }
            ],
        }
        if caption:
            body["text"] = caption

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers={"Authorization": token},
                json=body,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Sent photo to Max chat %s: %s", chat_id, result)
            return result
    except httpx.HTTPError as e:
        logger.error("Failed to send photo to Max: %s", e)
        raise MaxServiceError(f"Failed to send photo to Max: {e}") from e


async def forward_channel_post_to_max(
    session: AsyncSession,
    connection: Connection,
    post_data: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Forward a Telegram channel post to Max.

    Args:
        session: Database session
        connection: Connection object
        post_data: Telegram channel post data

    Returns:
        Tuple of (max_message_id, error_message)
    """
    # Get Max token from user
    from ..services.crypto import decrypt_token

    user = connection.user
    max_token = decrypt_token(user.max_token or "")
    max_chat_id = connection.max_chat_id

    if not max_token or not max_chat_id:
        error = "Max credentials not configured"
        logger.error(error)
        return None, error

    content_type = "unsupported"
    max_message_id = None
    error_message = None

    try:
        # Check if channel_post has photo
        if post_data.get("photo"):
            content_type = "photo"
            photo_list = post_data["photo"]
            # Get the largest photo
            photo = photo_list[-1]
            file_id = photo["file_id"]
            caption = post_data.get("caption")

            # Note: In production, we would need to download the photo
            # from Telegram's file_url. For now, we'll add a placeholder
            # that indicates this needs the Telegram client file download.
            # The webhook handler will handle the actual download.

            # This is a simplified version - the actual implementation
            # would need file downloading from Telegram
            logger.warning(
                "Photo forwarding not fully implemented without Telegram file URL"
            )
            error_message = "Photo forwarding requires Telegram file download"
            return None, error_message

        # Check if channel_post has text
        elif post_data.get("text"):
            content_type = "text"
            result = await send_max_text(max_token, max_chat_id, post_data["text"])
            max_message_id = str(result.get("message_id", ""))

        else:
            error_message = f"Unsupported content type: {list(post_data.keys())}"
            logger.warning(error_message)

    except MaxServiceError as e:
        error_message = str(e)
        logger.error("Failed to forward post to Max: %s", e)

    return max_message_id, error_message


async def send_test_message(
    max_token: str,
    max_chat_id: int,
    test_message: str,
) -> dict[str, Any]:
    """Send a test message to Max.

    Args:
        max_token: Max bot API token
        max_chat_id: Max chat ID
        test_message: Test message text

    Returns:
        Response from Max API
    """
    return await send_max_text(max_token, max_chat_id, test_message)