"""Tests for core.proxy_manager — proxy parsing, formatting and rotation logic."""
import pytest

from config.settings import Config
from core.proxy_manager import ProxyManager


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """ProxyManager isolated from the real proxies.txt via a temp proxy file."""
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text(
        "# comment line\n"
        "10.0.0.1:8080\n"
        "user1:pw1@10.0.0.2:3128\n"
        "\n"
    )
    monkeypatch.setattr(Config, "PROXY_FILE", str(proxy_file))
    return ProxyManager()


class TestParse:
    @pytest.mark.parametrize("raw,expected", [
        # host:port
        ("1.2.3.4:8080", {"host": "1.2.3.4", "port": 8080, "user": None, "pass": None, "protocol": "http"}),
        # host:port:user:pass (legacy)
        ("1.2.3.4:8080:bob:s3cret", {"host": "1.2.3.4", "port": 8080, "user": "bob", "pass": "s3cret", "protocol": "http"}),
        # user:pass@host:port
        ("bob:s3cret@1.2.3.4:8080", {"host": "1.2.3.4", "port": 8080, "user": "bob", "pass": "s3cret", "protocol": "http"}),
        # protocol://host:port
        ("socks5://1.2.3.4:1080", {"host": "1.2.3.4", "port": 1080, "user": None, "pass": None, "protocol": "socks5"}),
        # protocol://user:pass@host:port  (the documented format that used to fail)
        ("http://bob:s3cret@proxy.example.com:3128",
         {"host": "proxy.example.com", "port": 3128, "user": "bob", "pass": "s3cret", "protocol": "http"}),
        # surrounding whitespace is tolerated
        ("  1.2.3.4:8080  ", {"host": "1.2.3.4", "port": 8080, "user": None, "pass": None, "protocol": "http"}),
    ])
    def test_supported_formats(self, raw, expected):
        assert ProxyManager.parse(raw) == expected

    @pytest.mark.parametrize("raw", [
        None,
        "",
        "no-port-here",
        "1.2.3.4:notaport",
        "1.2.3.4:99999",
        "ftp://1.2.3.4:8080",       # unsupported scheme
        "user@1.2.3.4:8080:extra",  # malformed leftovers
    ])
    def test_invalid_inputs_return_none(self, raw):
        assert ProxyManager.parse(raw) is None

    def test_password_containing_colon(self):
        parsed = ProxyManager.parse("bob:pa:ss@1.2.3.4:8080")
        assert parsed["user"] == "bob"
        assert parsed["pass"] == "pa:ss"


class TestFormatForPlaywright:
    def test_without_auth(self):
        assert ProxyManager.format_for_playwright("1.2.3.4:8080") == {
            "server": "http://1.2.3.4:8080"
        }

    def test_with_auth(self):
        result = ProxyManager.format_for_playwright("http://bob:s3cret@1.2.3.4:8080")
        assert result == {
            "server": "http://1.2.3.4:8080",
            "username": "bob",
            "password": "s3cret",
        }

    def test_socks5_protocol_preserved(self):
        result = ProxyManager.format_for_playwright("socks5://1.2.3.4:1080")
        assert result["server"] == "socks5://1.2.3.4:1080"

    def test_invalid_returns_none(self):
        assert ProxyManager.format_for_playwright("garbage") is None


class TestFormatForSelenium:
    def test_without_auth(self):
        assert ProxyManager.format_for_selenium("1.2.3.4:8080") == "1.2.3.4:8080"

    def test_with_auth(self):
        assert ProxyManager.format_for_selenium(
            "bob:s3cret@1.2.3.4:8080", proxy_type="socks5"
        ) == "socks5://bob:s3cret@1.2.3.4:8080"


class TestRotationAndHealth:
    def test_loads_file_skipping_comments_and_blanks(self, manager):
        assert manager.count == 2
        assert set(manager.get_all_proxies()) == {"10.0.0.1:8080", "user1:pw1@10.0.0.2:3128"}

    def test_get_next_rotates_round_robin(self, manager):
        first = manager.get_next()
        second = manager.get_next()
        assert first != second
        assert manager.get_next() == first  # wraps around

    def test_get_random_returns_loaded_proxy(self, manager):
        assert manager.get_random() in manager.get_all_proxies()

    def test_empty_manager_returns_none(self, tmp_path, monkeypatch):
        proxy_file = tmp_path / "empty.txt"
        proxy_file.write_text("# only comments\n\n")
        monkeypatch.setattr(Config, "PROXY_FILE", str(proxy_file))
        pm = ProxyManager()
        assert pm.get_next() is None
        assert pm.get_random() is None
        assert pm.get_best() is None

    def test_mark_failure_drops_below_threshold(self, manager):
        proxy = manager.get_all_proxies()[0]
        for _ in range(5):
            manager.mark_failure(proxy, fatal=True)  # 50 -> 0
        assert manager._health[proxy] is False
        stats = manager.get_stats()
        assert stats["unhealthy"] == 1
        assert stats["healthy"] == 1  # the other proxy is untouched

    def test_mark_success_restores_score(self, manager):
        proxy = manager.get_all_proxies()[0]
        manager.mark_failure(proxy, fatal=True)   # 50 - 30 = 20
        manager.mark_success(proxy)               # 20 + 10 = 30
        assert manager._scores[proxy] == 30

    def test_unhealthy_proxies_are_skipped(self, manager):
        proxies = manager.get_all_proxies()
        for _ in range(5):
            manager.mark_failure(proxies[0], fatal=True)
        # round-robin over the remaining healthy pool must never pick the dead one
        for _ in range(4):
            assert manager.get_next() == proxies[1]
