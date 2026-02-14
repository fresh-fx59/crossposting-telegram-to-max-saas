"""Authentication service for JWT and password management."""

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import EmailVerificationToken, User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def generate_jwt_token(user_id: int) -> str:
    """Generate a JWT access token.

    Args:
        user_id: User ID to encode in token

    Returns:
        JWT access token string
    """
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_jwt_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload as dict

    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_token(token: str, secret: str, algorithms: list[str]) -> dict:
    """Verify a JWT token.

    This is the function referenced in deps.py.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=algorithms)
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def generate_verification_token() -> str:
    """Generate a secure random token for email verification.

    Returns:
        Random token string
    """
    return secrets.token_urlsafe(32)


async def create_verification_token(session: AsyncSession, user_id: int) -> str:
    """Create an email verification token for a user.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        The verification token
    """
    token = generate_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )

    verification_token = EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )

    session.add(verification_token)
    await session.flush()

    return token


async def verify_email_token(
    session: AsyncSession,
    token: str,
) -> User | None:
    """Verify an email verification token and return the user.

    Args:
        session: Database session
        token: Verification token

    Returns:
        User if token is valid, None otherwise
    """
    # Find the token
    result = await session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        return None

    # Check if token is expired
    if verification_token.expires_at < datetime.now(timezone.utc):
        await session.delete(verification_token)
        await session.flush()
        return None

    # Fetch the user
    user_result = await session.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        return None

    # Mark user as verified
    user.is_email_verified = True

    # Delete the verification token
    await session.delete(verification_token)

    return user


async def create_password_reset_token(session: AsyncSession, user: User) -> str:
    """Create a password reset token for a user.

    Args:
        session: Database session
        user: User object

    Returns:
        The reset token
    """
    token = generate_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )

    # Delete any existing reset tokens for this user
    result = await session.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id
        )
    )
    existing_tokens = result.scalars().all()
    for existing_token in existing_tokens:
        await session.delete(existing_token)

    # Create new token
    reset_token = EmailVerificationToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )

    session.add(reset_token)
    await session.flush()

    return token


async def verify_password_reset_token(
    session: AsyncSession,
    token: str,
) -> User | None:
    """Verify a password reset token and return the user.

    Args:
        session: Database session
        token: Reset token

    Returns:
        User if token is valid, None otherwise
    """
    result = await session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        return None

    if verification_token.expires_at < datetime.now(timezone.utc):
        await session.delete(verification_token)
        await session.flush()
        return None

    user_result = await session.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        return None

    return user