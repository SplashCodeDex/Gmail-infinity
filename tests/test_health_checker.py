"""Tests for core.health_checker — IMAP status mapping and summary math."""
import imaplib
from unittest.mock import MagicMock, patch

from core.health_checker import AccountHealthChecker


def check_with_error(side_effect):
    with patch("core.health_checker.imaplib.IMAP4_SSL", side_effect=side_effect):
        return AccountHealthChecker.check_single("user@gmail.com", "pw")


class TestCheckSingle:
    def test_active_login(self):
        mail = MagicMock()
        with patch("core.health_checker.imaplib.IMAP4_SSL", return_value=mail):
            result = AccountHealthChecker.check_single("user@gmail.com", "pw")
        assert result["status"] == "active"
        mail.login.assert_called_once_with("user@gmail.com", "pw")

    def test_invalid_credentials(self):
        result = check_with_error(imaplib.IMAP4.error("Invalid credentials"))
        assert result["status"] == "password_changed"

    def test_locked_requires_web_login(self):
        result = check_with_error(imaplib.IMAP4.error("Web login required"))
        assert result["status"] == "locked"

    def test_suspended(self):
        result = check_with_error(imaplib.IMAP4.error("Account disabled by Google"))
        assert result["status"] == "suspended"

    def test_connection_error(self):
        result = check_with_error(ConnectionError("refused"))
        assert result["status"] == "network_error"

    def test_generic_error(self):
        result = check_with_error(imaplib.IMAP4.error("UNAUTHENTICATE blarg"))
        assert result["status"] == "error"

    def test_result_has_timestamp_and_email(self):
        result = check_with_error(ConnectionError())
        assert result["email"] == "user@gmail.com"
        assert result["checked_at"]


class TestGetSummary:
    def test_summary_math(self):
        results = [
            {"status": "active"},
            {"status": "active"},
            {"status": "locked"},
            {"status": "suspended"},
            {"status": "password_changed"},
            {"status": "error"},
            {"status": "network_error"},
        ]
        s = AccountHealthChecker.get_summary(results)
        assert s["total"] == 7
        assert s["active"] == 2
        assert s["locked"] == 1
        assert s["suspended"] == 1
        assert s["password_changed"] == 1
        assert s["errors"] == 2
        assert s["health_rate"] == 2 / 7 * 100

    def test_empty_summary_is_zero_safe(self):
        s = AccountHealthChecker.get_summary([])
        assert s["total"] == 0
        assert s["health_rate"] == 0
