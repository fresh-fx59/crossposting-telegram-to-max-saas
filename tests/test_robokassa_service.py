"""Unit tests for Robokassa helper functions."""

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend/app/services/robokassa_service.py"
SPEC = importlib.util.spec_from_file_location("robokassa_service", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Failed to load robokassa_service module")
robokassa_service = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(robokassa_service)

compute_result_signature = robokassa_service.compute_result_signature
out_sum_to_minor = robokassa_service.out_sum_to_minor
verify_result_signature = robokassa_service.verify_result_signature


def test_out_sum_to_minor() -> None:
    assert out_sum_to_minor("123") == 12300
    assert out_sum_to_minor("123.45") == 12345
    assert out_sum_to_minor("0.009") == 1


def test_signature_with_shp_params() -> None:
    out_sum = "123.45"
    inv_id = "100500"
    password_2 = "secret2"
    shp = {"Shp_user_id": "42", "Shp_plan": "monthly"}

    signature = compute_result_signature(out_sum, inv_id, password_2, shp)
    assert verify_result_signature(out_sum, inv_id, signature.upper(), password_2, shp)
    assert not verify_result_signature(out_sum, inv_id, "bad", password_2, shp)
