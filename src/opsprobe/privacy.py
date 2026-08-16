"""Best-effort redaction for reports that may be attached to support tickets."""

from __future__ import annotations

import getpass
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
    return cleaned


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
