"""Telegram bot command webhook for onboarding and billing."""

import logging
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_async_session
from ..database.models import PaymentTransaction, TelegramUserLink, User
from ..services.auth_service import decode_jwt_token
from ..services.billing_access import can_publish_with_billing_status
from ..services.billing_service import get_current_subscription, transition_subscription
from ..services.robokassa_service import build_payment_url, compute_payment_signature
from ..services.telegram_service import send_message

logger = logging.getLogger(__name__)
router = APIRouter()

PLAN_CATALOG = {
    "monthly": {
        "title": "Monthly",
        "price_rub": 990,
        "billing_period_days": 30,
        "recommended": True,
    },
    "annual": {
        "title": "Annual",
        "price_rub": 9990,
        "billing_period_days": 365,
        "recommended": False,
    },
}


@router.post("/bot/{webhook_secret}", status_code=status.HTTP_200_OK)
async def telegram_bot_commands_webhook(
    webhook_secret: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Process bot commands received from Telegram webhook."""
    if not settings.TELEGRAM_COMMAND_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot command webhook secret is not configured",
        )
    if webhook_secret != settings.TELEGRAM_COMMAND_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    if not settings.TELEGRAM_BOT_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot API token is not configured",
        )

    try:
        update = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"status": "ignored", "reason": "no message"}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = (chat.get("type") or "").lower()
    if not chat_id:
        return {"status": "ignored", "reason": "no chat id"}

    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return {"status": "ignored", "reason": "not a command"}

    from_user = message.get("from") or {}
    telegram_user_id = from_user.get("id")
    telegram_username = from_user.get("username")
    if not telegram_user_id:
        return {"status": "ignored", "reason": "no sender id"}

    command, arg = _parse_command(text)

    if command == "/start":
        await _reply(chat_id, _start_message())
        return {"status": "ok"}

    if command == "/plans":
        await _reply(chat_id, _plans_message())
        return {"status": "ok"}

    if command == "/link":
        if chat_type != "private":
            await _reply(chat_id, "For security, run /link only in a private chat with the bot.")
            return {"status": "ok"}
        if not arg:
            await _reply(chat_id, "Usage: /link <jwt_token>")
            return {"status": "ok"}
        link_result = await _link_user(session, int(telegram_user_id), telegram_username, arg)
        await _reply(chat_id, link_result)
        return {"status": "ok"}

    linked_user = await _get_linked_user(session, int(telegram_user_id))
    if linked_user is None:
        await _reply(
            chat_id,
            "Account is not linked. Send /link <jwt_token> from a private chat to continue.",
        )
        return {"status": "ok"}

    if command == "/status":
        await _reply(chat_id, await _status_message(session, linked_user))
        return {"status": "ok"}

    if command == "/pay":
        plan_code = (arg or "monthly").strip().lower()
        pay_message = await _create_payment_link(session, linked_user, plan_code)
        await _reply(chat_id, pay_message)
        return {"status": "ok"}

    await _reply(chat_id, "Unknown command. Available: /start, /plans, /link, /status, /pay")
    return {"status": "ok"}


def _parse_command(text: str) -> tuple[str, str | None]:
    raw = text.split(maxsplit=1)
    command = raw[0].split("@", maxsplit=1)[0].lower()
    arg = raw[1].strip() if len(raw) > 1 else None
    return command, arg


async def _reply(chat_id: int, text: str) -> None:
    try:
        await send_message(settings.TELEGRAM_BOT_API_TOKEN, chat_id, text)
    except Exception as exc:
        logger.exception("Failed to send bot reply to chat %s: %s", chat_id, exc)


def _start_message() -> str:
    return (
        "Crossposter onboarding bot\n\n"
        "Commands:\n"
        "/plans - show plans\n"
        "/link <jwt_token> - link your account\n"
        "/status - show billing status\n"
        "/pay [monthly|annual] - generate payment link"
    )


def _plans_message() -> str:
    lines = ["Available plans:"]
    for code, plan in PLAN_CATALOG.items():
        marker = " (recommended)" if plan["recommended"] else ""
        lines.append(f"- {code}: {plan['price_rub']} RUB{marker}")
    return "\n".join(lines)


async def _link_user(
    session: AsyncSession,
    telegram_user_id: int,
    telegram_username: str | None,
    token: str,
) -> str:
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub", 0))
    except Exception:
        return "Invalid JWT token. Generate a fresh token via web login and try again."

    if not user_id:
        return "Invalid token payload: user id is missing."

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return "User not found for this token."

    link_result = await session.execute(
        select(TelegramUserLink).where(TelegramUserLink.telegram_user_id == telegram_user_id)
    )
    link = link_result.scalar_one_or_none()

    if link is None:
        user_link_result = await session.execute(
            select(TelegramUserLink).where(TelegramUserLink.user_id == user_id)
        )
        user_link = user_link_result.scalar_one_or_none()
        if user_link and user_link.telegram_user_id != telegram_user_id:
            user_link.telegram_user_id = telegram_user_id
            user_link.telegram_username = telegram_username
        elif user_link is None:
            session.add(
                TelegramUserLink(
                    user_id=user_id,
                    telegram_user_id=telegram_user_id,
                    telegram_username=telegram_username,
                )
            )
    else:
        user_link_result = await session.execute(
            select(TelegramUserLink).where(TelegramUserLink.user_id == user_id)
        )
        user_link = user_link_result.scalar_one_or_none()
        if user_link and user_link.telegram_user_id != telegram_user_id:
            return "This account is already linked to another Telegram user."
        link.user_id = user_id
        link.telegram_username = telegram_username

    await session.commit()
    return "Account linked. You can now use /status and /pay."


async def _get_linked_user(session: AsyncSession, telegram_user_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .join(TelegramUserLink, TelegramUserLink.user_id == User.id)
        .where(TelegramUserLink.telegram_user_id == telegram_user_id)
    )
    return result.scalar_one_or_none()


async def _status_message(session: AsyncSession, user: User) -> str:
    current = await get_current_subscription(session, user.id)
    if current is None:
        return "Billing status: none. Use /pay monthly to start subscription."

    can_publish = can_publish_with_billing_status(current.status)
    lines = [
        f"Billing status: {current.status}",
        f"Plan: {current.plan_code}",
        f"Can publish: {'yes' if can_publish else 'no'}",
    ]
    if current.current_period_end:
        lines.append(f"Current period end: {current.current_period_end.isoformat()}")
    if current.trial_ends_at:
        lines.append(f"Trial ends at: {current.trial_ends_at.isoformat()}")
    return "\n".join(lines)


async def _create_payment_link(session: AsyncSession, user: User, plan_code: str) -> str:
    plan = PLAN_CATALOG.get(plan_code)
    if plan is None:
        return "Unknown plan. Supported: monthly, annual."
    if not settings.ROBOKASSA_MERCHANT_LOGIN or not settings.ROBOKASSA_PASSWORD_1:
        return "Billing provider is not configured yet."

    inv_id = f"{user.id}{int(time())}"
    out_sum = f"{plan['price_rub']:.2f}"
    shp_params = {
        "Shp_user_id": str(user.id),
        "Shp_plan": plan_code,
    }
    signature = compute_payment_signature(
        settings.ROBOKASSA_MERCHANT_LOGIN,
        out_sum,
        inv_id,
        settings.ROBOKASSA_PASSWORD_1,
        shp_params,
    )

    payment_url = build_payment_url(
        payment_url=settings.ROBOKASSA_PAYMENT_URL,
        merchant_login=settings.ROBOKASSA_MERCHANT_LOGIN,
        out_sum=out_sum,
        inv_id=inv_id,
        description=f"Crossposter {plan['title']} subscription",
        signature_value=signature,
        is_test=settings.ROBOKASSA_TEST_MODE,
        shp_params=shp_params,
    )

    current = await get_current_subscription(session, user.id)
    if current is None:
        current = await transition_subscription(
            session,
            user_id=user.id,
            next_status="trial",
            event_type="onboarding_started",
            provider_event_id=f"onboarding:{user.id}:{int(time())}",
            payload_json='{"source":"telegram_bot"}',
            plan_code="trial",
        )

    tx = PaymentTransaction(
        user_id=user.id,
        subscription_id=current.id if current else None,
        provider="robokassa",
        provider_payment_id=inv_id,
        status="created",
        amount_minor=plan["price_rub"] * 100,
        currency="RUB",
        idempotency_key=f"pay:{inv_id}",
    )
    session.add(tx)
    await session.commit()

    return f"Plan: {plan_code}\nAmount: {plan['price_rub']} RUB\nPay here: {payment_url}"
