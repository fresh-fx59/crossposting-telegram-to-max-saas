"""Telegram service for webhook management and API interactions."""

import logging
import secrets
from typing import Any

import httpx

from ..config import settings
from ..services.crypto import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)


async def get_telegram_bot_info(bot_token: str) -> dict[str, Any]:
    """Get bot information from Telegram API.

    Args:
        bot_token: Telegram bot token

    Returns:
        Bot info dictionary with id, username, etc.
    """
    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/getMe"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        raise ValueError(f"Telegram API error: {error}")

    return data["result"]


async def get_chat_info_by_username(bot_token: str, username: str) -> dict[str, Any]:
    """Get chat information by username (public channel).

    Args:
        bot_token: Telegram bot token
        username: Channel username (with or without @)

    Returns:
        Chat info dictionary
    """
    # Remove @ prefix if present
    username = username.lstrip("@")

    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/getChat?chat_id=@{username}"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        raise ValueError(f"Telegram API error: {error}")

    return data["result"]


async def set_webhook(
    bot_token: str,
    webhook_url: str,
    max_connections: int = 40,
) -> dict[str, Any]:
    """Set up Telegram webhook for a bot.

    Args:
        bot_token: Telegram bot token
        webhook_url: Full webhook URL
        max_connections: Maximum number of parallel connections

    Returns:
        Response from Telegram API
    """
    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/setWebhook"
    params = {
        "url": webhook_url,
        "max_connections": max_connections,
        "drop_pending_updates": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=params)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        raise ValueError(f"Failed to set webhook: {error}")

    logger.info("Telegram webhook set to: %s", webhook_url)
    return data


async def delete_webhook(bot_token: str) -> dict[str, Any]:
    """Delete Telegram webhook for a bot.

    Args:
        bot_token: Telegram bot token

    Returns:
        Response from Telegram API
    """
    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/deleteWebhook"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        logger.warning("Failed to delete webhook: %s", error)
        return data

    logger.info("Telegram webhook deleted for bot")
    return data


async def get_webhook_info(bot_token: str) -> dict[str, Any]:
    """Get current webhook information for a bot.

    Args:
        bot_token: Telegram bot token

    Returns:
        Webhook info dictionary
    """
    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/getWebhookInfo"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        raise ValueError(f"Failed to get webhook info: {error}")

    return data["result"]


async def send_message(bot_token: str, chat_id: int | str, text: str) -> dict[str, Any]:
    """Send a text message via Telegram bot.

    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID or username
        text: Message text

    Returns:
        Response from Telegram API
    """
    url = f"{settings.TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": text}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=params)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        error = data.get("description", "Unknown error")
        raise ValueError(f"Failed to send message: {error}")

    return data["result"]


def generate_webhook_secret() -> str:
    """Generate a secure random webhook secret.

    Returns:
        Random secret string
    """
    return secrets.token_urlsafe(32)


async def get_channel_id_from_username(bot_token: str, username: str) -> int:
    """Get numeric channel ID from username.

    Args:
        bot_token: Telegram bot token
        username: Channel username (with or without @)

    Returns:
        Numeric channel ID
    """
    chat_info = await get_chat_info_by_username(bot_token, username)
    return int(chat_info["id"])