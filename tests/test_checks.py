from __future__ import annotations

import socket
import unittest
from collections import namedtuple
from unittest.mock import MagicMock, patch

from opsprobe.checks import check_disk, check_dns, check_https, check_tcp
from opsprobe.models import Status


DiskUsage = namedtuple("DiskUsage", "total used free")


class CheckTests(unittest.TestCase):
    @patch("opsprobe.checks.shutil.disk_usage")
    def test_disk_warns_below_fifteen_percent(self, disk_usage: MagicMock) -> None:
        disk_usage.return_value = DiskUsage(1000, 900, 100)
        result = check_disk("/")
        self.assertEqual(result.status, Status.WARN)
        self.assertEqual(result.details["free_percent"], 10.0)

    @patch("opsprobe.checks.shutil.disk_usage")
    def test_disk_fails_below_five_percent(self, disk_usage: MagicMock) -> None:
        disk_usage.return_value = DiskUsage(1000, 960, 40)
        result = check_disk("/")
        self.assertEqual(result.status, Status.FAIL)

    @patch("opsprobe.checks.socket.getaddrinfo")
    def test_dns_report_does_not_include_resolved_addresses(self, getaddrinfo: MagicMock) -> None:
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.5", 443))
        ]
        result = check_dns("example.com")
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.details["record_count"], 1)
        self.assertNotIn("203.0.113.5", str(result.details))

    @patch("opsprobe.checks.socket.create_connection")
    def test_tcp_uses_a_bounded_timeout(self, create_connection: MagicMock) -> None:
        create_connection.return_value.__enter__.return_value = object()
        result = check_tcp("example.com", timeout=1.25)
        self.assertEqual(result.status, Status.PASS)
        create_connection.assert_called_once_with(("example.com", 443), timeout=1.25)

    @patch("opsprobe.checks.urlopen")
    def test_https_keeps_certificate_verification_enabled(self, urlopen: MagicMock) -> None:
        response = urlopen.return_value.__enter__.return_value
        response.status = 204
        result = check_https("example.com")
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.details["tls_verification"], "enabled")
        self.assertIsNotNone(urlopen.call_args.kwargs["context"])


if __name__ == "__main__":
    unittest.main()
