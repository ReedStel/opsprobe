"""Best-effort redaction for reports that may be attached to support tickets."""

from __future__ import annotations

import getpass
import ipaddress
import os
import re
import socket
from pathlib import Path
from typing import Any


REDACTED = "[redacted]"

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
_IPV4 = re.compile(
    r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])"
)
_MAC = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
_CREDENTIAL_URL = re.compile(r"(?i)(https?://)([^\s/@:]+):([^\s/@]+)@")
_IPV6_CANDIDATE = re.compile(r"(?<![\w:])(?=[0-9A-Fa-f:]*:)[0-9A-Fa-f:]{2,}(?![\w:])")


def _known_identifiers() -> tuple[str, ...]:
    values = {
        str(Path.home()),
        os.environ.get("USERPROFILE", ""),
        os.environ.get("HOME", ""),
        getpass.getuser(),
        socket.gethostname(),
    }
    return tuple(sorted((value for value in values if len(value) >= 3), key=len, reverse=True))


def sanitize_text(value: str) -> str:
    """Remove common workstation identifiers without changing ordinary prose."""

    cleaned = value
    for identifier in _known_identifiers():
        cleaned = cleaned.replace(identifier, REDACTED)
    cleaned = _CREDENTIAL_URL.sub(r"\1[redacted]@", cleaned)
    cleaned = _EMAIL.sub("[redacted-email]", cleaned)
    cleaned = _MAC.sub("[redacted-mac]", cleaned)
    cleaned = _IPV4.sub("[redacted-ip]", cleaned)
    cleaned = _IPV6_CANDIDATE.sub(_redact_ipv6, cleaned)
    return cleaned


def _redact_ipv6(match: re.Match[str]) -> str:
    candidate = match.group(0)
    try:
        return "[redacted-ip]" if ipaddress.ip_address(candidate).version == 6 else candidate
    except ValueError:
        return candidate


def sanitize_data(value: Any) -> Any:
    """Recursively sanitize strings in JSON-compatible report data."""

    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {sanitize_text(str(key)): sanitize_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_data(item) for item in value)
    return value
