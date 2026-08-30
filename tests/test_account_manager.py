"""Tests for core.account_manager — SQLite single-source persistence."""
import csv
import json

import pytest

from core.account_manager import AccountManager


@pytest.fixture
def legacy_dir(tmp_path):
    d = tmp_path / "legacy"
    d.mkdir()
    return d


@pytest.fixture
def manager(tmp_path, legacy_dir):
    # Empty db + empty legacy dir: auto-import guard has nothing to do
    return AccountManager(db_path=str(tmp_path / "test.db"), legacy_dir=str(legacy_dir))


class TestSaveAndGetAll:
    def test_save_and_roundtrip(self, manager):
        assert manager.save(email="a@gmail.com", password="pw1") is True
        accounts = manager.get_all()
        assert len(accounts) == 1
        assert accounts[0]["email"] == "a@gmail.com"
        assert accounts[0]["password"] == "pw1"

    def test_duplicate_email_is_rejected(self, manager):
        assert manager.save(email="a@gmail.com", password="pw1") is True
        assert manager.save(email="a@gmail.com", password="pw2") is False
        assert manager.get_count() == 1

    def test_get_stats(self, manager):
        manager.save(email="a@gmail.com", password="pw", strategy="standard")
        manager.save(email="b@gmail.com", password="pw", strategy="standard")
        manager.save(email="c@gmail.com", password="pw", strategy="youtube")
        stats = manager.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 3
        assert stats["strategies"] == {"standard": 2, "youtube": 1}


class TestExports:
    def test_export_txt(self, manager, tmp_path):
        manager.save(email="a@gmail.com", password="pw1")
        out = manager.export_txt(filepath=str(tmp_path / "out.txt"))
        content = open(out, encoding="utf-8").read()
        assert "a@gmail.com:pw1" in content

    def test_export_csv(self, manager, tmp_path):
        manager.save(email="a@gmail.com", password="pw1", first_name="A")
        out = manager.export_csv(filepath=str(tmp_path / "out.csv"))
        rows = list(csv.reader(open(out, encoding="utf-8")))
        assert rows[0][0] == "Email"
        assert ["a@gmail.com", "pw1", "A"] == rows[1][:3]

    def test_export_json(self, manager, tmp_path):
        manager.save(email="a@gmail.com", password="pw1")
        out = manager.export_json(filepath=str(tmp_path / "out.json"))
        data = json.load(open(out, encoding="utf-8"))
        assert data[0]["email"] == "a@gmail.com"


class TestLegacyMigration:
    def test_migrate_from_legacy_files(self, manager, legacy_dir):
        (legacy_dir / "accounts.txt").write_text("old1@gmail.com:pw1\n")
        (legacy_dir / "accounts.json").write_text(json.dumps([
            {"email": "old2@gmail.com", "password": "pw2", "first_name": "Old"},
            {"email": "old3@gmail.com", "password": "pw3"},
        ]))
        migrated = manager.migrate_old_data()
        assert migrated == 3
        assert manager.get_count() == 3

    def test_migration_is_idempotent(self, manager, legacy_dir):
        (legacy_dir / "accounts.txt").write_text("old1@gmail.com:pw1\n")
        assert manager.migrate_old_data() == 1
        assert manager.migrate_old_data() == 0  # UNIQUE constraint skips dupes
        assert manager.get_count() == 1

    def test_auto_import_on_empty_db(self, tmp_path, legacy_dir):
        (legacy_dir / "accounts.json").write_text(json.dumps([
            {"email": "auto@gmail.com", "password": "pw"},
        ]))
        # Fresh empty db + legacy file present -> constructor auto-imports
        manager = AccountManager(db_path=str(tmp_path / "fresh.db"), legacy_dir=str(legacy_dir))
        assert manager.get_count() == 1
        assert manager.get_all()[0]["email"] == "auto@gmail.com"

    def test_no_auto_import_when_db_populated(self, tmp_path, legacy_dir):
        manager = AccountManager(db_path=str(tmp_path / "populated.db"), legacy_dir=str(legacy_dir))
        manager.save(email="seed@gmail.com", password="pw")
        # Legacy file appears AFTER the vault is populated
        (legacy_dir / "accounts.txt").write_text("late@gmail.com:pw\n")
        # Re-instantiating: db is non-empty -> legacy file must NOT be imported
        manager2 = AccountManager(db_path=str(tmp_path / "populated.db"), legacy_dir=str(legacy_dir))
        assert manager2.get_count() == 1
        assert manager2.get_all()[0]["email"] == "seed@gmail.com"
