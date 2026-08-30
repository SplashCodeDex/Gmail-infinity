"""
Tests for api.main — FastAPI endpoints, auth middleware, session lifecycle, export, and diagnostics.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app, active_sessions
from core.account_manager import account_manager
from core.database import DatabaseManager


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = DatabaseManager(str(tmp_path / "api_test.db"))
    monkeypatch.setattr(account_manager, "db", test_db)
    active_sessions.clear()
    return TestClient(app)


class TestApiGeneralEndpoints:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_config(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "engine" in data
        assert "sms_providers" in data

    def test_capabilities(self, client):
        resp = client.get("/api/engine/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "engines" in data
        assert "stealth_modules" in data

    def test_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "accounts" in data
        assert "proxies" in data
        assert "active_sessions" in data


class TestApiAccountsEndpoints:
    def test_get_accounts_empty(self, client):
        resp = client.get("/api/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["accounts"] == []

    def test_get_accounts_populated(self, client):
        account_manager.save("user1@gmail.com", "pass1")
        account_manager.save("user2@gmail.com", "pass2")

        resp = client.get("/api/accounts?limit=1&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["accounts"]) == 1

    def test_export_accounts(self, client):
        account_manager.save("export@gmail.com", "pass")
        for fmt in ["json", "csv", "txt", "all"]:
            resp = client.post("/api/accounts/export", json={"format": fmt})
            assert resp.status_code == 200

    def test_export_invalid_format(self, client):
        resp = client.post("/api/accounts/export", json={"format": "xml"})
        assert resp.status_code == 422


class TestApiSessionLifecycle:
    def test_start_and_get_session(self, client):
        with patch("api.main.run_creation_session"):
            start_resp = client.post("/api/session/start", json={"num_accounts": 2, "concurrent": 1, "use_proxies": False})
            assert start_resp.status_code == 200
            sid = start_resp.json()["session_id"]

            get_resp = client.get(f"/api/session/{sid}")
            assert get_resp.status_code == 200
            s_data = get_resp.json()
            assert s_data["id"] == sid
            assert s_data["status"] == "initializing"

            stop_resp = client.post(f"/api/session/{sid}/stop")
            assert stop_resp.status_code == 200

            # List sessions
            sessions_resp = client.get("/api/sessions")
            assert sessions_resp.status_code == 200
            all_s = sessions_resp.json()["sessions"]
            assert any(s["id"] == sid for s in all_s)

    def test_preflight_proxy_validation(self, client, monkeypatch):
        from core.proxy_manager import proxy_manager
        monkeypatch.setattr("config.settings.Config.ENABLE_PROXY", True)

        # Empty pool
        monkeypatch.setattr(proxy_manager, "get_all_proxies", lambda: [])
        resp = client.post("/api/session/start", json={"num_accounts": 2, "use_proxies": True})
        assert resp.status_code == 400
        assert "No proxies in pool" in resp.json()["detail"]

        # Proxies exist but 0 healthy
        monkeypatch.setattr(proxy_manager, "get_all_proxies", lambda: [{"ip": "1.1.1.1", "port": 8080}])
        monkeypatch.setattr(proxy_manager, "get_stats", lambda: {"total": 1, "healthy": 0})
        resp = client.post("/api/session/start", json={"num_accounts": 2, "use_proxies": True})
        assert resp.status_code == 400
        assert "All proxies marked unhealthy" in resp.json()["detail"]

    def test_resume_unknown_session_404(self, client):
        resp = client.post("/api/session/does-not-exist/resume")
        assert resp.status_code == 404

    def test_resume_active_status_rejected(self, client):
        with patch("api.main.run_creation_session"):
            start_resp = client.post(
                "/api/session/start",
                json={"num_accounts": 3, "concurrent": 1, "use_proxies": False},
            )
            sid = start_resp.json()["session_id"]
        # status is 'initializing' after creation — not a resumable terminal state
        resp = client.post(f"/api/session/{sid}/resume")
        assert resp.status_code == 400
        assert "active status" in resp.json()["detail"]

    def test_resume_corrupt_config_rejected(self, client):
        with patch("api.main.run_creation_session"):
            start_resp = client.post(
                "/api/session/start",
                json={"num_accounts": 3, "concurrent": 1, "use_proxies": False},
            )
            sid = start_resp.json()["session_id"]
        # Corrupt a field OTHER than num_accounts (num_accounts is replaced by remaining)
        account_manager.db.save_session(
            sid,
            status="stopped",
            num_accounts=3,
            config_json='{"num_accounts": 3, "concurrent": "bogus"}',
        )
        resp = client.post(f"/api/session/{sid}/resume")
        assert resp.status_code == 400
        assert "Invalid stored session configuration" in resp.json()["detail"]

    def test_preflight_proxy_disabled_distinct_message(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.Config.ENABLE_PROXY", False)
        resp = client.post(
            "/api/session/start",
            json={"num_accounts": 2, "use_proxies": True},
        )
        assert resp.status_code == 400
        assert "ENABLE_PROXY" in resp.json()["detail"]

    def test_preflight_sms_zero_balance(self, client, monkeypatch):
        from config.settings import Config

        async def _zero(*args, **kwargs):
            return {"5sim": 0.0, "sms-activate": 0.0}

        monkeypatch.setattr(Config, "FIVESIM_API_KEY", "k5")
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "ksa")
        monkeypatch.setattr("services.sms_manager.check_balance", _zero)

        resp = client.post(
            "/api/session/start",
            json={"num_accounts": 1, "use_sms": True, "use_proxies": False},
        )
        assert resp.status_code == 400
        assert "zero balance" in resp.json()["detail"]

    def test_preflight_sms_positive_balance_proceeds(self, client, monkeypatch):
        from config.settings import Config

        async def _funded(*args, **kwargs):
            return {"5sim": 5.0, "sms-activate": None}

        monkeypatch.setattr(Config, "FIVESIM_API_KEY", "k5")
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "")
        monkeypatch.setattr("services.sms_manager.check_balance", _funded)

        with patch("api.main.run_creation_session"):
            resp = client.post(
                "/api/session/start",
                json={"num_accounts": 1, "use_sms": True, "use_proxies": False},
            )
        assert resp.status_code == 200

    def test_sms_balances_endpoint_canonical_keys(self, client, monkeypatch):
        async def _fake(*args, **kwargs):
            return {"5sim": 1.5, "sms-activate": 2.5}

        monkeypatch.setattr("services.sms_manager.check_balance", _fake)
        resp = client.get("/api/sms/balances")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "sms-activate" in data["balances"]
        assert data["balances"]["sms-activate"] == 2.5


class TestApiWebSocketRedaction:
    def test_add_account_broadcast_redacts_secrets(self, client, monkeypatch):
        import asyncio
        from api.main import CreationSession, SessionConfig, manager

        captured = {}

        async def fake_broadcast(message):
            captured["payload"] = message

        monkeypatch.setattr(manager, "broadcast", fake_broadcast)

        session = CreationSession("ws_sess", SessionConfig(num_accounts=1))
        result = {
            "index": 0,
            "email": "a@x.com",
            "password": "supersecret",
            "proxy": "user:pass@1.2.3.4:8080",
            "strategy": "standard",
            "success": True,
            "created_at": "now",
            "duration": 2.5,
        }
        asyncio.run(session.add_account(result))

        payload = captured["payload"]["account"]
        assert "password" not in payload
        assert "proxy" not in payload
        assert payload["email"] == "a@x.com"
        assert payload["strategy"] == "standard"
        assert payload["success"] is True

        # The full secret-bearing result is still kept server-side
        assert session.created_accounts[0]["password"] == "supersecret"

    def test_resume_session_flow(self, client):
        with patch("api.main.run_creation_session"):
            # 1. Start session with 5 accounts
            start_resp = client.post("/api/session/start", json={"num_accounts": 5, "concurrent": 1, "use_proxies": False})
            assert start_resp.status_code == 200
            sid = start_resp.json()["session_id"]

            # Simulate session completing partially: 2 successes, 1 failure -> 2 remaining
            account_manager.db.update_session(sid, status="stopped", successes=2, failures=1)

            # 2. Resume session
            resume_resp = client.post(f"/api/session/{sid}/resume")
            assert resume_resp.status_code == 200
            r_data = resume_resp.json()
            assert r_data["resumed_from"] == sid
            assert r_data["remaining"] == 2
            new_sid = r_data["session_id"]
            assert new_sid != sid

            # Verify new session in DB
            new_sess = account_manager.db.get_session(new_sid)
            assert new_sess["num_accounts"] == 2

            # 3. Resume when remaining <= 0 -> 400
            account_manager.db.update_session(new_sid, status="completed", successes=2, failures=0)
            fail_resp = client.post(f"/api/session/{new_sid}/resume")
            assert fail_resp.status_code == 400
            assert "no remaining accounts" in fail_resp.json()["detail"].lower()

    def test_session_start_with_explicit_flow_mode(self, client):
        with patch("api.main.run_creation_session"):
            resp = client.post("/api/session/start", json={
                "num_accounts": 3,
                "concurrent": 1,
                "use_proxies": False,
                "flow_mode": "youtube",
            })
            assert resp.status_code == 200
            sid = resp.json()["session_id"]
            sess = account_manager.db.get_session(sid)
            assert sess["config"]["flow_mode"] == "youtube"



class TestApiAuthMiddleware:
    def test_auth_enforced_when_token_set(self, client, monkeypatch):
        monkeypatch.setenv("API_SECRET_TOKEN", "supersecret123")

        # Without token -> 401
        resp = client.get("/api/health")
        assert resp.status_code == 401

        # With Bearer token -> 200
        resp = client.get("/api/health", headers={"Authorization": "Bearer supersecret123"})
        assert resp.status_code == 200

        # With X-API-Key -> 200
        resp = client.get("/api/health", headers={"X-API-Key": "supersecret123"})
        assert resp.status_code == 200
