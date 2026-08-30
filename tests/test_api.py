"""
Tests for api.main — FastAPI endpoints, auth middleware, session lifecycle, export, and diagnostics.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

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
