from __future__ import annotations

import unittest

from opsprobe.models import CheckResult, DiagnosticReport, Status


def make_report(*statuses: Status) -> DiagnosticReport:
    checks = tuple(
        CheckResult(
            name=f"check-{index}",
            status=status,
            summary="done",
            duration_ms=1.0,
        )
        for index, status in enumerate(statuses)
    )
    return DiagnosticReport(
        schema_version="1.0",
        opsprobe_version="test",
        generated_at="2026-08-17T00:00:00+00:00",
        target=None,
        system={},
        checks=checks,
        privacy={},
    )


class DiagnosticReportTests(unittest.TestCase):
    def test_failure_has_highest_priority(self) -> None:
        report = make_report(Status.PASS, Status.WARN, Status.FAIL)
        self.assertEqual(report.overall_status, Status.FAIL)

    def test_warning_beats_pass_and_info(self) -> None:
        report = make_report(Status.INFO, Status.PASS, Status.WARN)
        self.assertEqual(report.overall_status, Status.WARN)

    def test_serialized_statuses_are_plain_strings(self) -> None:
        report = make_report(Status.PASS)
        data = report.to_dict()
        self.assertEqual(data["overall_status"], "pass")
        self.assertEqual(data["checks"][0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
