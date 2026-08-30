"""
Runners - Public entry points for account creation flows.

The implementation now lives in the modular `core.flows` package
(shared, prewarm, navigation, steps, post_registration, completion,
playwright_flow, appium_flow, sync_entry). This module remains as the
stable import surface for existing callers (enhanced_creator.py).

Import order: core.flows -> core.flows.shared/others. No circular
imports (flows modules only import core.* siblings, never runners).
"""
from core.flows.shared import (
    capture_failure,
    _update_progress,
    _try_click,
    _wait_for_page_change,
    parse_birthday as _parse_birthday,
)
from core.flows.prewarm import google_prewarm as _google_prewarm
from core.flows.navigation import navigate_to_signup
from core.flows.steps import (
    fill_name_step,
    fill_birthday_step,
    choose_username_step,
    fill_password_step,
    refill_after_qr_escape,
)
from core.flows.post_registration import handle_post_registration_steps as _handle_post_registration_steps
from core.flows.completion import (
    verify_account_created,
    save_account,
    notify_success,
    warm_new_account,
)
from core.flows.playwright_flow import async_playwright_flow
from core.flows.appium_flow import run_appium_flow
from core.flows.sync_entry import run_playwright_flow

__all__ = [
    # Public flow entry points (historical API)
    "run_playwright_flow",
    "run_appium_flow",
    "async_playwright_flow",
    # Re-exported internals for backward compatibility
    "capture_failure",
    "_update_progress",
    "_try_click",
    "_wait_for_page_change",
    "_parse_birthday",
    "_google_prewarm",
    "_handle_post_registration_steps",
    "navigate_to_signup",
    "fill_name_step",
    "fill_birthday_step",
    "choose_username_step",
    "fill_password_step",
    "refill_after_qr_escape",
    "verify_account_created",
    "save_account",
    "notify_success",
    "warm_new_account",
]
