"""Data structures shared by collectors, checks and report writers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: Status
    summary: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    schema_version: str
    opsprobe_version: str
    generated_at: str
    target: str | None
    system: dict[str, Any]
    checks: tuple[CheckResult, ...]
    privacy: dict[str, Any]

    @property
    def overall_status(self) -> Status:
        statuses = {check.status for check in self.checks}
        if Status.FAIL in statuses:
            return Status.FAIL
        if Status.WARN in statuses:
            return Status.WARN
        return Status.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "opsprobe_version": self.opsprobe_version,
            "generated_at": self.generated_at,
            "target": self.target,
            "overall_status": self.overall_status.value,
            "system": self.system,
            "checks": [check.to_dict() for check in self.checks],
            "privacy": self.privacy,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
