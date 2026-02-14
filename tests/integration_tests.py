"""Integration tests for the SaaS application."""

import asyncio
import time
from typing import Any

import httpx

from .mocks import MockMaxAPI, MockSMTP, MockTelegramAPI, MockTurnstile
from .test_emulator import TestEmulator
from .test_result import TestResult, TestSuite


# ============================================================================
# Test Functions
# ============================================================================

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
            return TestResult(
                name=name,
                passed=False,
                message="No access_token in response",
                duration_ms=(time.time() - start_time) * 1000,
            )

        emulator.access_token = data["access_token"]

        if not emulator.mock_smtp.sent_emails:
            return TestResult(
                name=name,
                passed=False,
                message="No verification email sent",
                duration_ms=(time.time() - start_time) * 1000,
            )

        return TestResult(
            name=name,
            passed=True,
            message=f"Registered user {emulator.test_email}, email sent",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


async def test_email_verification(emulator: TestEmulator) -> TestResult:
    """Test email verification flow."""
    start_time = time.time()
    name = "Email Verification"

    try:
        token = emulator.mock_smtp.find_verification_link(emulator.test_email)
        if not token:
            return TestResult(
                name=name,
                passed=False,
                message="No verification link found",
                duration_ms=(time.time() - start_time) * 1000,
            )

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{emulator.api_url}/auth/verify-email",
                json={"token": token},
            )

        if response.status_code != 200:
            return TestResult(
                name=name,
                passed=False,
                message=f"Verification failed: {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        return TestResult(
            name=name,
            passed=True,
            message="Email verified successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


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
            return TestResult(
                name=name,
                passed=False,
                message=f"Update failed: {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        return TestResult(
            name=name,
            passed=True,
            message="User settings updated successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


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
            return TestResult(
                name=name,
                passed=False,
                message=f"Creation failed: {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        data = response.json()
        if "id" not in data:
            return TestResult(
                name=name,
                passed=False,
                message="Invalid response structure",
                duration_ms=(time.time() - start_time) * 1000,
            )

        webhook_url = data.get("webhook_url", "")
        emulator.webhook_secret = webhook_url.split("/")[-1] if webhook_url else ""

        return TestResult(
            name=name,
            passed=True,
            message=f"Telegram connection created (id: {data['id']})",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


async def test_create_connection(emulator: TestEmulator) -> TestResult:
    """Test creating a Telegram->Max connection."""
    start_time = time.time()
    name = "Create Connection"

    try:
        headers = {"Authorization": f"Bearer {emulator.access_token}"}

        # Get Telegram connections
        async with httpx.AsyncClient(timeout=30) as client:
            tg_response = await client.get(
                f"{emulator.api_url}/api/connections/telegram",
                headers=headers,
            )

        tg_connections = tg_response.json()
        if not tg_connections:
            return TestResult(
                name=name,
                passed=False,
                message="No Telegram connections found",
                duration_ms=(time.time() - start_time) * 1000,
            )

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
            return TestResult(
                name=name,
                passed=False,
                message=f"Creation failed: {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        return TestResult(
            name=name,
            passed=True,
            message="Connection created successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


async def test_forward_text_post(emulator: TestEmulator) -> TestResult:
    """Test forwarding a text post from Telegram to Max via webhook."""
    start_time = time.time()
    name = "Forward Text Post (Webhook)"

    try:
        emulator.mock_max.clear()

        if not emulator.webhook_secret:
            return TestResult(
                name=name,
                passed=False,
                message="No webhook secret available",
                duration_ms=(time.time() - start_time) * 1000,
            )

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
            return TestResult(
                name=name,
                passed=False,
                message=f"Webhook failed: {response.status_code}",
                error=response.text,
                duration_ms=(time.time() - start_time) * 1000,
            )

        if emulator.mock_max.get_message_count() == 0:
            return TestResult(
                name=name,
                passed=False,
                message="Message not forwarded to Max",
                duration_ms=(time.time() - start_time) * 1000,
            )

        latest_message = emulator.mock_max.get_latest_message()
        if not latest_message or latest_message.get("text") != test_text:
            actual = latest_message.get("text", "null") if latest_message else "null"
            return TestResult(
                name=name,
                passed=False,
                message=f"Message mismatch: expected '{test_text}' got '{actual}'",
                duration_ms=(time.time() - start_time) * 1000,
            )

        return TestResult(
            name=name,
            passed=True,
            message=f"Text post forwarded successfully",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            message=f"Exception: {e}",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


# ============================================================================
# Test Runner
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


async def main():
    """Run all tests and display results."""
    from .test_result import TestSuite

    print("\n" + "=" * 70)
    print("  TELEGRAM CROSSPOSTER SAAS - AUTOMATED TEST SUITE")
    print("=" * 70)

    emulator = TestEmulator()
    suite = await run_all_tests(emulator)
    await emulator.cleanup()

    suite.print_summary()
    return suite.summary()