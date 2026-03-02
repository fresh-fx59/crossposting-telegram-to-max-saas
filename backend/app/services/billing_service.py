"""Billing helper functions."""

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import BillingEvent, PaymentTransaction, Subscription
from .subscription_state_machine import apply_status_fields, ensure_valid_transition


async def get_current_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    """Return the latest subscription row for a user."""
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(desc(Subscription.created_at), desc(Subscription.id))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def transition_subscription(
    session: AsyncSession,
    *,
    user_id: int,
    next_status: str,
    event_type: str,
    provider_event_id: str | None = None,
    transaction: PaymentTransaction | None = None,
    payload_json: str | None = None,
    plan_code: str = "monthly",
) -> Subscription:
    """Transition current user subscription and persist immutable billing event."""
    subscription = await get_current_subscription(session, user_id)
    current_status = "none"
    if subscription is None:
        subscription = Subscription(
            user_id=user_id,
            plan_code=plan_code,
            status="trial",
            provider="robokassa",
        )
        session.add(subscription)
        await session.flush()
    else:
        current_status = subscription.status

    ensure_valid_transition(current_status, next_status)
    now = datetime.now(timezone.utc)
    apply_status_fields(subscription, next_status, now=now)
    if plan_code:
        subscription.plan_code = plan_code

    event = BillingEvent(
        user_id=user_id,
        subscription=subscription,
        transaction=transaction,
        event_type=event_type,
        status_before=current_status,
        status_after=next_status,
        provider_event_id=provider_event_id,
        occurred_at=now,
        payload_json=payload_json,
    )
    session.add(event)
    await session.flush()
    return subscription
