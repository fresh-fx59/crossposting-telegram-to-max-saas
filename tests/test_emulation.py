"""
Comprehensive test stand emulation for Telegram-to-Max Crossposting SaaS.

This module provides a complete test environment with mocks for all external services:
- Mock Telegram API
- Mock Max API  
- Mock SMTP (email service)
- Mock Cloudflare Turnstile (captcha)
- In-memory SQLite database

Tests are full user flow from registration to post forwarding.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# ============================================================================
# Mocks for External Services
# ============================================================================

class MockTelegramAPI:
    """Mock Telegram API for testing."""

    def __init__(self):
        self.bots: dict[str, "TelegramMockBot"] = {}
        self.webhooks: dict[str, str] = {}
        self.sent_messages: list[dict] = []
        self.channels: dict[str, "TelegramMockChannel"] = {}
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
        logger.info(f"Created default test bot")

        channel = TelegramMockChannel(
            id=-1001234567890,
            username="testchannel",
            title="Test Channel",
            type="channel",
        )
        self.channels["@testchannel"] = channel
        logger.info(f"Created default test channel: @testchannel")

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
            logger.info(f"Set webhook for bot to: {webhook_url}")
            return {"ok": True, "result": True, "description": "Webhook was set"}
        return {"ok": False, "description": "Invalid bot token"}

    async def deleteWebhook(self, bot_token: str) -> dict[str, Any]:
        """Simulate deleteWebhook API call."""
        if bot_token in self.webhooks:
            self.webhooks.pop(bot_token)
            logger.info(f"Deleted webhook for bot")
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
        logger.info(f"MockMax: Sent text to chat {chat_id}: '{text[:30]}...'")
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
        logger.info("MockMax: Cleared all messages")


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
        logger.info(f"MockSMTP: Sent email to {to} - {subject}")
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
        logger.info("MockSMTP: Cleared all emails")


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


# ============================================================================
# Test Result and Suite
# ============================================================================

@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0
    error: str | None = None


@dataclass
class TestSuite:
    """Test suite for running multiple tests."""
    name: str
    tests: list[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult):
        self.tests.append(result)

    def summary(self) -> dict[str, Any]:
        passed = sum(1 for t in self.tests if t.passed)
        return {
            "name": self.name,
            "total": len(self.tests),
            "passed": passed,
            "failed": len(self.tests) - passed,
            "tests": [t.__dict__ for t in self.tests],
        }

    def print_summary(self):
        """Print human-readable test summary."""
        print("\n" + "=" * 70)
        print(f"  TEST SUITE: {self.name}")
        print("=" * 70)

        for i, test in enumerate(self.tests, 1):
            status = "✓ PASS" if test.passed else "✗ FAIL"
            print(f"\n{i}. {test.name}")
            print(f"   Status: {status}")
            print(f"   Message: {test.message}")
            print(f"   Duration: {test.duration_ms:.2f}ms")
            if test.error:
                print(f"   Error: {test.error}")

        summary = self.summary()
        print("\n" + "-" * 70)
        print(f"  SUMMARY: {summary['passed']}/{summary['total']} tests passed")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print("=" * 70 + "\n")


# ============================================================================
# Test Emulator
# ============================================================================

class TestEmulator:
    """Main test emulator with all mocks."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.mock_telegram = MockTelegramAPI()
        self.mock_max = MockMaxAPI()
        self.mock_smtp = MockSMTP()
        self.mock_turnstile = MockTurnstile()
        self.api_url = api_url
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "testpassword123"
        self.test_max_token = "test_max_bot_token_xyz"
        self.test_max_chat_id = 123456789
        self.access_token: str | None = None
        self.test_bot_token = list(self.mock_telegram.bots.keys())[0] if self.mock_telegram.bots else ""
        self.webhook_secret: str | None = None

        logger.info(f"TestEmulator initialized with URL: {api_url}")

    async def cleanup(self):
        """Clean up test data between tests."""
        self.mock_max.clear()
        self.mock_smtp.clear()


# ============================================================================
# Integration Tests
# ============================================================================


async def run_all_tests(emulator: TestEmulator) -> TestSuite:
    """Run all test scenarios."""
    suite = TestSuite(name="Telegram Crossposter SaaS Integration Tests")
    
    suite.add_result(await test_user_registration(emulator))
    suite.add_result(await test_email_verification(emulator))
    suite.add_result(await test_update_user_settings(emulator))
    suite.add_result(await test_create_telegram_connection(emulator))
    suite.add_result(await test_create_connection(emulator))
    suite.add_result(await test_forward_text_post(emulator))
    
    return suite


