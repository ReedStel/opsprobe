"""Bounded health and connectivity checks used by the default diagnostic profile."""

from __future__ import annotations

import os
import shutil
import socket
import ssl
import sys
from pathlib import Path
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import CheckResult, Status


def _elapsed(started: float) -> float:
    return round((monotonic() - started) * 1000, 1)


def check_disk(path: str | os.PathLike[str] | None = None) -> CheckResult:
    started = monotonic()
    disk_path = Path(path) if path else Path.home().anchor or os.path.sep

    try:
        usage = shutil.disk_usage(disk_path)
    except OSError as exc:
        return CheckResult(
            name="Disk headroom",
            status=Status.FAIL,
            summary="Disk usage could not be read.",
            duration_ms=_elapsed(started),
            details={"error": str(exc)},
            suggestion="Confirm the volume is mounted and readable, then run the check again.",
        )

    free_percent = (usage.free / usage.total * 100) if usage.total else 0
    if free_percent < 5:
        status = Status.FAIL
        summary = "Free disk space is critically low."
        suggestion = "Free space before installing updates or collecting large logs."
    elif free_percent < 15:
        status = Status.WARN
        summary = "Free disk space is below the recommended buffer."
        suggestion = "Review downloads, temporary files and stale application data."
    else:
        status = Status.PASS
        summary = "Disk space has a healthy buffer."
        suggestion = None

    return CheckResult(
        name="Disk headroom",
        status=status,
        summary=summary,
        duration_ms=_elapsed(started),
        details={
            "total_gb": round(usage.total / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "free_percent": round(free_percent, 1),
        },
        suggestion=suggestion,
    )


def check_loopback() -> CheckResult:
    started = monotonic()
    try:
        records = socket.getaddrinfo("localhost", None)
        families = sorted({socket.AddressFamily(item[0]).name for item in records})
        return CheckResult(
            name="Local TCP/IP stack",
            status=Status.PASS,
            summary="The local hostname resolves correctly.",
            duration_ms=_elapsed(started),
            details={"address_families": families},
        )
    except OSError as exc:
        return CheckResult(
            name="Local TCP/IP stack",
            status=Status.FAIL,
            summary="The local hostname did not resolve.",
            duration_ms=_elapsed(started),
            details={"error": str(exc)},
            suggestion="Check the hosts file and local resolver configuration.",
        )


def check_runtime() -> CheckResult:
    started = monotonic()
    supported = sys.version_info >= (3, 11)
    return CheckResult(
        name="Runtime",
        status=Status.PASS if supported else Status.WARN,
        summary=(
            "Python runtime is supported." if supported else "Python 3.11 or newer is recommended."
        ),
        duration_ms=_elapsed(started),
        details={"python": ".".join(map(str, sys.version_info[:3]))},
        suggestion=(
            None if supported else "Install a supported Python release before relying on reports."
        ),
    )


def check_dns(target: str) -> CheckResult:
    started = monotonic()
    try:
        records = socket.getaddrinfo(target, 443, type=socket.SOCK_STREAM)
        families = sorted({socket.AddressFamily(item[0]).name for item in records})
        return CheckResult(
            name="DNS resolution",
            status=Status.PASS,
            summary=f"{target} resolved successfully.",
            duration_ms=_elapsed(started),
            details={"record_count": len(records), "address_families": families},
        )
    except socket.gaierror as exc:
        return CheckResult(
            name="DNS resolution",
            status=Status.FAIL,
            summary=f"{target} could not be resolved.",
            duration_ms=_elapsed(started),
            details={"error": str(exc)},
            suggestion="Check the active adapter, DNS server assignment and captive portal state.",
        )


def check_tcp(target: str, port: int = 443, timeout: float = 3.0) -> CheckResult:
    started = monotonic()
    try:
        with socket.create_connection((target, port), timeout=timeout):
            pass
        return CheckResult(
            name="TCP connectivity",
            status=Status.PASS,
            summary=f"A TCP connection to {target}:{port} succeeded.",
            duration_ms=_elapsed(started),
            details={"port": port, "timeout_seconds": timeout},
        )
    except OSError as exc:
        return CheckResult(
            name="TCP connectivity",
            status=Status.FAIL,
            summary=f"A TCP connection to {target}:{port} failed.",
            duration_ms=_elapsed(started),
            details={"port": port, "error": str(exc)},
            suggestion=(
                "Check routing, firewall policy, proxy requirements and upstream availability."
            ),
        )


def check_https(target: str, timeout: float = 4.0) -> CheckResult:
    started = monotonic()
    url = f"https://{target}/"
    request = Request(url, method="HEAD", headers={"User-Agent": "OpsProbe/0.1"})
    context = ssl.create_default_context()

    try:
        with urlopen(request, timeout=timeout, context=context) as response:
            status_code = response.status
        status = Status.PASS if status_code < 400 else Status.WARN
        return CheckResult(
            name="HTTPS request",
            status=status,
            summary=f"TLS negotiation completed with HTTP {status_code}.",
            duration_ms=_elapsed(started),
            details={"status_code": status_code, "tls_verification": "enabled"},
            suggestion=(
                None
                if status is Status.PASS
                else "Confirm whether the response is expected for this host."
            ),
        )
    except HTTPError as exc:
        return CheckResult(
            name="HTTPS request",
            status=Status.WARN,
            summary=f"TLS succeeded, but the server returned HTTP {exc.code}.",
            duration_ms=_elapsed(started),
            details={"status_code": exc.code, "tls_verification": "enabled"},
            suggestion="Confirm whether authentication or a different path is required.",
        )
    except (URLError, OSError, ssl.SSLError) as exc:
        reason = getattr(exc, "reason", exc)
        return CheckResult(
            name="HTTPS request",
            status=Status.FAIL,
            summary="The verified HTTPS request failed.",
            duration_ms=_elapsed(started),
            details={"error": str(reason), "tls_verification": "enabled"},
            suggestion="Check system time, certificate trust, proxy settings and network access.",
        )
