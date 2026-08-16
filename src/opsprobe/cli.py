"""Command-line interface for the default diagnostic profile."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from . import __version__
from .models import DiagnosticReport, Status
from .reporting import render_html, render_json, render_markdown, write_report
from .runner import run_diagnostics


COLOURS = {
    Status.PASS: "\033[32m",
    Status.WARN: "\033[33m",
    Status.FAIL: "\033[31m",
    Status.INFO: "\033[36m",
}
RESET = "\033[0m"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opsprobe",
        description="Run a bounded workstation and network triage profile.",
    )
    parser.add_argument("--version", action="version", version=f"OpsProbe {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="run the diagnostic profile")
    doctor.add_argument(
        "--target", default="example.com", help="hostname or IP used for network checks"
    )
    doctor.add_argument(
        "--timeout", type=float, default=3.0, help="network timeout in seconds (0.2–30)"
    )
    doctor.add_argument("--offline", action="store_true", help="skip all external network checks")
    doctor.add_argument("--json", metavar="PATH", help="write a redacted JSON report")
    doctor.add_argument(
        "--markdown", metavar="PATH", help="write a ticket-friendly Markdown report"
    )
    doctor.add_argument("--html", metavar="PATH", help="write a self-contained HTML report")
    doctor.add_argument(
        "--include-identifiers",
        action="store_true",
        help="include hostname, username and home path in exports",
    )
    doctor.add_argument(
        "--strict", action="store_true", help="return a non-zero exit code for warnings"
    )
    doctor.add_argument("--no-colour", action="store_true", help="disable ANSI terminal colours")

    subparsers.add_parser("explain-data", help="show what OpsProbe collects and omits")
    return parser


def _print_report(report: DiagnosticReport, *, colour: bool) -> None:
    print(f"\nOpsProbe {report.opsprobe_version}  ·  {report.generated_at}")
    print("─" * 68)
    for check in report.checks:
        label = check.status.value.upper().ljust(4)
        if colour:
            label = f"{COLOURS[check.status]}{label}{RESET}"
        print(f"{label}  {check.name:<22} {check.summary} ({check.duration_ms:.1f} ms)")
        if check.suggestion:
            print(f"      Next: {check.suggestion}")
    print("─" * 68)
    print(f"Overall: {report.overall_status.value.upper()}\n")


def _explain_data() -> None:
    print(
        """OpsProbe collects:
  - operating system, release, architecture and Python version
  - logical CPU count, total memory and configured proxy scheme names
  - disk capacity and free-space percentage
  - DNS, TCP 443 and verified HTTPS outcomes for one chosen target

By default it omits:
  - hostname, username and home-directory path
  - resolved IP addresses, MAC addresses, file listings and environment values
  - browser history, credentials, document contents and installed applications

Exports receive a second best-effort redaction pass. Always review a report before sharing it.
"""
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        arguments = ["doctor"]

    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.command == "explain-data":
        _explain_data()
        return 0
    if args.command != "doctor":
        parser.print_help()
        return 2

    try:
        report = run_diagnostics(
            target=args.target,
            timeout=args.timeout,
            offline=args.offline,
            include_identifiers=args.include_identifiers,
        )
    except ValueError as exc:
        parser.error(str(exc))

    colour = sys.stdout.isatty() and not args.no_colour and "NO_COLOR" not in os.environ
    _print_report(report, colour=colour)
    sanitize = not args.include_identifiers
    if args.json:
        print(f"JSON report: {write_report(args.json, render_json(report, sanitize=sanitize))}")
    if args.markdown:
        content = render_markdown(report, sanitize=sanitize)
        print(f"Markdown report: {write_report(args.markdown, content)}")
    if args.html:
        print(f"HTML report: {write_report(args.html, render_html(report, sanitize=sanitize))}")

    if report.overall_status is Status.FAIL:
        return 1
    if args.strict and report.overall_status is Status.WARN:
        return 1
    return 0
