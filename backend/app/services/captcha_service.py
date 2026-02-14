"""Cloudflare Turnstile captcha validation service."""

import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Cloudflare Turnstile verification URL
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def validate_turnstile_token(token: str, remote_ip: str | None = None) -> dict[str, Any]:
    """Validate a Cloudflare Turnstile token.

    Args:
        token: The Turnstile token from the client
        remote_ip: Optional remote IP address for additional verification

    Returns:
        Dictionary with success status and error codes if any
    """
    if not settings.CLOUDFLARE_TURNSTILE_SECRET:
        # In development/test mode without a secret, skip validation
        logger.warning("CLOUDFLARE_TURNSTILE_SECRET not set, skipping validation")
        return {"success": True}

    # Prepare request data
    data = {
        "secret": settings.CLOUDFLARE_TURNSTILE_SECRET,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(TURNSTILE_VERIFY_URL, data=data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to validate Turnstile token: %s", e)
            return {
                "success": False,
                "error-codes": ["validation-failed"],
                "message": f"Failed to validate captcha: {e}",
            }


async def require_captcha(token: str, remote_ip: str | None = None) -> None:
    """Require valid captcha token, raise exception if invalid.

    Args:
        token: The Turnstile token from the client
        remote_ip: Optional remote IP address

    Raises:
        ValueError: If captcha validation fails
    """
    result = await validate_turnstile_token(token, remote_ip)

    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        error_message = result.get("message", "Captcha validation failed")

        if "invalid-input-secret" in error_codes:
            logger.error("Invalid Turnstile secret key configured")
            raise ValueError("Server configuration error (invalid captcha secret)")

        raise ValueError(f"Captcha validation failed: {error_message}")