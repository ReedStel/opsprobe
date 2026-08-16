"""Small, dependency-free system inventory collector."""

from __future__ import annotations

import ctypes
import getpass
import os
import platform
import socket
import sys
from pathlib import Path
from urllib.request import getproxies


def _memory_bytes() -> int | None:
    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            return None

    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_physical)
        return None

    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def collect_system_context(include_identifiers: bool = False) -> dict[str, object]:
    """Collect enough context for triage without inventorying the whole machine."""

    memory = _memory_bytes()
    context: dict[str, object] = {
        "operating_system": platform.system() or "Unknown",
        "os_release": platform.release() or "Unknown",
        "architecture": platform.machine() or "Unknown",
        "python_version": platform.python_version(),
        "logical_cpus": os.cpu_count(),
        "memory_gb": round(memory / (1024**3), 1) if memory else None,
        "proxy_schemes": sorted(getproxies().keys()),
    }

    if include_identifiers:
        context.update(
            {
                "hostname": socket.gethostname(),
                "username": getpass.getuser(),
                "home_directory": str(Path.home()),
            }
        )

    return context
