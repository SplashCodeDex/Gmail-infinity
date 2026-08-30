"""
Flows Navigation - Reaching the Google signup form.

Extracted from runners.py: signup URL pools per flow mode, error-page
detection, direct URL rotation, google.com redirect route, and the
organic YouTube header route.
"""
import logging
import random

from core.warmup import WarmupEngine
from core.flows.shared import _update_progress

logger = logging.getLogger('gmail_creator_runners')

ERROR_PAGE_SIGNALS = [
    "something went wrong", "حدث خطأ ما", "try again later",
    "حاول مرة أخرى لاحقًا", "couldn't create your account",
    "تعذر إنشاء حسابك", "sorry, we couldn't sign you up",
    "this browser or app may not be secure",
    "المتصفح أو التطبيق غير آمن",
]


def get_signup_urls(flow_mode):
    if flow_mode == "youtube":
        return [
            "https://accounts.google.com/signup/v2/webcreateaccount?biz=false&cc=youtube&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26app%3Ddesktop%26hl%3Den%26next%3Dhttps%253A%252F%252Fwww.youtube.com%252F&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en",
            "https://accounts.google.com/signup/v2/createaccount?continue=https://www.youtube.com/&flowName=GlifWebSignIn&flowEntry=SignUp",
        ]
    elif flow_mode == "workspace":
        return [
            "https://accounts.google.com/lifecycle/steps/signup/name?continue=https://workspace.google.com/&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en",
            "https://accounts.google.com/signup/v2/createaccount?continue=https://workspace.google.com/&flowName=GlifWebSignIn&flowEntry=SignUp",
        ]
    else:
        return [
            "https://accounts.google.com/lifecycle/steps/signup/name?continue=https%3A%2F%2Fmyaccount.google.com%3Futm_source%3Daccount&dsh=S1527412391%3A" + str(random.randint(1000000000, 9999999999)) + "&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en&theme=glif",
            "https://accounts.google.com/signup/v2/webcreateaccount?biz=false&cc=youtube&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en",
            "https://accounts.google.com/lifecycle/steps/signup/name?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en-US&service=mail&theme=glif",
            "https://accounts.google.com/signup/v2/createaccount?biz=false&flowName=GlifWebSignIn&flowEntry=SignUp&hl=en",
            "https://accounts.google.com/lifecycle/steps/signup/name?continue=https%3A%2F%2Fplay.google.com&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en&theme=glif",
        ]


async def _looks_like_error_page(page):
    """Return True if the current page shows a known error/block signal."""
    try:
        page_content = (await page.content()).lower()
        page_url = page.url.lower()

        if any(sig in page_content for sig in ERROR_PAGE_SIGNALS):
            return "content_error"
        if "accounts.google.com/v3/signin/rejected" in page_url or "accounts.google.com/speedbump" in page_url:
            return "rejected_speedbump"
    except Exception:
        pass
    return None


async def _try_urls(page, signup_urls, progress, account_task):
    """Rotate through signup URLs until the name form appears."""
    navigated = False
    random.shuffle(signup_urls)

    for url_idx, url in enumerate(signup_urls):
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(1500, 3000))

            # Check for "Something went wrong" or error pages
            error_kind = await _looks_like_error_page(page)
            if error_kind == "content_error":
                logger.warning(f"Error page detected on URL #{url_idx+1}: {url[:60]}...")
                _update_progress(progress, account_task,
                                     description="[yellow]Error page detected, trying alternate URL...[/]")
                await page.wait_for_timeout(random.randint(3000, 6000))
                # Clear cookies and try again with next URL
                try:
                    await page.context.clear_cookies()
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass
                continue

            if error_kind == "rejected_speedbump":
                logger.warning(f"Rejected/speedbump page on URL #{url_idx+1}")
                await page.wait_for_timeout(random.randint(3000, 6000))
                continue

            el = await page.wait_for_selector('input[name="firstName"]', timeout=10000)
            if el:
                navigated = True
                break
        except Exception:
            logger.debug(f"Signup URL #{url_idx+1} failed, trying next...")
            await page.wait_for_timeout(random.randint(2000, 4000))
    return navigated


async def _try_google_redirect_route(page, progress, account_task):
    """Last resort: navigate to accounts.google.com/signin and click through."""
    try:
        logger.info("All signup URLs failed. Trying via google.com redirect...")
        _update_progress(progress, account_task,
                             description="[yellow]Trying alternate signup path...[/]")
        await page.goto("https://accounts.google.com/signin", timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        # Click "Create account"
        for create_sel in [
            "a:has-text('Create account')", "button:has-text('Create account')",
            "a:has-text('إنشاء حساب')", "span:has-text('Create account')",
        ]:
            try:
                el = await page.query_selector(create_sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                continue
        # Click "For my personal use"
        for personal_sel in [
            "li:has-text('For my personal use')", "span:has-text('For my personal use')",
            "li:has-text('لاستخدامي الشخصي')", "div:has-text('For my personal use')",
        ]:
            try:
                el = await page.query_selector(personal_sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                continue

        el = await page.wait_for_selector('input[name="firstName"]', timeout=10000)
        if el:
            return True
    except Exception:
        pass
    return False


async def _try_youtube_organic_route(page, progress, account_task):
    """YouTube header: Sign In -> Create account -> For my personal use."""
    try:
        logger.info("[FLOW] Attempting organic YouTube header Sign In -> Create Account route...")
        _update_progress(progress, account_task, description="[yellow]Trying organic YouTube route...[/]")
        await page.goto("https://www.youtube.com", timeout=25000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await WarmupEngine.dismiss_consent(page)

        for signin_sel in [
            "a[aria-label='Sign in']", "a:has-text('Sign in')",
            "ytd-button-renderer a[href*='accounts.google.com']",
            "a[href*='accounts.google.com/ServiceLogin']",
        ]:
            try:
                btn = await page.query_selector(signin_sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                continue

        for create_sel in [
            "button:has-text('Create account')", "a:has-text('Create account')",
            "span:has-text('Create account')", "a:has-text('إنشاء حساب')",
        ]:
            try:
                el = await page.query_selector(create_sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                continue

        for personal_sel in [
            "li:has-text('For my personal use')", "span:has-text('For my personal use')",
            "div:has-text('For my personal use')", "li:has-text('لاستخدامي الشخصي')",
        ]:
            try:
                el = await page.query_selector(personal_sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                continue

        el = await page.wait_for_selector('input[name="firstName"]', timeout=10000)
        if el:
            return True
    except Exception:
        pass
    return False


async def navigate_to_signup(page, flow_mode, progress, account_task):
    """Get the signup name form on screen by any route. Returns True on success."""
    signup_urls = get_signup_urls(flow_mode)
    navigated = await _try_urls(page, signup_urls, progress, account_task)

    if not navigated:
        navigated = await _try_google_redirect_route(page, progress, account_task)

    if not navigated and flow_mode == "youtube":
        navigated = await _try_youtube_organic_route(page, progress, account_task)

    return navigated
