"""Validation checks for onboarding payment URL generation helpers."""

import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend/app/services/robokassa_service.py"
SPEC = importlib.util.spec_from_file_location("robokassa_service", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Failed to load robokassa_service module")
robokassa_service = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(robokassa_service)


def run_checks() -> None:
    merchant_login = "crossposter"
    out_sum = "990.00"
    inv_id = "42123456"
    password_1 = "password1"
    shp = {"Shp_user_id": "42", "Shp_plan": "monthly"}

    signature = robokassa_service.compute_payment_signature(
        merchant_login, out_sum, inv_id, password_1, shp
    )
    payment_url = robokassa_service.build_payment_url(
        payment_url="https://auth.robokassa.ru/Merchant/Index.aspx",
        merchant_login=merchant_login,
        out_sum=out_sum,
        inv_id=inv_id,
        description="Crossposter Monthly subscription",
        signature_value=signature,
        is_test=True,
        shp_params=shp,
    )
    query = parse_qs(urlparse(payment_url).query)
    assert query["MerchantLogin"][0] == merchant_login
    assert query["OutSum"][0] == out_sum
    assert query["InvId"][0] == inv_id
    assert query["Shp_user_id"][0] == "42"
    assert query["Shp_plan"][0] == "monthly"
    assert query["IsTest"][0] == "1"


if __name__ == "__main__":
    run_checks()
    print("onboarding_payment_link_validation_ok")

