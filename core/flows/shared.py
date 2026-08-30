"""
Flows Shared - Common utilities for account creation flows.

Extracted from runners.py: failure capture, progress reporting,
page interaction helpers, and the immutable signup profile dataclass.
"""
import asyncio
import logging
import os
import re
import time

logger = logging.getLogger('gmail_creator_runners')

# Screenshot capture settings
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "screenshots")


async def capture_failure(page, tag, username=None):
    """Capture screenshot + URL + HTML snapshot when a step fails, for diagnosis."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        ident = f"_{username}" if username else ""
        base = os.path.join(SCREENSHOT_DIR, f"{ts}{ident}_{tag}")

        try:
            await page.screenshot(path=f"{base}.png", full_page=True)
            logger.debug(f"[SCREENSHOT] Saved: {base}.png")
        except Exception as shot_err:
            logger.debug(f"[SCREENSHOT] Screenshot failed: {shot_err}")

        try:
            with open(f"{base}_url.txt", "w", encoding="utf-8") as f:
                f.write(page.url)
        except Exception:
            pass

        try:
            with open(f"{base}_page.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
        except Exception:
            pass

        logger.error(f"[FAILURE-CAPTURE] tag={tag} url={page.url} files={base}.png")
    except Exception as cap_err:
        logger.debug(f"[FAILURE-CAPTURE] Failed to capture ({tag}): {cap_err}")


def _update_progress(progress, task, event_callback=None, **kwargs):
    if progress is not None and task is not None:
        progress.update(task, **kwargs)
    cb = event_callback or (getattr(progress, 'event_callback', None) if progress else None)
    desc = kwargs.get('description', '')
    if desc:
        clean_desc = re.sub(r'\[.*?\]', '', desc).strip()
        if clean_desc:
            logger.info(f"[FLOW] {clean_desc}")
            if cb:
                try:
                    cb('step', {'description': clean_desc, 'completed': kwargs.get('completed', 0)})
                except Exception:
                    pass


async def _try_click(page, selectors, is_mobile=False, timeout=5000):
    # Fast pass: check all selectors immediately without waiting
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                if is_mobile:
                    await el.tap()
                else:
                    await el.click()
                return True
        except Exception:
            continue
    # Slow pass: wait for first available selector
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=timeout)
            if el and await el.is_visible():
                if is_mobile:
                    await el.tap()
                else:
                    await el.click()
                return True
        except Exception:
            continue
    return False


async def _wait_for_page_change(page, old_url, timeout_s=10):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while loop.time() < deadline:
        try:
            if page.url != old_url:
                return True
        except Exception:
            pass
        await asyncio.sleep(0.4)
    return False


def parse_birthday(birthday_str):
    try:
        parts = birthday_str.strip().split()
        if len(parts) < 3:
            return "1", "1", "1990"
        month = str(int(parts[0]))
        day = str(int(parts[1]))
        year = str(int(parts[2]))
        if not (1 <= int(month) <= 12):
            month = "1"
        if not (1 <= int(day) <= 31):
            day = "1"
        if not (1900 <= int(year) <= 2010):
            year = "1990"
        return month, day, year
    except Exception:
        return "1", "1", "1990"
