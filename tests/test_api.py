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
            start_resp = client.post("/api/session/start", json={"num_accounts": 2, "concurrent": 1})
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

    def test_resume_session_flow(self, client):
        with patch("api.main.run_creation_session"):
            # 1. Start session with 5 accounts
            start_resp = client.post("/api/session/start", json={"num_accounts": 5, "concurrent": 1})
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
