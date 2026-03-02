"""Subscription status transition rules."""

from datetime import datetime, timedelta, timezone


BILLING_STATES = {
    "trial",
    "active",
    "grace",
    "past_due",
    "cancelled",
    "expired",
}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "none": {"trial", "active"},
    "trial": {"active", "cancelled", "expired"},
    "active": {"grace", "past_due", "cancelled", "expired"},
    "grace": {"active", "past_due", "cancelled", "expired"},
    "past_due": {"active", "cancelled", "expired"},
    "cancelled": {"active", "expired"},
    "expired": {"active"},
}


def ensure_valid_transition(current_status: str, next_status: str) -> None:
    """Raise ValueError when transition is not allowed."""
    if next_status not in BILLING_STATES:
        raise ValueError(f"Unknown target status: {next_status}")
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise ValueError(f"Invalid transition: {current_status} -> {next_status}")


def apply_status_fields(
    subscription: object,
    next_status: str,
    *,
    now: datetime | None = None,
    period_days: int = 30,
    grace_days: int = 3,
    trial_days: int = 7,
) -> None:
    """Apply derived field updates for subscription status."""
    if now is None:
        now = datetime.now(timezone.utc)

    subscription.status = next_status
    if next_status == "trial":
        subscription.trial_ends_at = now + timedelta(days=trial_days)
    elif next_status == "active":
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=period_days)
        subscription.grace_ends_at = None
        subscription.cancelled_at = None
    elif next_status == "grace":
        subscription.grace_ends_at = now + timedelta(days=grace_days)
    elif next_status == "cancelled":
        subscription.cancelled_at = now
    elif next_status == "expired":
        if getattr(subscription, "grace_ends_at", None) is None:
            subscription.grace_ends_at = now