async def test_user_registration(emulator: TestEmulator) -> TestResult:
    """Test user registration flow."""
    start_time = time.time()
    name = "User Registration"

    try:
        captcha_token = emulator.mock_turnstile.generate_valid_token()

        payload = {
            "email": emulator.test_email,
            "password": emulator.test_password,
            "captcha_token": captcha_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/auth/register",
                json=payload,
            )

        if response.status_code not in (200, 201):
            return TestResult(
                name=name,
                passed=False,
                message=f"Expected 200/201, got {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        data = response.json()
        if "access_token" not in data:
            return TestResult(name=name, passed=False, message="No access_token in response", duration_ms=(time.time() - start_time) * 1000)

        emulator.access_token = data["access_token"]

        if not emulator.mock_smtp.sent_emails:
            return TestResult(name=name, passed=False, message="No verification email sent", duration_ms=(time.time() - start_time) * 1000)

        return TestResult(
            name=name,
            passed=True,
            message=f"Registered user {emulator.test_email}, email sent",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


async def test_email_verification(emulator: TestEmulator) -> TestResult:
    """Test email verification flow."""
    start_time = time.time()
    name = "Email Verification"

    try:
        token = emulator.mock_smtp.find_verification_link(emulator.test_email)
        if not token:
            return TestResult(name=name, passed=False, message="No verification link found", duration_ms=(time.time() - start_time) * 1000)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/auth/verify-email",
                json={"token": token},
            )

        if response.status_code != 200:
            return TestResult(name=name, passed=False, message=f"Verification failed: {response.status_code}", error=response.text, duration_ms=(time.time() - start_time) * 1000)

        return TestResult(
            name=name,
            passed=True,
            message="Email verified successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


async def test_update_user_settings(emulator: TestEmulator) -> TestResult:
    """Test updating user settings (Max credentials)."""
    start_time = time.time()
    name = "Update User Settings"

    try:
        headers = {"Authorization": f"Bearer {emulator.access_token}"}

        settings_payload = {
            "max_token": emulator.test_max_token,
            "max_chat_id": emulator.test_max_chat_id,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.put(
                f"{emulator.api_url}/api/users/me",
                json=settings_payload,
                headers=headers,
            )

        if response.status_code != 200:
            return TestResult(name=name, passed=False, message=f"Update failed: {response.status_code}", error=response.text, duration_ms=(time.time() - start_time) * 1000)

        return TestResult(
            name=name,
            passed=True,
            message="User settings updated successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


async def test_create_telegram_connection(emulator: TestEmulator) -> TestResult:
    """Test creating a Telegram connection."""
    start_time = time.time()
    name = "Create Telegram Connection"

    try:
        headers = {"Authorization": f"Bearer {emulator.access_token}"}

        tg_payload = {
            "telegram_channel_username": "@testchannel",
            "bot_token": emulator.test_bot_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/api/connections/telegram",
                json=tg_payload,
                headers=headers,
            )

        if response.status_code not in (200, 201):
            return TestResult(name=name, passed=False, message=f"Creation failed: {response.status_code}", error=response.text, duration_ms=(time.time() - start_time) * 1000)

        data = response.json()
        if "id" not in data:
            return TestResult(name=name, passed=False, message="Invalid response structure", duration_ms=(time.time() - start_time) * 1000)

        webhook_url = data.get("webhook_url", "")
        extractor webhook_secret
        emulator.webhook_secret = webhook_url.split("/")[-1] if webhook_url else ""

        return TestResult(
            name=name,
            passed=True,
            message=f"Telegram connection created (id: {data['id']})",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


async def test_create_connection(emulator: TestEmulator) -> TestResult:
    """Test creating a Telegram->Max connection."""
    start_time = time.time()
    name = "Create Connection"

    try:
        headers = {"Authorization": f"Bearer {emulator.access_token}"}

        async with httpx.AsyncClient(timeout=30) as client:
            tg_response = await client.get(
                f"{emulator.api_url}/api/connections/telegram",
                headers=headers,
            )

        tg_connections = tg_response.json()
        if not tg_connections:
            return TestResult(name=name, passed=False, message="No Telegram connections found", duration_ms=(time.time() - start_time) * 1000)

        tg_conn_id = tg_connections[0]["id"]

        conn_payload = {
            "telegram_connection_id": tg_conn_id,
            "max_chat_id": emulator.test_max_chat_id,
            "name": "Test Connection",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/api/connections",
                json=conn_payload,
                headers=headers,
            )

        if response.status_code not in (200, 201):
            return TestResult(name=name, passed=False, message=f"Creation failed: {response.status_code}", error=response.text, duration_ms=(time.time() - start_time) * 1000)

        return TestResult(
            name=name,
            passed=True,
            message="Connection created successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


async def test_forward_text_post(emulator: TestEmulator) -> TestResult:
    """Test forwarding a text post from Telegram to Max via webhook."""
    start_time = time.time()
    name = "Forward Text Post (Webhook)"

    try:
        emulator.mock_max.clear()

        if not emulator.webhook_secret:
            return TestResult(name=name, passed=False, message="No webhook secret available", duration_ms=(time.time() - start_time) * 1000)

        test_text = "This is a test message from Telegram webhook!"
        webhook_payload = emulator.mock_telegram.create_channel_post(
            channel_id=-1001234567890,
            text=test_text,
        )

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/webhook/telegram/{emulator.webhook_secret}",
                json=webhook_payload,
            )

        if response.status_code != 200:
            return TestResult(name=name, passed=False, message=f"Webhook failed: {response.status_code}", error=response.text, duration_ms=(time.time() - start_time) * 1000)

        if emulator.mock_max.get_message_count() == 0:
            return TestResult(name=name, passed=False, message="Message not forwarded to Max", duration_ms=(time.time() - start_time) * 1000)

        latest_message = emulator.mock_max.get_latest_message()
        if not latest_message or latest_message.get("text") != test_text:
            actual = latest_message.get("text", "null") if latest_message else "null"
            return TestResult(name=name, passed=False, message=f"Message mismatch: '{actual}' vs '{test_text}'", duration_ms=(time.time() - start_time) * 1000)

        return TestResult(
            name=name,
            passed=True,
            message=f"Text post forwarded successfully: '{test_text[:30]}...'",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(name=name, passed=False, message=f"Exception: {e}", error=str(e), duration_ms=(time.time() - start_time) * 1000)


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run all tests and display results."""
    print("\n" + "=" * 70)
    print("  TELEGRAM CROSSPOSTER SAAS - AUTOMATED TEST SUITE")
    print("=" * 70)

    # Test mocks
    print("\n1. Testing mock components...")
    mock_tests = TestSuite(name="Mock Components")
    
    # Test MockTelegram
    try:
        tg = MockTelegramAPI()
        result = await tg.getMe(tg.bots.keys().__next__())
        mock_tests.add_result(TestResult(name="Mock Telegram API", passed=result["ok"], message="getMe successful", duration_ms=10))
    except Exception as e:
        mock_tests.add_result(TestResult(name="Mock Telegram API", passed=False, message=str(e), error=str(e), duration_ms=10))

    # Test MockMax
    try:
        max_api = MockMaxAPI()
        msg = await max_api.send_message("token", 123, "test")
        mock_tests.add_result(TestResult(name="Mock Max API", passed="message_id" in msg, message="Message sent", duration_ms=10))
    except Exception as e:
        mock_tests.add_result(TestResult(name="Mock Max API", passed=False, message=str(e), error=str(e), duration_ms=10))

    # Test MockSMTP
    try:
        smtp = MockSMTP()
        smtp.send("test@example.com", "Subject", "HTML")
        mock_tests.add_result(TestResult(name="Mock SMTP", passed=bool(smtp.sent_emails), message="Email sent", duration_ms=10))
    except Exception as e:
        mock_tests.add_result(TestResult(name="Mock SMTP", passed=False, message=str(e), error=str(e), duration_ms=10))

    # Test MockTurnstile
    try:
        turnstile = MockTurnstile()
        token = turnstile.generate_valid_token()
        result = await turnstile.validate(token)
        mock_tests.add_result(TestResult(name="Mock Turnstile", passed=result["success"], message="Token validated", duration_ms=10))
    except Exception as e:
        mock_tests.add_result(TestResult(name="Mock Turnstile", passed=False, message=str(e), error=str(e), duration_ms=10))

    mock_tests.print_summary()

    # Run integration tests
    print("\n2. Running integration tests (requires running backend)...")
    print("   Note: If backend is not running, these tests will fail.\n")
    
    emulator = TestEmulator()
    suite = await run_all_tests(emulator)
    await emulator.claenup()
    suite.print_summary()

    return suite.summary()


if __name__ == "__main__":
    asyncio.run(main())
