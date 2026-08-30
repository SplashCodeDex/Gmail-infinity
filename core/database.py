"""
Database Manager - SQLite storage for accounts, logs, and session data
"""
import sqlite3
import os
import logging
from datetime import datetime
import json
from typing import Optional, List, Dict

from config.settings import PROJECT_ROOT

logger = logging.getLogger('gmail_creator_db')


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = str(PROJECT_ROOT / "data" / "database.db")
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
        self._migrate_schema()

    def _ensure_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
        except sqlite3.Error:
            pass
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        first_name TEXT DEFAULT '',
                        last_name TEXT DEFAULT '',
                        birthday TEXT DEFAULT '',
                        gender TEXT DEFAULT '',
                        proxy TEXT DEFAULT '',
                        strategy TEXT DEFAULT '',
                        sms_service TEXT DEFAULT '',
                        phone_number TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        notes TEXT DEFAULT ''
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS execution_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level TEXT,
                        message TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS session_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_attempts INTEGER DEFAULT 0,
                        successes INTEGER DEFAULT 0,
                        failures INTEGER DEFAULT 0,
                        strategies_used TEXT DEFAULT '{}',
                        errors TEXT DEFAULT '{}',
                        duration_seconds REAL DEFAULT 0
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        status TEXT,
                        num_accounts INTEGER,
                        successes INTEGER DEFAULT 0,
                        failures INTEGER DEFAULT 0,
                        progress_json TEXT DEFAULT '{}',
                        config_json TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        ended_at TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS session_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level TEXT,
                        message TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_session_logs_session_id ON session_logs (session_id)
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS session_strategy_stats (
                        session_id TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        attempts INTEGER DEFAULT 0,
                        successes INTEGER DEFAULT 0,
                        failures INTEGER DEFAULT 0,
                        avg_time REAL DEFAULT 0.0,
                        PRIMARY KEY (session_id, strategy)
                    )
                ''')

                conn.commit()
                logger.debug("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")

    def _migrate_schema(self):
        new_columns = [
            ("birthday", "TEXT DEFAULT ''"),
            ("gender", "TEXT DEFAULT ''"),
            ("strategy", "TEXT DEFAULT ''"),
            ("sms_service", "TEXT DEFAULT ''"),
            ("phone_number", "TEXT DEFAULT ''"),
            ("notes", "TEXT DEFAULT ''"),
            ("recovery_email", "TEXT DEFAULT ''"),
            ("health_note", "TEXT DEFAULT ''"),
            ("last_health_checked_at", "TEXT DEFAULT ''"),
        ]
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(accounts)")
                existing = {row[1] for row in cursor.fetchall()}
                for col_name, col_def in new_columns:
                    if col_name not in existing:
                        cursor.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_def}")
                        logger.info(f"Migrated: added column '{col_name}' to accounts table")
                conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"Schema migration warning: {e}")

    def save_account(self, email, password, first_name="", last_name="",
                     proxy="", strategy="", sms_service="", phone_number="",
                     birthday="", gender="", status="active", notes="",
                     recovery_email=""):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO accounts
                    (email, password, first_name, last_name, birthday, gender,
                     proxy, strategy, sms_service, phone_number, status, notes, recovery_email, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (email, password, first_name, last_name, birthday, gender,
                      proxy, strategy, sms_service, phone_number, status, notes, recovery_email,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
                logger.info(f"Account saved: {email}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Account already exists: {email}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to save account {email}: {e}")
            return False

    def get_all_accounts(self):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve accounts: {e}")
            return []

    def get_accounts_page(self, limit=50, offset=0):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM accounts ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (max(1, limit), max(0, offset))
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve accounts page: {e}")
            return []

    def get_account_count(self):
        return self.get_accounts_count()

    def get_accounts_count(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM accounts')
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.Error:
            return 0

    def get_stats(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                        COUNT(*),
                        SUM(CASE WHEN status='active' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status='suspended' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status='locked' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status='error' THEN 1 ELSE 0 END)
                    FROM accounts
                ''')
                row = cursor.fetchone() or (0, 0, 0, 0, 0)
                total = row[0] or 0
                active = row[1] or 0
                suspended = row[2] or 0
                locked = row[3] or 0
                error = row[4] or 0

                cursor.execute('''
                    SELECT COALESCE(NULLIF(strategy, ''), 'unknown'), COUNT(*)
                    FROM accounts GROUP BY strategy
                ''')
                strategies = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('''
                    SELECT sms_service, COUNT(*)
                    FROM accounts WHERE sms_service != '' AND sms_service IS NOT NULL
                    GROUP BY sms_service
                ''')
                sms_services = {r[0]: r[1] for r in cursor.fetchall()}

                return {
                    "total": total,
                    "active": active,
                    "suspended": suspended,
                    "locked": locked,
                    "error": error,
                    "success_rate": (active / total * 100) if total > 0 else 0,
                    "strategies": strategies,
                    "sms_services": sms_services,
                }
        except sqlite3.Error as e:
            logger.error(f"Failed to calculate stats: {e}")
            return {
                "total": 0, "active": 0, "suspended": 0, "locked": 0, "error": 0,
                "success_rate": 0, "strategies": {}, "sms_services": {}
            }

    def update_account_status(self, email, status, notes=""):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE accounts SET status=?, notes=? WHERE email=?',
                    (status, notes, email)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update account {email}: {e}")
            return False

    def update_account_health(self, email: str, status: Optional[str] = None, note: str = "", checked_at: Optional[str] = None) -> bool:
        """Update account health diagnostics and conditionally flip status if definitive.

        Definitive statuses that flip the account status:
          active, unverified, password_changed, suspended
        Ambiguous IMAP/network statuses (locked, network_error, error, unknown):
          Only update health_note and last_health_checked_at. Never clobber status or creation notes.
        """
        DEFINITIVE_STATUSES = {"active", "unverified", "password_changed", "suspended"}
        now_str = checked_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status and status in DEFINITIVE_STATUSES:
                    cursor.execute('''
                        UPDATE accounts
                        SET status = ?, health_note = ?, last_health_checked_at = ?
                        WHERE email = ?
                    ''', (status, note, now_str, email))
                else:
                    cursor.execute('''
                        UPDATE accounts
                        SET health_note = ?, last_health_checked_at = ?
                        WHERE email = ?
                    ''', (note, now_str, email))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update account health for {email}: {e}")
            return False

    def email_exists(self, email: str) -> bool:
        """Check if an email already exists in the vault."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM accounts WHERE email = ? LIMIT 1', (email,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Failed to check email existence for {email}: {e}")
            return False

    def save_session_strategy_stats(self, session_id: str, rows: List[Dict]) -> bool:
        """Persist real per-strategy execution metrics for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for row in rows:
                    strat = row.get("strategy", "")
                    attempts = row.get("attempts", 0)
                    successes = row.get("successes", 0)
                    failures = row.get("failures", 0)
                    avg_time = row.get("avg_time", 0.0)
                    if strat:
                        cursor.execute('''
                            INSERT OR REPLACE INTO session_strategy_stats
                            (session_id, strategy, attempts, successes, failures, avg_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (session_id, strat, attempts, successes, failures, avg_time))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to save session strategy stats for {session_id}: {e}")
            return False

    def get_recent_strategy_stats(self, limit_sessions: int = 20) -> List[Dict]:
        """Aggregate real per-strategy performance across recent sessions."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT session_id FROM session_strategy_stats
                    ORDER BY rowid DESC LIMIT ?
                ''', (limit_sessions,))
                recent_sids = [r["session_id"] for r in cursor.fetchall()]
                if not recent_sids:
                    return []

                placeholders = ",".join("?" for _ in recent_sids)
                cursor.execute(f'''
                    SELECT strategy,
                           SUM(attempts) as total_attempts,
                           SUM(successes) as total_successes,
                           SUM(failures) as total_failures,
                           AVG(avg_time) as avg_time
                    FROM session_strategy_stats
                    WHERE session_id IN ({placeholders})
                    GROUP BY strategy
                ''', recent_sids)
                return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent strategy stats: {e}")
            return []

    def log_event(self, level, message):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO execution_logs (level, message, timestamp)
                    VALUES (?, ?, ?)
                ''', (level, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save log: {e}")

    def save_session_stats(self, total_attempts, successes, failures,
                           strategies_used, errors, duration_seconds):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO session_stats
                    (total_attempts, successes, failures, strategies_used, errors, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (total_attempts, successes, failures,
                      json.dumps(strategies_used), json.dumps(errors),
                      duration_seconds))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save session stats: {e}")

    def get_session_history(self, limit=10):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM session_stats ORDER BY session_start DESC LIMIT ?',
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    # ==========================================
    # Phase A Sessions Table Operations
    # ==========================================

    def save_session(self, session_id, status="initializing", num_accounts=0, config_json="{}"):
        if isinstance(config_json, dict):
            config_json = json.dumps(config_json)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sessions (session_id, status, num_accounts, config_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        status=excluded.status,
                        num_accounts=excluded.num_accounts,
                        config_json=excluded.config_json
                ''', (session_id, status, num_accounts, config_json, now))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False

    def update_session(self, session_id, status=None, successes=None, failures=None,
                       progress_json=None, started_at=None, ended_at=None):
        updates = []
        params = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if successes is not None:
            updates.append("successes = ?")
            params.append(successes)
        if failures is not None:
            updates.append("failures = ?")
            params.append(failures)
        if progress_json is not None:
            if isinstance(progress_json, dict):
                progress_json = json.dumps(progress_json)
            updates.append("progress_json = ?")
            params.append(progress_json)
        if started_at is not None:
            updates.append("started_at = ?")
            params.append(started_at)
        if ended_at is not None:
            updates.append("ended_at = ?")
            params.append(ended_at)

        if not updates:
            return True

        params.append(session_id)
        sql = f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    def append_session_log(self, session_id, level, message, timestamp=None):
        if not timestamp:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO session_logs (session_id, timestamp, level, message)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, timestamp, level, message))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to append session log for {session_id}: {e}")
            return False

    def get_sessions(self, limit=100, offset=0):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM sessions ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (max(1, limit), max(0, offset))
                )
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("progress_json"), str):
                        try:
                            item["progress"] = json.loads(item["progress_json"])
                        except Exception:
                            item["progress"] = {}
                    if isinstance(item.get("config_json"), str):
                        try:
                            item["config"] = json.loads(item["config_json"])
                        except Exception:
                            item["config"] = {}
                    results.append(item)
                return results
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve sessions: {e}")
            return []

    def get_session(self, session_id):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                item = dict(row)
                if isinstance(item.get("progress_json"), str):
                    try:
                        item["progress"] = json.loads(item["progress_json"])
                    except Exception:
                        item["progress"] = {}
                if isinstance(item.get("config_json"), str):
                    try:
                        item["config"] = json.loads(item["config_json"])
                    except Exception:
                        item["config"] = {}
                return item
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None

    def get_session_logs(self, session_id, limit=100):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM session_logs WHERE session_id = ? ORDER BY id ASC LIMIT ?',
                    (session_id, max(1, limit))
                )
                return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve logs for session {session_id}: {e}")
            return []

    def get_interrupted_sessions(self):
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE status IN ('running', 'initializing')"
                )
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("progress_json"), str):
                        try:
                            item["progress"] = json.loads(item["progress_json"])
                        except Exception:
                            item["progress"] = {}
                    if isinstance(item.get("config_json"), str):
                        try:
                            item["config"] = json.loads(item["config_json"])
                        except Exception:
                            item["config"] = {}
                    results.append(item)
                return results
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve interrupted sessions: {e}")
            return []


