"""Token encryption utilities for secure storage of bot tokens."""

import base64
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from password using PBKDF2.

    Args:
        password: Password string
        salt: Salt bytes

    Returns:
        32-byte key for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# Use ENCRYPTION_KEY directly as a base64-encoded Fernet key
# Fernet keys must be 32 url-safe base64-encoded bytes
ENCRYPTION_KEY: bytes
try:
    # Try to use the encryption key as-is (should be 32 bytes base64)
    ENCRYPTION_KEY = settings.ENCRYPTION_KEY.encode()
    # Validate it's a valid Fernet key
    Fernet(ENCRYPTION_KEY)
except Exception:
    # If the key is invalid, derive one from the setting
    import os

    salt = b"telegram-crossposter-salt"
    ENCRYPTION_KEY = _derive_key(settings.ENCRYPTION_KEY, salt)


_cryptor = Fernet(ENCRYPTION_KEY)


def encrypt_token(token: str) -> str:
    """Encrypt a token string.

    Args:
        token: Plain text token

    Returns:
        Encrypted token as base64 string
    """
    if not token:
        return ""
    encrypted = _cryptor.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token string.

    Args:
        encrypted_token: Encrypted token as base64 string

    Returns:
        Plain text token

    Raises:
        ValueError: If decryption fails
    """
    if not encrypted_token:
        return ""
    try:
        decrypted = _cryptor.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except InvalidToken as e:
        raise ValueError("Failed to decrypt token") from e


def encrypt_optional_token(token: str | None) -> str | None:
    """Encrypt an optional token, returning None if input is None.

    Args:
        token: Plain text token or None

    Returns:
        Encrypted token or None
    """
    if token is None:
        return None
    return encrypt_token(token)


def decrypt_optional_token(encrypted_token: str | None) -> str | None:
    """Decrypt an optional token, returning None if input is None.

    Args:
        encrypted_token: Encrypted token or None

    Returns:
        Plain text token or None
    """
    if encrypted_token is None:
        return None
    return decrypt_token(encrypted_token)