"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..database.models import User
from ..config import settings
from .services.auth_service import decode_jwt_token, verify_token


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials
        session: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify and decode token
    payload = verify_token(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    # Get user ID from payload
    user_id: int = int(payload.get("sub", 0))
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Fetch user from database
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def require_email_verified(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require email verification.

    Raises:
        HTTPException: If user's email is not verified
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_email_verified_optional(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Like require_email_verified but doesn't raise an exception.

    Returns the same user regardless of verification status.
    The endpoint caller can check current_user.is_email_verified.
    """
    return current_user


CurrentUserId = Annotated[int, Depends(lambda cu: cu.id)]


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
VerifiedUser = Annotated[User, Depends(require_email_verified)]
VerifiedUserOptional = Annotated[User, Depends(require_email_verified_optional)]