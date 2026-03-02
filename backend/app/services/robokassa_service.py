"""Robokassa signature helpers."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
from urllib.parse import urlencode


def out_sum_to_minor(out_sum: str) -> int:
    """Convert amount string to minor units (kopeks)."""
    try:
        amount = Decimal(out_sum)
    except InvalidOperation as exc:
        raise ValueError("Invalid OutSum") from exc
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute_result_signature(out_sum: str, inv_id: str, password_2: str, shp_params: dict[str, str]) -> str:
    """Compute ResultURL signature using Password #2."""
    base = f"{out_sum}:{inv_id}:{password_2}"
    if shp_params:
        for key in sorted(shp_params):
            base += f":{key}={shp_params[key]}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def verify_result_signature(
    out_sum: str,
    inv_id: str,
    signature_value: str,
    password_2: str,
    shp_params: dict[str, str],
) -> bool:
    """Verify signature from Robokassa ResultURL callback."""
    expected = compute_result_signature(out_sum, inv_id, password_2, shp_params)
    return expected.lower() == signature_value.strip().lower()


def compute_payment_signature(
    merchant_login: str,
    out_sum: str,
    inv_id: str,
    password_1: str,
    shp_params: dict[str, str],
) -> str:
    """Compute payment page signature using Password #1."""
    base = f"{merchant_login}:{out_sum}:{inv_id}:{password_1}"
    if shp_params:
        for key in sorted(shp_params):
            base += f":{key}={shp_params[key]}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def build_payment_url(
    *,
    payment_url: str,
    merchant_login: str,
    out_sum: str,
    inv_id: str,
    description: str,
    signature_value: str,
    is_test: bool,
    shp_params: dict[str, str],
) -> str:
    """Build Robokassa checkout URL."""
    params: dict[str, str] = {
        "MerchantLogin": merchant_login,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": description,
        "SignatureValue": signature_value,
    }
    if is_test:
        params["IsTest"] = "1"
    params.update(shp_params)
    return f"{payment_url}?{urlencode(params)}"
