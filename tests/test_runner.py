from __future__ import annotations

import unittest
from unittest.mock import patch

from opsprobe.models import CheckResult, Status
from opsprobe.runner import _guarded, run_diagnostics, validate_target


PASS = CheckResult("test", Status.PASS, "ok", 0.1)


class TargetValidationTests(unittest.TestCase):
    def test_accepts_hostname_and_ip(self) -> None:
        self.assertEqual(validate_target("Example.COM."), "example.com")
        self.assertEqual(validate_target("1.1.1.1"), "1.1.1.1")

    def test_rejects_urls_paths_and_ports(self) -> None:
        for target in ("https://example.com", "example.com/path", "example.com:443", ""):
            with self.subTest(target=target), self.assertRaises(ValueError):
                validate_target(target)


class RunnerTests(unittest.TestCase):
    def test_unexpected_check_error_becomes_a_failed_result(self) -> None:
        def broken_check() -> CheckResult:
            raise RuntimeError("collector broke")

        result = _guarded("Example check", broken_check)
        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(result.name, "Example check")
        self.assertEqual(result.details["error_type"], "RuntimeError")

    @patch("opsprobe.runner.collect_system_context", return_value={"os": "TestOS"})
    @patch("opsprobe.runner.check_runtime", return_value=PASS)
    @patch("opsprobe.runner.check_loopback", return_value=PASS)
    @patch("opsprobe.runner.check_disk", return_value=PASS)
    def test_offline_profile_runs_only_local_checks(
        self,
        _disk: object,
        _loopback: object,
        _runtime: object,
        _system: object,
    ) -> None:
        report = run_diagnostics(offline=True)
        self.assertIsNone(report.target)
        self.assertEqual(len(report.checks), 3)
        self.assertFalse(report.privacy["identifiers_included"])


if __name__ == "__main__":
    unittest.main()
