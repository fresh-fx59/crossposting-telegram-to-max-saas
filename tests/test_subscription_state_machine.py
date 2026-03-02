"""Validation checks for billing subscription state machine."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend/app/services/subscription_state_machine.py"
SPEC = importlib.util.spec_from_file_location("subscription_state_machine", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Failed to load subscription_state_machine module")
state_machine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_machine)


def _expect_transition_error(current: str, nxt: str) -> None:
    try:
        state_machine.ensure_valid_transition(current, nxt)
    except ValueError:
        return
    raise AssertionError(f"Expected invalid transition error: {current} -> {nxt}")


def run_checks() -> None:
    state_machine.ensure_valid_transition("trial", "active")
    state_machine.ensure_valid_transition("active", "grace")
    state_machine.ensure_valid_transition("grace", "expired")
    state_machine.ensure_valid_transition("cancelled", "active")
    state_machine.ensure_valid_transition("none", "active")

    _expect_transition_error("trial", "trial")
    _expect_transition_error("expired", "grace")
    _expect_transition_error("past_due", "trial")

    sub = SimpleNamespace(
        status="trial",
        current_period_start=None,
        current_period_end=None,
        grace_ends_at=None,
        cancelled_at=None,
    )
    state_machine.apply_status_fields(sub, "active")
    assert sub.status == "active"
    assert sub.current_period_start is not None
    assert sub.current_period_end is not None

    state_machine.apply_status_fields(sub, "grace")
    assert sub.grace_ends_at is not None

    state_machine.apply_status_fields(sub, "cancelled")
    assert sub.cancelled_at is not None


if __name__ == "__main__":
    run_checks()
    print("subscription_state_machine_validation_ok")

