"""Diagnostic profile orchestration."""

from __future__ import annotations

import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from . import __version__
from .checks import check_disk, check_dns, check_https, check_loopback, check_runtime, check_tcp
from .models import CheckResult, DiagnosticReport, Status, utc_now
from .system_info import collect_system_context


_HOST_LABEL = re.compile(r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")


def validate_target(value: str) -> str:
    """Accept a hostname or IP address, but not a URL, path or port range."""

    target = value.strip().rstrip(".")
    if not target or len(target) > 253:
        raise ValueError("target must be a hostname or IP address")
    if any(character in target for character in "/:@?#"):
        raise ValueError("use a hostname only, without a URL, path or port")

    try:
        ipaddress.ip_address(target)
        return target
    except ValueError:
        pass

    try:
        ascii_target = target.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("target is not a valid hostname") from exc

    if not all(_HOST_LABEL.fullmatch(label) for label in ascii_target.split(".")):
        raise ValueError("target is not a valid hostname")
    return ascii_target.lower()


def _guarded(name: str, task: Callable[[], CheckResult]) -> CheckResult:
    """Keep one unexpected collector error from discarding the whole report."""

    try:
        return task()
    except Exception as exc:  # The CLI boundary should return a usable partial report.
        return CheckResult(
            name=name,
            status=Status.FAIL,
            summary="The check stopped because of an unexpected local error.",
            duration_ms=0.0,
            details={"error_type": type(exc).__name__, "error": str(exc)},
            suggestion="Run the check again; if it repeats, attach a redacted report to an issue.",
        )


def run_diagnostics(
    *,
    target: str = "example.com",
    timeout: float = 3.0,
    offline: bool = False,
    include_identifiers: bool = False,
    disk_path: str | None = None,
) -> DiagnosticReport:
    if not 0.2 <= timeout <= 30:
        raise ValueError("timeout must be between 0.2 and 30 seconds")

    checked_target = None if offline else validate_target(target)
    tasks: list[tuple[str, Callable[[], CheckResult]]] = [
        ("Disk headroom", lambda: check_disk(disk_path)),
        ("Local TCP/IP stack", check_loopback),
        ("Runtime", check_runtime),
    ]
    if checked_target:
        tasks.extend(
            [
                ("DNS resolution", lambda: check_dns(checked_target)),
                ("TCP connectivity", lambda: check_tcp(checked_target, timeout=timeout)),
                (
                    "HTTPS request",
                    lambda: check_https(checked_target, timeout=min(timeout + 1, 30)),
                ),
            ]
        )

    with ThreadPoolExecutor(max_workers=min(6, len(tasks)), thread_name_prefix="opsprobe") as pool:
        results = tuple(pool.map(lambda named: _guarded(*named), tasks))

    return DiagnosticReport(
        schema_version="1.0",
        opsprobe_version=__version__,
        generated_at=utc_now(),
        target=checked_target,
        system=collect_system_context(include_identifiers=include_identifiers),
        checks=results,
        privacy={
            "identifiers_included": include_identifiers,
            "default_redaction": not include_identifiers,
            "sharing_note": (
                "Review exported files before sharing; redaction is best-effort, not a guarantee."
            ),
        },
    )
