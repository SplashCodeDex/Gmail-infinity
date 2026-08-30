"""
Flows Playwright - Orchestrates the full Playwright signup flow.

Extracted from runners.py (async_playwright_flow): initializes the
stealth browser, pre-warms, navigates, walks the form steps, handles
verification (with QR-escape restart), verifies creation, persists,
notifies, and warms the new account.
"""
import logging

from core.phone_bypass import handle_verification
from core.retry_engine import CreationError
from core.flows.shared import capture_failure, _update_progress
from core.flows.prewarm import google_prewarm
from core.flows.navigation import navigate_to_signup
from core.flows.steps import (
    fill_name_step,
    fill_birthday_step,
    choose_username_step,
    fill_password_step,
    refill_after_qr_escape,
)
from core.flows.post_registration import handle_post_registration_steps
from core.flows.completion import verify_account_created, save_account, notify_success, warm_new_account

try:
    from core.stealth_browser import PlaywrightStealthManager
except ImportError:
    PlaywrightStealthManager = None

logger = logging.getLogger('gmail_creator_runners')


async def async_playwright_flow(i, num_accounts, username, first_name, last_name,
                                 password, progress, account_task, proxy,
                                 month, day, year, gender,
                                 use_sms_api=False, flow_mode="standard", headless=None,
                                 retry_engine=None, event_callback=None):
    if progress is not None:
        setattr(progress, 'event_callback', event_callback)

    _update_progress(progress, account_task, completed=5, description="Starting Playwright Stealth flow...")
    manager = PlaywrightStealthManager()

    try:
        # ── Initialize browser ────────────────────────────────────────────
        if not await manager.initialize(proxy=proxy, is_premium=use_sms_api, headless=headless):
            logger.error("PlaywrightStealthManager.initialize() returned False")
            return False, CreationError.BROWSER_CRASH

        page = manager.page
        is_mobile = getattr(manager, 'is_mobile', False)

        # ── Pre-Warming ──────────────────────────────────────────────────
        if not use_sms_api:
            _update_progress(progress, account_task, completed=10, description="Building Google trust session...")
            await google_prewarm(page)
        else:
            _update_progress(progress, account_task, completed=10, description="Premium Mode: Direct to Registration...")

        # ── Step 1: Navigate to Google Signup ────────────────────────────
        _update_progress(progress, account_task, completed=15,
                         description=f"Opening Google Sign Up page [{flow_mode.upper()}]...")

        navigated = await navigate_to_signup(page, flow_mode, progress, account_task)
        if not navigated:
            logger.error("Could not find Google signup form after trying all URLs.")
            await capture_failure(page, "signup_form_not_found", username)
            return False, CreationError.TIMEOUT

        await page.wait_for_timeout(1000)

        # ── Step 2: Enter Name ────────────────────────────────────────────
        ok, err = await fill_name_step(page, manager, first_name, last_name, username,
                                       progress, account_task)
        if not ok:
            await capture_failure(page, "name_step_stuck", username)
            return False, err

        # ── Step 3: Birthday & Gender ─────────────────────────────────────
        ok, err = await fill_birthday_step(page, manager, month, day, year, gender,
                                            username, progress, account_task)
        if not ok:
            await capture_failure(page, "birthday_step_stuck", username)
            return False, err

        # ── Step 4: Choose username ───────────────────────────────────────
        ok, username = await choose_username_step(page, username, first_name, last_name,
                                                  progress, account_task)
        if not ok:
            await capture_failure(page, "username_taken_exhausted" if err == CreationError.USERNAME_TAKEN else "username_step_stuck", username)
            return False, err

        # ── Step 5: Password ──────────────────────────────────────────────
        await fill_password_step(page, password, progress, account_task)

        # ── Step 6: Verification (using phone_bypass module) ──────────────
        _update_progress(progress, account_task, completed=85, description="Handling verification...")

        success, method, should_restart = await handle_verification(
            page,
            is_mobile=is_mobile,
            use_sms_api=use_sms_api,
            progress=progress,
            account_task=account_task,
        )

        if should_restart:
            # Escaped verification — need to restart the entire signup flow
            logger.info(f"Verification escaped ({method}) — restarting signup flow...")
            ok, err = await refill_after_qr_escape(
                page, manager, first_name, last_name, username, password,
                month, day, year, gender, is_mobile, progress, account_task, method,
            )
            if not ok:
                return False, err

            # Re-check verification after restart
            success2, method2, _ = await handle_verification(
                page, is_mobile=is_mobile, use_sms_api=use_sms_api,
                progress=progress, account_task=account_task,
            )
            if not success2:
                error_type = CreationError.QR_BLOCKED if "qr" in method2 else CreationError.PHONE_REQUIRED
                return False, error_type
            method = method2

        if not success:
            error_type = CreationError.QR_BLOCKED if "qr" in method else CreationError.PHONE_REQUIRED
            if "send_sms" in method:
                _update_progress(progress, account_task,
                                 description="[bold red]IP flagged — use proxy/VPN[/]")
            else:
                _update_progress(progress, account_task,
                                 description=f"[bold red]Failed: {method}[/]")
            await capture_failure(page, f"verification_{method}", username)
            return False, error_type

        # ── Step 7: Post-registration multi-step handling ──
        await handle_post_registration_steps(page, username, progress, account_task, is_mobile=is_mobile)

        # ── Step 8: Verify account was actually created (Tamper-Proof) ────
        account_verified = await verify_account_created(page, username, progress, account_task)

        if not account_verified:
            logger.error(f"VERIFICATION FAILED: Account was NOT created. Still on page: {page.url}")
            await capture_failure(page, "account_unverified", username)
            _update_progress(progress, account_task, completed=100,
                             description="[bold red]FAILED: Google account was not created[/]")
            return False, CreationError.UNKNOWN

        # ── Done ──────────────────────────────────────────────────────────
        _update_progress(progress, account_task, completed=100,
                         description=f"[bold green]SUCCESS: {username}@gmail.com[/]")
        logger.info(f"Account VERIFIED and created: {username}@gmail.com")

        save_account(username, password, first_name, last_name, proxy, flow_mode,
                     method, month, day, year, gender)
        notify_success(username, password, flow_mode, proxy)
        await warm_new_account(username, password, progress, account_task)

        return True, "success"

    except Exception as e:
        logger.error(f"Playwright flow failed: {e}", exc_info=True)
        return False, CreationError.UNKNOWN
    finally:
        await manager.close()
