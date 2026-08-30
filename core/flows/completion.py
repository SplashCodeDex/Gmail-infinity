"""
Flows Completion - Post-signup verification, persistence, and warming.

Extracted from runners.py: tamper-proof account verification (session
cookies, landing URL, myaccount probe), database save, console output,
Telegram notification, and optional session warming.
"""
import logging

from config.settings import Config
from core.flows.shared import _update_progress

logger = logging.getLogger('gmail_creator_runners')

AUTH_COOKIE_NAMES = ["SID", "SSID", "HSID", "SAPISID", "APISID"]

SIGNUP_LIFECYCLE_MARKERS = [
    "accounts.google.com/lifecycle",
    "accounts.google.com/signup",
    "accounts.google.com/signin/v2",
    "flowentry=signup",
]


async def _get_auth_cookies(page):
    cookies = await page.context.cookies(["https://google.com", "https://accounts.google.com"])
    return {c.get("name", "") for c in cookies if c.get("name") in AUTH_COOKIE_NAMES}


async def _is_signup_lifecycle(url):
    return any(k in url for k in SIGNUP_LIFECYCLE_MARKERS)


async def verify_account_created(page, username, progress, account_task):
    """Tamper-proof check that the account was actually created & session is live."""
    _update_progress(progress, account_task, completed=95, description="Verifying Google account creation...")

    account_verified = False
    try:
        current_url = page.url.lower()
        is_signup_lifecycle = await _is_signup_lifecycle(current_url)

        # 1. Cookie Authentication Check (Google sets SID, SSID, HSID on authenticated session)
        auth_cookies = await _get_auth_cookies(page)
        if not is_signup_lifecycle and auth_cookies:
            account_verified = True
            logger.info(f"[VERIFY] Account confirmed via active session cookies: {auth_cookies}")

        # 2. Destination URL / Landing Check
        if not account_verified and not is_signup_lifecycle:
            if current_url.startswith("https://myaccount.google.com") or current_url.startswith("https://mail.google.com"):
                content = (await page.content()).lower()
                if "sign in" not in content and "use your google account" not in content:
                    account_verified = True
                    logger.info(f"[VERIFY] Account confirmed via landing URL: {current_url}")

        # 3. Direct verification probe against myaccount.google.com
        if not account_verified and not is_signup_lifecycle:
            try:
                await page.goto("https://myaccount.google.com/", timeout=15000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)
                my_url = page.url.lower()
                my_content = (await page.content()).lower()
                if "myaccount.google.com" in my_url and "sign in" not in my_url and "accounts.google.com/signin" not in my_url:
                    if not ("sign in to your account" in my_content or "use your google account" in my_content):
                        # Re-verify cookies after navigation
                        auth_cookies = await _get_auth_cookies(page)
                        if auth_cookies:
                            account_verified = True
                            logger.info(f"[VERIFY] Account confirmed via myaccount session probe (cookies: {auth_cookies})")
            except Exception as probe_err:
                logger.debug(f"MyAccount probe error: {probe_err}")

    except Exception as verify_err:
        logger.debug(f"Verification check exception: {verify_err}")

    return account_verified


def save_account(username, password, first_name, last_name, proxy, flow_mode,
                 method, month, day, year, gender):
    """Persist the created account to the database. Returns True on success."""
    recovery_email_val = getattr(Config, 'RECOVERY_EMAIL', '')
    try:
        from core.account_manager import account_manager
        account_manager.save(
            email=f"{username}@gmail.com",
            password=password,
            first_name=first_name,
            last_name=last_name,
            proxy=proxy or "",
            strategy=flow_mode,
            sms_service=method if "sms" in method else "",
            birthday=f"{month}/{day}/{year}",
            gender=gender,
            recovery_email=recovery_email_val,
            status="active",
            notes="Signup flow completed",
        )
        return True
    except Exception as db_err:
        logger.error(f"Failed to save account: {db_err}")
        return False


def notify_success(username, password, flow_mode, proxy):
    """Print credentials to console and send Telegram notification."""
    from rich.console import Console
    Console().print(f"[bold green]CREATED:[/] {username}@gmail.com | Password: {password}")

    try:
        from core.telegram_notifier import notifier
        notifier.notify_account_created(
            email=f"{username}@gmail.com",
            password=password,
            strategy=flow_mode,
            proxy=proxy or "",
        )
    except Exception:
        pass


async def warm_new_account(username, password, progress, account_task):
    """Post-creation account warming & login verification (non-fatal)."""
    try:
        if Config.ENABLE_SESSION_WARMING:
            from core.account_warmer import warm_account_playwright
            from core.account_manager import account_manager
            _update_progress(progress, account_task, completed=98,
                             description="Warming new account & verifying login...")
            warmed, warm_detail = await warm_account_playwright(f"{username}@gmail.com", password, duration_minutes=2)
            if warmed:
                account_manager.db.update_account_health(
                    f"{username}@gmail.com",
                    status="active",
                    note="Login verified and warmed successfully"
                )
            else:
                account_manager.db.update_account_health(
                    f"{username}@gmail.com",
                    status="unverified",
                    note=f"Created, but warm login verification failed: {warm_detail}"
                )
    except Exception as warm_err:
        logger.debug(f"Account warming (non-fatal): {warm_err}")
