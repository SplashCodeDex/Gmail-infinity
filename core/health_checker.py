"""
Account Health Checker - Verify that created accounts still work
Attempts IMAP login to check if account is active/suspended/locked.
"""
import logging
import imaplib
import time
from datetime import datetime

logger = logging.getLogger('gmail_creator_health')


class AccountHealthChecker:
    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993

    @staticmethod
    def check_single(email, password):
        """
        Check if a Gmail account is accessible via IMAP.
        Returns: dict with status, message, checked_at
        """
        result = {
            "email": email,
            "status": "unknown",
            "message": "",
            "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        try:
            mail = imaplib.IMAP4_SSL(
                AccountHealthChecker.IMAP_HOST,
                AccountHealthChecker.IMAP_PORT,
                timeout=15,
            )
            mail.login(email, password)
            mail.select("INBOX")
            mail.logout()
            result["status"] = "active"
            result["message"] = "Login successful"
        except imaplib.IMAP4.error as e:
            err = str(e).lower()
            if "invalid" in err or "credentials" in err:
                result["status"] = "password_changed"
                result["message"] = "Invalid credentials — password may have been changed"
            elif "web login" in err or "less secure" in err:
                result["status"] = "locked"
                result["message"] = "Account requires web login — may be locked"
            elif "suspended" in err or "disabled" in err:
                result["status"] = "suspended"
                result["message"] = "Account suspended by Google"
            else:
                result["status"] = "error"
                result["message"] = str(e)
        except ConnectionError:
            result["status"] = "network_error"
            result["message"] = "Cannot connect to Gmail IMAP server"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        return result

    @staticmethod
    def check_all(accounts, max_workers=8):
        """
        Check multiple accounts concurrently using ThreadPoolExecutor.
        Preserves input account ordering and isolates errors per account.
        """
        import concurrent.futures
        if not accounts:
            return []

        indexed_accounts = [
            (i, acc.get("email", ""), acc.get("password", ""))
            for i, acc in enumerate(accounts)
            if acc.get("email") and acc.get("password")
        ]

        if not indexed_accounts:
            return []

        results_by_index = {}
        worker_count = min(len(indexed_accounts), max(1, max_workers))

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_idx = {
                executor.submit(AccountHealthChecker.check_single, email, password): idx
                for idx, email, password in indexed_accounts
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    res = future.result()
                    results_by_index[idx] = res
                    logger.info(f"Health check: {res.get('email')} -> {res.get('status')}")
                except Exception as e:
                    results_by_index[idx] = {
                        "email": accounts[idx].get("email", ""),
                        "status": "error",
                        "message": str(e),
                        "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    }

        return [results_by_index[i] for i in sorted(results_by_index.keys())]

    @staticmethod
    def get_summary(results):
        """Summarize health check results."""
        total = len(results)
        active = sum(1 for r in results if r["status"] == "active")
        locked = sum(1 for r in results if r["status"] == "locked")
        suspended = sum(1 for r in results if r["status"] == "suspended")
        pw_changed = sum(1 for r in results if r["status"] == "password_changed")
        errors = sum(1 for r in results if r["status"] in ("error", "network_error"))

        return {
            "total": total,
            "active": active,
            "locked": locked,
            "suspended": suspended,
            "password_changed": pw_changed,
            "errors": errors,
            "health_rate": (active / total * 100) if total > 0 else 0,
        }
