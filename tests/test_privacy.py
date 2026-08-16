from __future__ import annotations

import unittest

from opsprobe.privacy import sanitize_data, sanitize_text


class PrivacyTests(unittest.TestCase):
    def test_redacts_common_network_identifiers(self) -> None:
        text = "user@example.org used 192.168.10.24 from AA:BB:CC:DD:EE:FF"
        cleaned = sanitize_text(text)

        self.assertNotIn("user@example.org", cleaned)
        self.assertNotIn("192.168.10.24", cleaned)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", cleaned)
        self.assertIn("[redacted-email]", cleaned)
        self.assertIn("[redacted-ip]", cleaned)
        self.assertIn("[redacted-mac]", cleaned)

    def test_removes_credentials_from_urls(self) -> None:
        cleaned = sanitize_text("proxy=https://reed:secret@example.org:8443")
        self.assertEqual(cleaned, "proxy=https://[redacted]@example.org:8443")

    def test_recurses_through_report_data(self) -> None:
        cleaned = sanitize_data({"items": ["10.0.0.4", {"owner": "a@b.com"}], "count": 2})
        self.assertEqual(cleaned["items"][0], "[redacted-ip]")
        self.assertEqual(cleaned["items"][1]["owner"], "[redacted-email]")
        self.assertEqual(cleaned["count"], 2)


if __name__ == "__main__":
    unittest.main()
