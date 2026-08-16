from __future__ import annotations

import json
import unittest

from opsprobe.models import CheckResult, DiagnosticReport, Status
from opsprobe.reporting import render_html, render_json, render_markdown


def report_with(value: str) -> DiagnosticReport:
    return DiagnosticReport(
        schema_version="1.0",
        opsprobe_version="test",
        generated_at="2026-08-17T00:00:00+00:00",
        target="example.com",
        system={"hostname": value},
        checks=(CheckResult("DNS <check>", Status.PASS, value, 2.5),),
        privacy={"sharing_note": "Review before sharing."},
    )


class ReportingTests(unittest.TestCase):
    def test_json_is_valid_and_redacted(self) -> None:
        output = render_json(report_with("host 192.168.1.8"))
        data = json.loads(output)
        self.assertEqual(data["system"]["hostname"], "host [redacted-ip]")

    def test_html_escapes_report_content(self) -> None:
        output = render_html(report_with("<script>alert(1)</script>"), sanitize=False)
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", output)

    def test_markdown_contains_next_step_when_present(self) -> None:
        report = report_with("safe")
        check = CheckResult("Disk", Status.WARN, "low", 1.0, suggestion="Free space.")
        updated = DiagnosticReport(
            report.schema_version,
            report.opsprobe_version,
            report.generated_at,
            report.target,
            report.system,
            (check,),
            report.privacy,
        )
        self.assertIn("Next step: Free space.", render_markdown(updated))


if __name__ == "__main__":
    unittest.main()
