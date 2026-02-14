"""Email service for sending verification and password reset emails."""

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Exception raised when email sending fails."""

    pass


def _create_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> EmailMessage:
    """Create an email message.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body content

    Returns:
        EmailMessage object
    """
    msg = EmailMessage()
    msg["From"] = formataddr(
        (settings.SMTP_FROM_NAME, settings.SMTP_FROM)
    )
    msg["To"] = to_email
    msg["Subject"] = subject

    # Set content as HTML
    msg.add_alternative(html_content, subtype="html")

    return msg


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> dict[str, Any]:
    """Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body content

    Returns:
        Dictionary with success status

    Raises:
        EmailError: If email sending fails
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email send")
        return {"success": True, "skipped": True}

    msg = _create_email(to_email, subject, html_content)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()

            # Login
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            # Send
            server.send_message(msg)

            logger.info("Email sent to %s: %s", to_email, subject)
            return {"success": True}

    except smtplib.SMTPException as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        raise EmailError(f"Failed to send email: {e}") from e


def send_verification_email(
    to_email: str,
    token: str,
) -> dict[str, Any]:
    """Send an email verification email.

    Args:
        to_email: Recipient email address
        token: Verification token

    Returns:
        Dictionary with success status
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; }}
            .content {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px 0; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Verify Your Email Address</h2>
            </div>
            <div class="content">
                <p>Thank you for registering with Telegram Crossposter!</p>
                <p>Please verify your email address by clicking the button below:</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 3px;">
                    {verification_url}
                </p>
                <p>This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.</p>
            </div>
            <div class="footer">
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, "Verify Your Email Address", html_content)


def send_password_reset_email(
    to_email: str,
    token: str,
) -> dict[str, Any]:
    """Send a password reset email.

    Args:
        to_email: Recipient email address
        token: Password reset token

    Returns:
        Dictionary with success status
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; }}
            .content {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px 0; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Reset Your Password</h2>
            </div>
            <div class="content">
                <p>We received a request to reset your password for Telegram Crossposter.</p>
                <p>Click the button below to set a new password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 3px;">
                    {reset_url}
                </p>
            </div>
            <div class="warning">
                <p><strong>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.</strong></p>
                <p>If you didn't request this password reset, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>Telegram Crossposter</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, "Reset Your Password", html_content)