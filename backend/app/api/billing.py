"""Billing API routes."""

import logging
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_async_session
from ..database.models import PaymentTransaction, User
from ..schemas.billing import (
    OnboardingPayRequest,
    OnboardingPayResponse,
    OnboardingPlansResponse,
    OnboardingStartResponse,
    OnboardingStatusResponse,
    PlanInfo,
    SubscriptionStateResponse,
)
from ..services.billing_access import can_publish_with_billing_status
from ..services.billing_service import get_current_subscription, transition_subscription
from ..services.robokassa_service import (
    build_payment_url,
    compute_payment_signature,
    out_sum_to_minor,
    verify_result_signature,
)
from .deps import CurrentUser

router = APIRouter()
logger = logging.getLogger(__name__)

PLAN_CATALOG = {
    "monthly": {"title": "Monthly", "price_rub": 990, "billing_period_days": 30, "recommended": True},
    "annual": {"title": "Annual", "price_rub": 9990, "billing_period_days": 365, "recommended": False},
}


@router.get("/subscription/current", response_model=SubscriptionStateResponse)
async def get_current_subscription_state(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> SubscriptionStateResponse:
    """Return current subscription status for the authenticated user."""
    current = await get_current_subscription(session, current_user.id)
    if current is None:
        return SubscriptionStateResponse(user_id=current_user.id, status="none")

    return SubscriptionStateResponse(
        user_id=current_user.id,
        subscription_id=current.id,
        plan_code=current.plan_code,
        status=current.status,
        provider=current.provider,
        current_period_end=current.current_period_end,
        grace_ends_at=current.grace_ends_at,
        trial_ends_at=current.trial_ends_at,
    )


@router.post("/onboarding/start", response_model=OnboardingStartResponse)
async def onboarding_start(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OnboardingStartResponse:
    """Initialize onboarding and ensure trial subscription exists."""
    current = await get_current_subscription(session, current_user.id)
    if current is None:
        current = await transition_subscription(
            session,
            user_id=current_user.id,
            next_status="trial",
            event_type="onboarding_started",
            provider_event_id=f"onboarding:{current_user.id}:{int(time())}",
            payload_json='{"source":"bot_start"}',
            plan_code="trial",
        )
        await session.commit()

    return OnboardingStartResponse(
        user_id=current_user.id,
        status=current.status,
        next_step="/plans",
        trial_ends_at=current.trial_ends_at,
    )


@router.get("/onboarding/plans", response_model=OnboardingPlansResponse)
async def onboarding_plans() -> OnboardingPlansResponse:
    """Return available plans for /plans command."""
    plans = [
        PlanInfo(plan_code=code, **data) for code, data in PLAN_CATALOG.items()
    ]
    return OnboardingPlansResponse(plans=plans)


@router.post("/onboarding/pay", response_model=OnboardingPayResponse)
async def onboarding_pay(
    data: OnboardingPayRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OnboardingPayResponse:
    """Generate a payment URL for /pay command."""
    plan = PLAN_CATALOG.get(data.plan_code)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown plan code")
    if not settings.ROBOKASSA_MERCHANT_LOGIN or not settings.ROBOKASSA_PASSWORD_1:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Robokassa is not configured")

    inv_id = f"{current_user.id}{int(time())}"
    out_sum = f"{plan['price_rub']:.2f}"
    shp_params = {
        "Shp_user_id": str(current_user.id),
        "Shp_plan": data.plan_code,
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

    current = await get_current_subscription(session, current_user.id)
    tx = PaymentTransaction(
        user_id=current_user.id,
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

    return OnboardingPayResponse(
        plan_code=data.plan_code,
        inv_id=inv_id,
        amount_rub=plan["price_rub"],
        payment_url=payment_url,
    )


@router.get("/onboarding/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OnboardingStatusResponse:
    """Return onboarding and billing status for /status command."""
    current = await get_current_subscription(session, current_user.id)
    status_value = current.status if current else "none"
    checklist = [
        "Connect Telegram bot and channel",
        "Connect Max channel",
        "Create Telegram->Max connection",
        "Send first test post",
    ]
    return OnboardingStatusResponse(
        user_id=current_user.id,
        status=status_value,
        can_publish=can_publish_with_billing_status(status_value),
        plan_code=current.plan_code if current else None,
        trial_ends_at=current.trial_ends_at if current else None,
        current_period_end=current.current_period_end if current else None,
        checklist=checklist,
    )


@router.post("/webhook/robokassa", response_class=PlainTextResponse)
async def robokassa_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PlainTextResponse:
    """Handle Robokassa payment notifications with idempotency."""
    payload: dict[str, str] = {k: v for k, v in request.query_params.items()}
    try:
        form = await request.form()
        payload.update({k: str(v) for k, v in form.items()})
    except Exception:
        pass

    out_sum = payload.get("OutSum", "")
    inv_id = payload.get("InvId", "")
    signature_value = payload.get("SignatureValue", "")
    shp_params = {k: v for k, v in payload.items() if k.startswith("Shp_")}

    if not out_sum or not inv_id or not signature_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required webhook fields")
    if not settings.ROBOKASSA_PASSWORD_2:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Robokassa secret is not set")

    if not verify_result_signature(out_sum, inv_id, signature_value, settings.ROBOKASSA_PASSWORD_2, shp_params):
        logger.warning("billing.webhook.robokassa.invalid_signature inv_id=%s", inv_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    user_id_raw = shp_params.get("Shp_user_id", "")
    if not user_id_raw.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shp_user_id is required")
    user_id = int(user_id_raw)

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown user")

    amount_minor = out_sum_to_minor(out_sum)
    tx_result = await session.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.provider == "robokassa",
            PaymentTransaction.provider_payment_id == inv_id,
        )
    )
    transaction = tx_result.scalar_one_or_none()

    if transaction and transaction.status == "paid":
        logger.info("billing.webhook.robokassa.duplicate inv_id=%s user_id=%s", inv_id, user_id)
        return PlainTextResponse(content=f"OK{inv_id}", status_code=status.HTTP_200_OK)

    plan_code = shp_params.get("Shp_plan", "monthly")

    if transaction is None:
        transaction = PaymentTransaction(
            user_id=user_id,
            provider="robokassa",
            provider_payment_id=inv_id,
            status="paid",
            amount_minor=amount_minor,
            currency="RUB",
            raw_payload=str(payload),
        )
        session.add(transaction)
    else:
        transaction.status = "paid"
        transaction.amount_minor = amount_minor
        transaction.raw_payload = str(payload)

    try:
        subscription = await transition_subscription(
            session,
            user_id=user_id,
            next_status="active",
            event_type="payment_succeeded",
            provider_event_id=f"robokassa:{inv_id}",
            transaction=transaction,
            payload_json=str(payload),
            plan_code=plan_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    transaction.subscription_id = subscription.id
    await session.commit()

    logger.info("billing.webhook.robokassa.processed inv_id=%s user_id=%s", inv_id, user_id)
    return PlainTextResponse(content=f"OK{inv_id}", status_code=status.HTTP_200_OK)
