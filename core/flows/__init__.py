"""
core.flows - Modular account creation flows.

Split from the original monolithic core/runners.py into focused modules:

  shared            - failure capture, progress, page helpers, birthday parsing
  prewarm           - Google trust-building pre-warm session
  navigation        - signup URL rotation & organic routes
  steps             - name / birthday / username / password form steps
  post_registration - recovery email, phone skip, review, personalization, terms
  verification      - delegated to core.phone_bypass (kept as entry point)
  completion        - account verification, persistence, notify, warming
  playwright_flow   - Playwright orchestration
  appium_flow       - Appium (Android) orchestration

Public entry points re-exported here match the historical runners.py API.
"""
from core.flows.shared import (
    capture_failure,
    _update_progress,
    _try_click,
    _wait_for_page_change,
    parse_birthday,
)
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
    "capture_failure",
    "_update_progress",
    "_try_click",
    "_wait_for_page_change",
    "parse_birthday",
    "google_prewarm",
    "navigate_to_signup",
    "fill_name_step",
    "fill_birthday_step",
    "choose_username_step",
    "fill_password_step",
    "refill_after_qr_escape",
    "handle_post_registration_steps",
    "verify_account_created",
    "save_account",
    "notify_success",
    "warm_new_account",
    "async_playwright_flow",
    "run_appium_flow",
    "run_playwright_flow",
]
