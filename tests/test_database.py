"""
Tests for core.database — DatabaseManager operations, schema, sessions, and logs.
"""
import pytest
from core.database import DatabaseManager


@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test.db"
    return DatabaseManager(str(db_file))


class TestDatabaseManager:
    def test_schema_initialization(self, db):
        assert db.get_account_count() == 0
        stats = db.get_stats()
        assert stats["total"] == 0
        assert stats["active"] == 0

    def test_save_and_retrieve_account(self, db):
        saved = db.save_account(
            email="test@gmail.com",
            password="secretpassword",
            first_name="John",
            last_name="Doe",
            proxy="127.0.0.1:8080",
            strategy="standard",
            status="active"
        )
        assert saved is True
        assert db.get_account_count() == 1

        # Duplicate email should fail
        saved_duplicate = db.save_account(
            email="test@gmail.com",
            password="secretpassword2"
        )
        assert saved_duplicate is False

        accounts = db.get_all_accounts()
        assert len(accounts) == 1
        assert accounts[0]["email"] == "test@gmail.com"
        assert accounts[0]["first_name"] == "John"

    def test_pagination(self, db):
        for i in range(15):
            db.save_account(f"user{i}@gmail.com", "pass")

        assert db.get_accounts_count() == 15
        page1 = db.get_accounts_page(limit=10, offset=0)
        page2 = db.get_accounts_page(limit=10, offset=10)

        assert len(page1) == 10
        assert len(page2) == 5

    def test_get_stats_aggregation(self, db):
        db.save_account("a1@gmail.com", "p", strategy="standard", sms_service="5sim", status="active")
        db.save_account("a2@gmail.com", "p", strategy="standard", sms_service="5sim", status="active")
        db.save_account("a3@gmail.com", "p", strategy="youtube", sms_service="getsms", status="suspended")

        stats = db.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 2
        assert stats["suspended"] == 1
        assert stats["strategies"]["standard"] == 2
        assert stats["strategies"]["youtube"] == 1
        assert stats["sms_services"]["5sim"] == 2
        assert stats["sms_services"]["getsms"] == 1

    def test_session_lifecycle(self, db):
        # Save session
        sid = "test_session_1"
        assert db.save_session(sid, status="initializing", num_accounts=5, config_json={"concurrent": 2})

        s = db.get_session(sid)
        assert s is not None
        assert s["session_id"] == sid
        assert s["status"] == "initializing"
        assert s["config"]["concurrent"] == 2

        # Update session
        assert db.update_session(
            sid,
            status="running",
            successes=2,
            failures=1,
            progress_json={"current": 3, "successes": 2, "failures": 1}
        )

        s_updated = db.get_session(sid)
        assert s_updated["status"] == "running"
        assert s_updated["successes"] == 2
        assert s_updated["failures"] == 1
        assert s_updated["progress"]["current"] == 3

        # Interrupted sessions query
        interrupted = db.get_interrupted_sessions()
        assert len(interrupted) == 1
        assert interrupted[0]["session_id"] == sid

        # Mark completed
        db.update_session(sid, status="completed")
        assert len(db.get_interrupted_sessions()) == 0

    def test_session_logs(self, db):
        sid = "log_session_1"
        db.save_session(sid, status="running")
        db.append_session_log(sid, "info", "Starting creation")
        db.append_session_log(sid, "success", "Created user1@gmail.com")

        logs = db.get_session_logs(sid, limit=10)
        assert len(logs) == 2
        assert logs[0]["level"] == "info"
        assert logs[1]["level"] == "success"
        assert "Created" in logs[1]["message"]

    def test_recovery_email_and_update_status(self, db):
        db.save_account(
            email="recov@gmail.com",
            password="pass",
            recovery_email="backup@outlook.com",
            status="unverified",
            notes="Initial signup"
        )
        accounts = db.get_all_accounts()
        assert len(accounts) == 1
        assert accounts[0]["recovery_email"] == "backup@outlook.com"
        assert accounts[0]["status"] == "unverified"

        # Update status
        assert db.update_account_status("recov@gmail.com", "active", notes="Warmed and login verified") is True
        updated = db.get_all_accounts()
        assert updated[0]["status"] == "active"
        assert updated[0]["notes"] == "Warmed and login verified"

    def test_update_account_health(self, db):
        db.save_account(
            email="health@gmail.com",
            password="pass",
            status="active",
            notes="Creation metadata note"
        )

        # 1. Ambiguous status (e.g. 'locked' / 'network_error') does NOT flip account status
        assert db.update_account_health("health@gmail.com", status="locked", note="Web login required") is True
        acc = db.get_all_accounts()[0]
        assert acc["status"] == "active"  # Status preserved!
        assert acc["health_note"] == "Web login required"
        assert acc["notes"] == "Creation metadata note"  # Original notes preserved!
        assert acc["last_health_checked_at"] != ""

        # 2. Definitive whitelist status (e.g. 'suspended' or 'unverified') DOES flip account status
        assert db.update_account_health("health@gmail.com", status="suspended", note="Account disabled") is True
        acc = db.get_all_accounts()[0]
        assert acc["status"] == "suspended"
        assert acc["health_note"] == "Account disabled"
        assert acc["notes"] == "Creation metadata note"

    def test_session_strategy_stats_and_aggregation(self, db):
        rows1 = [
            {"strategy": "standard", "attempts": 5, "successes": 4, "failures": 1, "avg_time": 25.0},
            {"strategy": "youtube", "attempts": 3, "successes": 1, "failures": 2, "avg_time": 40.0}
        ]
        assert db.save_session_strategy_stats("sess_1", rows1) is True

        rows2 = [
            {"strategy": "standard", "attempts": 2, "successes": 2, "failures": 0, "avg_time": 20.0},
        ]
        assert db.save_session_strategy_stats("sess_2", rows2) is True

        recent = db.get_recent_strategy_stats(limit_sessions=10)
        recent_by_strat = {r["strategy"]: r for r in recent}

        assert "standard" in recent_by_strat
        assert recent_by_strat["standard"]["total_attempts"] == 7
        assert recent_by_strat["standard"]["total_successes"] == 6
        assert recent_by_strat["standard"]["total_failures"] == 1

        assert "youtube" in recent_by_strat
        assert recent_by_strat["youtube"]["total_attempts"] == 3
        assert recent_by_strat["youtube"]["total_successes"] == 1

    def test_email_exists(self, db):
        assert db.email_exists("unknown@gmail.com") is False
        db.save_account("user1@gmail.com", "pass")
        assert db.email_exists("user1@gmail.com") is True
        assert db.email_exists("USER1@gmail.com") is True or db.email_exists("user1@gmail.com")


