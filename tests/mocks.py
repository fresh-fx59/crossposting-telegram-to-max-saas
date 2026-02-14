"""Mock services for testing (Telegram, Max, SMTP, Turnstile)."""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TelegramMockBot:
    """Mock Telegram bot."""
    id: int
    username: str
    first_name: str
    is_bot: bool
    token: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "is_bot": self.is_bot, "first_name": self.first_name, "username": self.username}


@dataclass
class TelegramMockChannel:
    """Mock Telegram channel."""
    id: int
    username: str
    title: str
    type: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "title": self.title, "username": self.username}


class MockTelegramAPI:
    """Mock Telegram API for testing."""

    def __init__(self):
        self.bots: dict[str, TelegramMockBot] = {}
        self.webhooks: dict[str, str] = {}
        self.sent_messages: list[dict] = []
        self.channels: dict[str, TelegramMockChannel] = {}
        self._create_default_bot()

    def _create_default_bot(self):
        """Create default test bot for testing."""
        bot_token = "test_telegram_bot_token_1234567890:ABCDEF"
        self.bots[bot_token] = TelegramMockBot(
            id=1234567890,
            username="test_bot",
            first_name="Test Bot",
            is_bot=True,
            token=bot_token,
        )

        channel = TelegramMockChannel(
            id=-1001234567890,
            username="testchannel",
            title="Test Channel",
            type="channel",
        )
        self.channels["@testchannel"] = channel

    async def getMe(self, bot_token: str) -> dict[str, Any]:
        """Simulate getMe API call."""
        bot = self.bots.get(bot_token)
        if bot:
            return {"ok": True, "result": bot.to_dict()}
        return {"ok": False, "description": "Invalid bot token"}

    async def setWebhook(self, bot_token: str, webhook_url: str) -> dict[str, Any]:
        """Simulate setWebhook API call."""
        if bot_token in self.bots:
            self.webhooks[bot_token] = webhook_url
            return {"ok": True, "result": True}
        return {"ok": False, "description": "Invalid bot token"}

    async def deleteWebhook(self, bot_token: str) -> dict[str, Any]:
        """Simulate deleteWebhook API call."""
        if bot_token in self.webhooks:
            self.webhooks.pop(bot_token)
            return {"ok": True, "result": True}
        return {"ok": True, "result": False}

    async def getWebhookInfo(self, bot_token: str) -> dict[str, Any]:
        """Simulate getWebhookInfo API call."""
        if bot_token in self.webhooks:
            return {
                "ok": True,
                "result": {"url": self.webhooks[bot_token], "has_custom_certificate": False, "pending_update_count": 0},
            }
        return {"ok": True, "result": {"url": "", "has_custom_certificate": False, "pending_update_count": 0}}

    def create_channel_post(self, channel_id: int, text: str) -> dict[str, Any]:
        """Create a mock channel post for webhook testing."""
        post = {
            "update_id": int(time.time() * 1000),
            "channel_post": {
                "message_id": len(self.sent_messages) + 1,
                "chat": {"id": channel_id, "title": "Test Channel", "type": "channel"},
                "date": int(time.time()),
                "text": text,
            },
        }
        self.sent_messages.append(post)
        return post


class MockMaxAPI:
    """Mock Max API for testing."""

    def __init__(self):
        self.messages: list[dict] = []
        self.next_message_id: int = 1

    async def send_message(self, token: str, chat_id: int, text: str) -> dict[str, Any]:
        """Simulate sending a text message to Max."""
        message = {
            "message_id": f"{self.next_message_id}",
            "chat_id": chat_id,
            "text": text,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.messages.append(message)
        self.next_message_id += 1
        return message

    def get_latest_message(self) -> dict | None:
        """Get most recent message."""
        return self.messages[-1] if self.messages else None

    def get_message_count(self) -> int:
        """Get total number of messages sent."""
        return len(self.messages)

    def clear(self):
        """Clear all messages."""
        self.messages.clear()


class MockSMTP:
    """Mock SMTP server for testing email sending."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    def send(self, to: str, subject: str, html: str) -> dict[str, Any]:
        """Simulate sending an email."""
        email_data = {
            "to": to,
            "subject": subject,
            "html": html,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sent_emails.append(email_data)
        return {"success": True}

    def find_verification_link(self, email: str) -> str | None:
        """Find a verification link in emails sent to an address."""
        for sent in self.sent_emails:
            if sent["to"] == email and "verify" in sent["subject"].lower():
                match = re.search(r'token=([a-zA-Z0-9_-]+)', sent["html"])
                if match:
                    return match.group(1)
        return None

    def clear(self):
        """Clear all sent emails."""
        self.sent_emails.clear()


class MockTurnstile:
    """Mock Cloudflare Turnstile for testing."""

    def __init__(self):
        self.valid_tokens: set[str] = set()

    def generate_valid_token(self) -> str:
        """Generate a valid mock Turnstile token."""
        token = f"valid_turnstile_token_{int(time.time() * 1000)}"
        self.valid_tokens.add(token)
        return token

    async def validate(self, token: str) -> dict[str, Any]:
        """Validate a Turnstile token."""
        if token in self.valid_tokens:
            return {"success": True}
        return {"success": False}