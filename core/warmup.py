import random
import logging
import time
from core.behavior import HumanBehavior

logger = logging.getLogger('gmail_creator_warmup')


class WarmupEngine:
    """Pre-browsing engine to build Google trust by visiting Google ecosystem sites with deep media telemetry."""

    GOOGLE_SITES = [
        "https://www.google.com",
        "https://www.youtube.com",
        "https://news.google.com",
        "https://maps.google.com",
        "https://play.google.com",
        "https://store.google.com",
        "https://translate.google.com",
        "https://scholar.google.com",
        "https://photos.google.com",
        "https://drive.google.com",
    ]

    GOOGLE_SEARCHES = [
        "best free email 2026", "how to create new email account",
        "google workspace features", "gmail tips and tricks",
        "weather today", "best restaurants near me",
        "latest technology news", "how to learn programming",
        "free online courses", "travel destinations 2026",
        "healthy recipes easy", "best movies this year",
    ]

    YOUTUBE_SEARCHES = [
        "lofi hip hop radio beats to relax",
        "relaxing nature 4k 60fps",
        "technology news and gadgets 2026",
        "top coding music background",
        "ambient space documentary 4k",
        "calm piano study music",
        "travel guide to switzerland 4k",
        "satisfying video compilation 2026",
    ]

    @staticmethod
    async def dismiss_consent(page):
        """Dismiss common Google and YouTube cookie/consent popups."""
        selectors = [
            "button:has-text('Accept all')", "button:has-text('I agree')",
            "button:has-text('Reject all')", "button:has-text('Accept')",
            "button[aria-label*='Accept']", "button[aria-label*='agree']",
            "#L2AGLb", ".tHlp8d", "ytd-button-renderer.ytd-consent-bump-v2-lightbox button",
            ".yt-spec-button-shape-next--filled",
        ]
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(600)
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    async def simulate_youtube_watch(page, min_watch_sec=15, max_watch_sec=30):
        """
        Dynamically search and stream a real YouTube video.
        Triggers HTML5 video telemetry, packet consumption, and VISITOR_INFO1_LIVE trust cookies.
        """
        logger.info("Warmup: Initiating dynamic YouTube video discovery & stream session...")
        try:
            current_url = page.url.lower()
            if "youtube.com" not in current_url:
                await page.goto("https://www.youtube.com", timeout=25000, wait_until="domcontentloaded")
                await page.wait_for_timeout(random.randint(1500, 2500))

            await WarmupEngine.dismiss_consent(page)
            await page.wait_for_timeout(random.randint(1000, 2000))

            video_opened = False
            use_search = random.random() < 0.65

            if use_search:
                query = random.choice(WarmupEngine.YOUTUBE_SEARCHES)
                logger.info(f"Warmup: Searching YouTube for '{query}'")

                # Try YouTube search input
                search_selectors = [
                    "input#search", "input[name='search_query']",
                    "input.ytSearchboxComponentInput", "input.ytd-searchbox",
                ]
                search_input = None
                for sel in search_selectors:
                    try:
                        search_input = await page.query_selector(sel)
                        if search_input and await search_input.is_visible():
                            break
                    except Exception:
                        continue

                if search_input:
                    await search_input.click()
                    await page.wait_for_timeout(random.randint(300, 600))
                    # Natural typing
                    for ch in query:
                        await page.keyboard.type(ch)
                        await page.wait_for_timeout(random.randint(35, 100))
                    await page.wait_for_timeout(random.randint(400, 800))
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(random.randint(3500, 6000))

                    # Click one of the first search results
                    result_selectors = [
                        "ytd-video-renderer a#video-title",
                        "ytd-video-renderer a#thumbnail",
                        "a#video-title-link",
                        "a#thumbnail",
                    ]
                    for r_sel in result_selectors:
                        try:
                            results = await page.query_selector_all(r_sel)
                            if results and len(results) > 1:
                                target = random.choice(results[:4])
                                await target.click(timeout=4000)
                                video_opened = True
                                break
                        except Exception:
                            continue

            # Fallback to homepage recommendation if search didn't open video
            if not video_opened:
                try:
                    await HumanBehavior.human_scroll(page, 1, 3)
                    await page.wait_for_timeout(random.randint(1000, 2000))
                    thumbnails = await page.query_selector_all("ytd-rich-item-renderer a#thumbnail, a#thumbnail")
                    if thumbnails and len(thumbnails) > 2:
                        target = random.choice(thumbnails[:6])
                        await target.click(timeout=4000)
                        video_opened = True
                except Exception as e:
                    logger.debug(f"Warmup: Thumbnail selection error: {e}")

            if video_opened:
                await page.wait_for_timeout(random.randint(2500, 4500))
                await WarmupEngine.dismiss_consent(page)

                # Ensure HTML5 video is actively playing and audio is simulated
                try:
                    is_playing = await page.evaluate("""() => {
                        const v = document.querySelector('video');
                        if (v) {
                            v.muted = false;
                            v.volume = 0.4 + Math.random() * 0.4;
                            if (v.paused) {
                                v.play().catch(() => {});
                            }
                            return !v.paused;
                        }
                        return false;
                    }""")
                    if not is_playing:
                        # Press 'k' or 'Space' to toggle play on player
                        await page.keyboard.press("k")
                except Exception:
                    pass

                watch_sec = random.randint(min_watch_sec, max_watch_sec)
                logger.info(f"Warmup: Actively streaming video for {watch_sec} seconds...")

                # Watch simulation loop: stream video while naturally interacting
                half_time = watch_sec // 2
                await page.wait_for_timeout(half_time * 1000)

                # Scroll down to inspect comments / related recommendations
                await HumanBehavior.human_scroll(page, 1, 2)
                await page.wait_for_timeout(random.randint(2000, 4000))

                # Scroll back up to the video player
                try:
                    await page.mouse.wheel(0, -random.randint(200, 500))
                    await page.wait_for_timeout(random.randint(1000, 2000))
                except Exception:
                    pass

                remaining = watch_sec - half_time - 3
                if remaining > 0:
                    await page.wait_for_timeout(remaining * 1000)

                logger.info("Warmup: YouTube video watch session completed successfully.")
                return True

        except Exception as e:
            logger.warning(f"Warmup: YouTube simulation notice: {e}")
            return False

    @staticmethod
    async def run_warmup(page, duration_minutes=3):
        """Build comprehensive Google trust through ecosystem browsing and real media consumption."""
        logger.info(f"Starting Google trust warmup for {duration_minutes} minutes...")

        end_time = time.time() + (duration_minutes * 60)

        # Step 1: Initial Google Home visit
        try:
            await page.goto("https://www.google.com", timeout=30000, wait_until="domcontentloaded")
            await WarmupEngine.dismiss_consent(page)
            await page.wait_for_timeout(random.randint(1000, 2000))
        except Exception:
            pass

        while time.time() < end_time:
            try:
                action = random.random()

                # Action 1 (35%): Google Organic Search & result visit
                if action < 0.35:
                    query = random.choice(WarmupEngine.GOOGLE_SEARCHES)
                    logger.info(f"Warmup: Google search '{query}'")
                    try:
                        await page.goto("https://www.google.com", timeout=20000, wait_until="domcontentloaded")
                        await WarmupEngine.dismiss_consent(page)
                        search_box = await page.query_selector("textarea[name='q'], input[name='q']")
                        if search_box:
                            await search_box.click()
                            await page.wait_for_timeout(random.randint(250, 500))
                            for ch in query:
                                await page.keyboard.type(ch)
                                await page.wait_for_timeout(random.randint(40, 110))
                            await page.wait_for_timeout(random.randint(500, 1000))
                            await page.keyboard.press("Enter")
                            await page.wait_for_timeout(random.randint(3000, 6000))
                            await HumanBehavior.human_scroll(page, 2, 4)

                            try:
                                results = await page.query_selector_all("a h3")
                                if results and len(results) > 1:
                                    target = random.choice(results[:5])
                                    await target.click(timeout=3000)
                                    await page.wait_for_timeout(random.randint(3000, 7000))
                                    await HumanBehavior.human_scroll(page, 1, 3)
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Action 2 (35%): YouTube Dynamic Search & Video Watch (High Trust Media Signal)
                elif action < 0.70:
                    await WarmupEngine.simulate_youtube_watch(page, min_watch_sec=15, max_watch_sec=30)

                # Action 3 (30%): Visit Google Ecosystem Sub-sites
                else:
                    site = random.choice(WarmupEngine.GOOGLE_SITES)
                    logger.info(f"Warmup: Visiting {site}")
                    try:
                        await page.goto(site, timeout=20000, wait_until="domcontentloaded")
                        await WarmupEngine.dismiss_consent(page)
                        await HumanBehavior.human_scroll(page, 2, 4)
                        await page.wait_for_timeout(random.randint(3000, 6000))
                    except Exception:
                        pass

                await page.wait_for_timeout(random.randint(2000, 5000))
            except Exception as e:
                logger.warning(f"Warmup error: {e}")
                continue

        try:
            await page.goto("https://accounts.google.com", timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(1500, 2500))
        except Exception:
            pass

        logger.info("Google trust warmup complete.")
        return True
