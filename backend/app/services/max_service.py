"""Max API service for sending messages.

All Max API calls go through MaxClient, which handles authentication
and base URL in a single place.
"""

import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import Connection

logger = logging.getLogger(__name__)


class MaxServiceError(Exception):
    """Exception raised when Max API operations fail."""

    pass


class MaxClient:
    """HTTP client for Max Bot API. Centralizes auth and base URL."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.MAX_API_BASE

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        content: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Max API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g. "/messages")
            params: Query parameters
            json: JSON body
            content: Raw body bytes
            extra_headers: Additional headers (merged with auth header)

        Returns:
            Parsed JSON response

        Raises:
            MaxServiceError: If the request fails
        """
        headers = {"Authorization": self.token}
        if extra_headers:
            headers.update(extra_headers)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=params,
                    json=json,
                    content=content,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("Max API error [%s %s]: %s", method, path, e)
            raise MaxServiceError(f"Max API error: {e}") from e

    async def send_text(self, chat_id: int, text: str) -> dict[str, Any]:
        """Send a text message to a Max chat."""
        result = await self.request(
            "POST",
            "/messages",
            params={"chat_id": chat_id},
            json={"text": text},
        )
        logger.info("Sent text to Max chat %s: %s", chat_id, result)
        return result

    async def upload_photo(self, chat_id: int, photo_bytes: bytes) -> dict[str, Any]:
        """Upload a photo to Max."""
        result = await self.request(
            "POST",
            "/uploads",
            params={"chat_id": chat_id, "type": "photo"},
            content=photo_bytes,
            extra_headers={"Content-Type": "image/jpeg"},
        )
        logger.info("Uploaded photo to Max chat %s: %s", chat_id, result)
        return result

    async def send_photo(
        self, chat_id: int, upload_result: dict[str, Any], caption: str | None = None
    ) -> dict[str, Any]:
        """Send a message with an uploaded photo attachment."""
        body: dict[str, Any] = {
            "attachments": [{"type": "image", "payload": upload_result}],
        }
        if caption:
            body["text"] = caption

        result = await self.request(
            "POST",
            "/messages",
            params={"chat_id": chat_id},
            json=body,
        )
        logger.info("Sent photo to Max chat %s: %s", chat_id, result)
        return result


async def send_test_message(
    max_token: str,
    max_chat_id: int,
    test_message: str,
) -> dict[str, Any]:
    """Send a test message to Max."""
    return await MaxClient(max_token).send_text(max_chat_id, test_message)


async def forward_channel_post_to_max(
    session: AsyncSession,
    connection: Connection,
    post_data: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Forward a Telegram channel post to Max.

    Returns:
        Tuple of (max_message_id, error_message)
    """
    from ..services.crypto import decrypt_token

    user = connection.user
    max_token = decrypt_token(user.max_token or "")
    max_chat_id = connection.max_chat_id

    if not max_token or not max_chat_id:
        error = "Max credentials not configured"
        logger.error(error)
        return None, error

    max_client = MaxClient(max_token)
    max_message_id = None
    error_message = None

    try:
        if post_data.get("photo"):
            # Photo forwarding not fully implemented without Telegram file URL
            logger.warning(
                "Photo forwarding not fully implemented without Telegram file URL"
            )
            error_message = "Photo forwarding requires Telegram file download"
            return None, error_message

        elif post_data.get("text"):
            result = await max_client.send_text(max_chat_id, post_data["text"])
            max_message_id = str(result.get("message_id", ""))

        else:
            error_message = f"Unsupported content type: {list(post_data.keys())}"
            logger.warning(error_message)

    except MaxServiceError as e:
        error_message = str(e)
        logger.error("Failed to forward post to Max: %s", e)

    return max_message_id, error_message
