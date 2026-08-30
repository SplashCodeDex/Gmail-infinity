"""
Flows Prewarm - Google Trust-Building Pre-Warm session.

Extracted from runners.py (_google_prewarm): visits Google properties,
performs searches, YouTube watch, Maps, Translate, and warms
accounts.google.com before navigating to signup.
"""
import logging
import random

from core.warmup import WarmupEngine

logger = logging.getLogger('gmail_creator_runners')


async def _safe_goto(page, url, timeout=20000):
    try:
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        await page.wait_for_timeout(random.randint(2000, 5000))
        return True
    except Exception as e:
        logger.debug(f"[PREWARM] Navigation failed for {url}: {e}")
        return False


async def _accept_cookies(page):
    for sel in [
        "button:has-text('Accept all')", "button:has-text('I agree')",
        "button:has-text('Reject all')", "button:has-text('Accept')",
        "#L2AGLb", ".tHlp8d",
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.click()
                await page.wait_for_timeout(800)
                return
        except Exception:
            pass


async def _human_scroll(page, min_px=300, max_px=900):
    try:
        dist = random.randint(min_px, max_px)
        steps = random.randint(3, 8)
        for _ in range(steps):
            await page.mouse.wheel(0, dist // steps)
            await page.wait_for_timeout(random.randint(100, 300))
        await page.wait_for_timeout(random.randint(400, 900))
        back = random.randint(50, 200)
        await page.mouse.wheel(0, -back)
        await page.wait_for_timeout(random.randint(300, 700))
    except Exception:
        pass


async def _random_mouse_movement(page):
    try:
        x = random.randint(100, 800)
        y = random.randint(100, 500)
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await page.wait_for_timeout(random.randint(200, 600))
    except Exception:
        pass


async def _perform_search(page, query):
    try:
        search_box = await page.query_selector("textarea[name='q'], input[name='q']")
        if not search_box:
            return
        await search_box.click()
        await page.wait_for_timeout(random.randint(400, 800))
        for ch in query:
            await page.keyboard.type(ch)
            await page.wait_for_timeout(random.randint(50, 120))
        await page.wait_for_timeout(random.randint(500, 1000))
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(random.randint(3000, 6000))
        await _human_scroll(page)
        await _random_mouse_movement(page)
    except Exception:
        pass


async def _click_search_result(page):
    try:
        results = await page.query_selector_all("a h3")
        if results and len(results) > 1:
            target = random.choice(results[:5])
            await target.click(timeout=3000)
            await page.wait_for_timeout(random.randint(3000, 7000))
            await _human_scroll(page, 150, 500)
    except Exception:
        pass


async def google_prewarm(page):
    """Build Google ecosystem trust before opening the signup flow."""
    logger.info("[PREWARM] Starting Google trust-building session...")

    try:
        # 1. Google Home — establish cookies
        if await _safe_goto(page, "https://www.google.com"):
            await _accept_cookies(page)
            await _random_mouse_movement(page)
            await _human_scroll(page, 200, 400)

            # 2. Real search — builds activity signal
            searches = [
                "best free email service 2025", "how to create gmail account",
                "google workspace features", "gmail tips and tricks",
                "weather today", "latest news today",
            ]
            query = random.choice(searches)
            await _perform_search(page, query)
            await _click_search_result(page)

        # 3. YouTube — strong Google ecosystem signal (Dynamic search & stream telemetry)
        try:
            await WarmupEngine.simulate_youtube_watch(page, min_watch_sec=15, max_watch_sec=25)
        except Exception as yt_err:
            logger.debug(f"[PREWARM] YouTube warm notice: {yt_err}")

        # 4. Google Maps — adds location trust
        if await _safe_goto(page, "https://www.google.com/maps"):
            await page.wait_for_timeout(random.randint(3000, 5000))
            await _random_mouse_movement(page)

        # 5. Second Google search for variety
        if await _safe_goto(page, "https://www.google.com"):
            try:
                search_box = await page.query_selector("textarea[name='q'], input[name='q']")
                if search_box:
                    await search_box.click()
                    await page.wait_for_timeout(300)
                    query2 = random.choice(["new gmail features", "google account security", "best email provider"])
                    for ch in query2:
                        await page.keyboard.type(ch)
                        await page.wait_for_timeout(random.randint(50, 110))
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(random.randint(3000, 5000))
                    await _human_scroll(page, 200, 500)
            except Exception:
                pass

        # 6. Google Translate — adds another service signal
        if await _safe_goto(page, "https://translate.google.com"):
            await page.wait_for_timeout(random.randint(2000, 4000))
            try:
                textarea = await page.query_selector("textarea")
                if textarea:
                    text = random.choice(["hello world", "good morning", "thank you", "how are you"])
                    await textarea.click()
                    for ch in text:
                        await page.keyboard.type(ch)
                        await page.wait_for_timeout(random.randint(50, 120))
                    await page.wait_for_timeout(random.randint(2000, 4000))
            except Exception:
                pass

        # 7. Warm accounts.google.com domain — critical for trust
        try:
            await page.goto("https://accounts.google.com", timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(2000, 4000))
            await _random_mouse_movement(page)
        except Exception:
            pass

        logger.info("[PREWARM] Trust session built successfully.")

    except Exception as e:
        logger.warning(f"[PREWARM] Non-fatal error: {e}")
