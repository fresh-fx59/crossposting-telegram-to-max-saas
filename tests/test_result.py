"""Test result and suite classes."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0
    error: str | None = None


@dataclass
class TestSuite:
    """Test suite for running multiple tests."""
    name: str
    tests: list[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult):
        self.tests.append(result)

    def summary(self) -> dict[str, Any]:
        passed = sum(1 for t in self.tests if t.passed)
        return {
            "name": self.name,
            "total": len(self.tests),
            "passed": passed,
            "failed": len(self.tests) - passed,
        }

    def print_summary(self):
        """Print human-readable test summary."""
        print("\n" + "=" * 70)
        print(f"  TEST SUITE: {self.name}")
        print("=" * 70)

        for i, test in enumerate(self.tests, 1):
            status = "✓ PASS" if test.passed else "✗ FAIL"
            print(f"\n{i}. {test.name}")
            print(f"   Status: {status}")
            print(f"   Message: {test.message}")
            print(f"   Duration: {test.duration_ms:.2f}ms")
            if test.error:
                print(f"   Error: {test.error}")

        summary = self.summary()
        print("\n" + "-" * 70)
        print(f"  SUMMARY: {summary['passed']}/{summary['total']} tests passed")
        print("=" * 70 + "\n")