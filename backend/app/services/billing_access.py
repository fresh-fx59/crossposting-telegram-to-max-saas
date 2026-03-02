"""Billing access rules used by posting guards."""

PUBLISH_ALLOWED_STATUSES = {"active", "grace"}


def can_publish_with_billing_status(subscription_status: str | None) -> bool:
    """Return whether posting is allowed for the given billing status."""
    return (subscription_status or "none") in PUBLISH_ALLOWED_STATUSES

