"""Pydantic schemas for billing endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class SubscriptionStateResponse(BaseModel):
    """Current subscription state for a user."""

    user_id: int
    subscription_id: int | None = None
    plan_code: str | None = None
    status: str
    provider: str | None = None
    current_period_end: datetime | None = None
    grace_ends_at: datetime | None = None
    trial_ends_at: datetime | None = None


class OnboardingStartResponse(BaseModel):
    """Response for onboarding start command."""

    user_id: int
    status: str
    next_step: str
    trial_ends_at: datetime | None = None


class PlanInfo(BaseModel):
    """Plan entry for onboarding plans response."""

    plan_code: str
    title: str
    price_rub: int
    billing_period_days: int
    recommended: bool = False


class OnboardingPlansResponse(BaseModel):
    """List of available plans."""

    plans: list[PlanInfo]


class OnboardingPayRequest(BaseModel):
    """Request to generate payment link."""

    plan_code: str = Field(..., min_length=1, max_length=32)


class OnboardingPayResponse(BaseModel):
    """Generated payment link response."""

    plan_code: str
    inv_id: str
    amount_rub: int
    payment_url: str


class OnboardingStatusResponse(BaseModel):
    """User onboarding status for bot command /status."""

    user_id: int
    status: str
    can_publish: bool
    plan_code: str | None = None
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    checklist: list[str]
