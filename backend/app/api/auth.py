"""Authentication API routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_async_session
from ..database.models import User
from ..schemas.auth import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..schemas.user import MessageResponse
from ..services.auth_service import (
    create_password_reset_token,
    create_verification_token,
    generate_jwt_token,
    hash_password,
    verify_email_token,
    verify_password,
    verify_password_reset_token,
)
from ..services.captcha_service import require_captcha
from ..services.email_service import (
    send_password_reset_email,
    send_verification_email,
)

from .deps import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenResponse:
    """Register a new user account.

    - Requires valid Cloudflare Turnstile captcha token
    - Sends verification email
    - Returns JWT access token
    """
    # Validate captcha
    remote_ip = request.client.host if request.client else None
    await require_captcha(user_data.captcha_token, remote_ip)

    # Check if user already exists
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_email_verified=False,
    )
    session.add(user)
    await session.flush()

    # Create and send verification email
    verification_token = await create_verification_token(session, user.id)
    send_verification_email(user.email, verification_token)

    # Commit after email sending
    await session.commit()

    # Generate JWT token
    access_token = generate_jwt_token(user.id)

    logger.info("New user registered: %s (verification email sent)", user.email)

    return TokenResponse(access_token=access_token)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: EmailVerifyRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> MessageResponse:
    """Verify a user's email address using verification token."""
    user = await verify_email_token(session, data.token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    await session.commit()

    logger.info("Email verified for user: %s", user.email)

    return MessageResponse(message="Email verified successfully")


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenResponse:
    """Authenticate user and return JWT token.

    - Requires valid Cloudflare Turnstile captcha token
    - Password must match hashed password in database
    """
    # Validate captcha
    remote_ip = request.client.host if request.client else None
    await require_captcha(user_data.captcha_token, remote_ip)

    # Find user by email
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT token
    access_token = generate_jwt_token(user.id)

    logger.info("User logged in: %s", user.email)

    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    """Logout the current user.

    Since we use stateless JWT tokens, the client should simply
    discard the token. This endpoint exists for API completeness.
    """
    return MessageResponse(message="Logout successful")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_obj: CurrentUser,
) -> UserResponse:
    """Get information about the currently authenticated user."""
    return UserResponse(
        id=current_user_obj.id,
        email=current_user_obj.email,
        max_token_set=bool(current_user_obj.max_token),
        max_chat_id=current_user_obj.max_chat_id,
        connections_limit=current_user_obj.connections_limit,
        daily_posts_limit=current_user_obj.daily_posts_limit,
        is_email_verified=current_user_obj.is_email_verified,
        created_at=current_user_obj.created_at,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> MessageResponse:
    """Request a password reset email.

    - Requires valid Cloudflare Turnstile captcha token
    - Sends email with reset token if user exists
    """
    # Validate captcha
    remote_ip = request.client.host if request.client else None
    await require_captcha(data.captcha_token, remote_ip)

    # Find user by email
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if user:
        # Create and send reset token
        reset_token = await create_password_reset_token(session, user)
        send_password_reset_email(user.email, reset_token)
        await session.commit()

        logger.info("Password reset requested for: %s", user.email)

    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If an account exists with that email, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> MessageResponse:
    """Reset password using the reset token from email.

    The token is single-use and expires after the configured time.
    """
    # Verify token and get user
    user = await verify_password_reset_token(session, data.token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user.hashed_password = hash_password(data.new_password)

    # Delete the used token
    from ..database.models import EmailVerificationToken

    result = await session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == data.token)
    )
    token_to_delete = result.scalar_one_or_none()
    if token_to_delete:
        await session.delete(token_to_delete)

    await session.commit()

    logger.info("Password reset for user: %s", user.email)

    return MessageResponse(message="Password reset successfully")