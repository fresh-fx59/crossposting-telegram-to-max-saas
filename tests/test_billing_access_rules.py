"""Validation checks for billing access control rules."""

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend/app/services/billing_access.py"
SPEC = importlib.util.spec_from_file_location("billing_service", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Failed to load billing_access module")
billing_access = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(billing_access)


def run_checks() -> None:
    assert billing_access.can_publish_with_billing_status("active")
    assert billing_access.can_publish_with_billing_status("grace")
    assert not billing_access.can_publish_with_billing_status("trial")
    assert not billing_access.can_publish_with_billing_status("past_due")
    assert not billing_access.can_publish_with_billing_status("expired")
    assert not billing_access.can_publish_with_billing_status("cancelled")
    assert not billing_access.can_publish_with_billing_status(None)


if __name__ == "__main__":
    run_checks()
    print("billing_access_rules_validation_ok")
