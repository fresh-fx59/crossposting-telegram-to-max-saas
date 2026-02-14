"""Main test emulator for integration testing."""

import asyncio
import httpx
import logging
from datetime import datetime, timezone

from .mocks import MockMaxAPI, MockSMTP, MockTelegramAPI, MockTurnstile

logger = logging.getLogger(__name__)


class TestEmulator:
    """Main test emulator with all mocks."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.mock_telegram = MockTelegramAPI()
        self.mock_max = MockMaxAPI()
        self.mock_smtp = MockSMTP()
        self.mock_turnstile = MockTurnstile()
        self.api_url = api_url

        # Test data
        self.test_email = f"test_{asyncio.get_event_loop().time()}@example.com"
        self.test_password = "testpassword123"
        self.test_max_token = "test_max_bot_token_xyz"
        self.test_max_chat_id = 123456789
        self.access_token: str | None = None
        self.webhook_secret: str | None = None

        # Get default bot token
        self.test_bot_token = list(self.mock_telegram.bots.keys())[0] if self.mock_telegram.bots else ""

        logger.info(f"TestEmulator initialized with URL: {api_url}")

    async def cleanup(self):
        """Clean up test data between tests."""
        self.mock_max.clear()
        self.mock_smtp.clear()
        logger.info("Test emulator cleaned up")

    async def close(self):
        """Close any resources."""
        # Placeholder for cleanup
        pass