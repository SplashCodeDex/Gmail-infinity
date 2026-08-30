"""
Sync entry point for the Playwright flow - bridges the synchronous
enhanced_creator loop to the async flow, applies Config defaults for
birthday/gender, and records the attempt in the retry engine.

Extracted from runners.py (run_playwright_flow).
"""
import asyncio
import logging

from config.settings import Config
from core.retry_engine import retry_engine as global_retry_engine
from core.flows.shared import parse_birthday
from core.flows.playwright_flow import async_playwright_flow

logger = logging.getLogger('gmail_creator_runners')


def run_playwright_flow(i, num_accounts, username, first_name, last_name, password,
                        progress, account_task, proxy,
                        month=None, day=None, year=None, gender=None,
                        use_sms_api=False, flow_mode="standard", headless=None,
                        retry_engine=None, event_callback=None):
    if month is None or day is None or year is None:
        b = getattr(Config, "YOUR_BIRTHDAY", "2 4 1990")
        month, day, year = parse_birthday(b)
    if gender is None:
        gender = str(getattr(Config, "YOUR_GENDER", "1"))

    result = asyncio.run(async_playwright_flow(
        i, num_accounts, username, first_name, last_name, password,
        progress, account_task, proxy, month, day, year, gender,
        use_sms_api, flow_mode, headless=headless,
        retry_engine=retry_engine, event_callback=event_callback,
    ))

    engine_to_use = retry_engine or global_retry_engine
    if isinstance(result, tuple):
        success, error_or_method = result
        if success:
            engine_to_use.record_attempt(flow_mode, True)
        else:
            engine_to_use.record_attempt(flow_mode, False, error_or_method)
        return success
    return result
