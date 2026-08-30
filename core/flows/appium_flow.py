"""
Flows Appium - Android account creation flow via Appium.

Extracted from runners.py (run_appium_flow): drives the Android
Settings "Add Account" path using the AppiumManager.
"""
import logging

from core.flows.shared import _update_progress

try:
    from core.android_creator import AppiumManager
except ImportError:
    AppiumManager = None

logger = logging.getLogger('gmail_creator_runners')


def run_appium_flow(i, num_accounts, username, first_name, last_name, password,
                    month, day, year, gender, progress, account_task):
    if AppiumManager is None:
        logger.error("Appium is not installed. Install with: pip install Appium-Python-Client")
        return False
    if progress and account_task is not None:
        _update_progress(progress, account_task, completed=10,
                         description="[blue]Starting Appium (Android) flow...[/]")
    manager = AppiumManager()
    if not manager.initialize():
        return False

    try:
        _update_progress(progress, account_task, completed=30, description="Navigating to Android Add Account...")
        if not manager.navigate_to_add_account():
            return False

        _update_progress(progress, account_task, completed=50, description="Starting Google Creation Flow...")
        if not manager.start_creation_flow():
            return False

        _update_progress(progress, account_task, completed=65, description="Entering Name...")
        if not manager.fill_name(first_name, last_name):
            return False

        _update_progress(progress, account_task, completed=75, description="Entering Birthday/Gender...")
        if not manager.fill_birthday_gender(month, day, year, gender):
            return False

        _update_progress(progress, account_task, completed=85, description="Checking for Phone Verification Bypass...")
        if not manager.bypass_phone_challenge():
            return False

        _update_progress(progress, account_task, completed=100, description="Account Created (Appium)!")
        return True
    except Exception as e:
        logger.error(f"Appium flow failed: {e}")
        return False
    finally:
        manager.close()
