"""
Flows Post-Registration - Modern Google post-registration multi-step UI.

Extracted from runners.py (_handle_post_registration_steps):
  1. Add Recovery Email (fills Config.RECOVERY_EMAIL or clicks Skip)
  2. Add Phone Number (optional screen -> clicks Skip)
  3. Review Account Info (clicks Next)
  4. Personalization Settings (chooses Express 1-step, clicks Next / Confirm)
  5. Privacy and Terms (solves Captcha if present, scrolls down, clicks I agree)
"""
import asyncio
import logging

from config.settings import Config
from core.flows.shared import _try_click, _update_progress

logger = logging.getLogger('gmail_creator_runners')

RECOVERY_SIGNALS = [
    "recovery email", "add recovery email", "recoveryemail",
    "بريد إلكتروني مخصص لاسترداد الحساب", "إضافة بريد إلكتروني",
]

PHONE_OPTIONAL_SIGNALS = [
    "add phone number", "add a phone number", "إضافة رقم هاتف",
    "add phone", "phone number",
]

REVIEW_SIGNALS = [
    "review your account info", "مراجعة معلومات حسابك",
    "review account", "reviewaccountinfo",
]

PERSONALIZATION_SIGNALS = [
    "choose personalization settings", "اختيار إعدادات التخصيص",
    "express personalization", "التخصيص السريع",
]

TERMS_SIGNALS = [
    "privacy and terms", "الخصوصية والبنود",
    "i agree", "أوافق", "agree",
    "terms of service", "بنود الخدمة",
]

GENERIC_SUBSCREEN_BUTTONS = [
    "button:has-text('I agree')", "button:has-text('أوافق')",
    "button:has-text('Confirm')", "button:has-text('تأكيد')",
    "button:has-text('Accept all')", "button:has-text('Next')",
    "button:has-text('Continue')", "button:has-text('Skip')",
    "button:has-text('تخطي')",
]

SIGNUP_LIFECYCLE_MARKERS = [
    "accounts.google.com/lifecycle", "accounts.google.com/signup",
    "accounts.google.com/signin/v2", "flowentry=signup",
]


async def _handle_recovery_email_screen(page, progress, account_task):
    recovery_email = getattr(Config, 'RECOVERY_EMAIL', '')
    if recovery_email:
        logger.info(f"[POST-REG] Entering recovery email: {recovery_email}")
        _update_progress(progress, account_task, description="Setting recovery email...")
        filled = False
        for sel in ['input[name="recoveryEmail"]', '#recoveryEmail', 'input[type="email"]', 'input[aria-label*="recovery" i]', 'input[aria-label*="استرداد" i]']:
            try:
                inp = await page.query_selector(sel)
                if inp and await inp.is_visible():
                    await inp.click()
                    await inp.fill(recovery_email)
                    await page.wait_for_timeout(500)
                    filled = True
                    break
            except Exception:
                continue
        if filled:
            await _try_click(page, ["button:has-text('Next')", "button:has-text('التالي')", "button[type='submit']", "div[role='button']:has-text('Next')"])
        else:
            await _try_click(page, ["button:has-text('Skip')", "button:has-text('تخطي')", "span:has-text('Skip')"])
    else:
        logger.info("[POST-REG] No recovery email configured -> clicking Skip")
        _update_progress(progress, account_task, description="Skipping recovery email...")
        await _try_click(page, [
            "button:has-text('Skip')", "button:has-text('تخطي')",
            "span:has-text('Skip')", "span:has-text('تخطي')",
        ])
    await page.wait_for_timeout(2500)


async def _handle_phone_optional_screen(page, progress, account_task):
    logger.info("[POST-REG] Optional phone screen detected -> clicking Skip")
    _update_progress(progress, account_task, description="Skipping optional phone...")
    return await _try_click(page, [
        "button:has-text('Skip')", "button:has-text('تخطي')",
        "span:has-text('Skip')", "span:has-text('تخطي')",
        "button:has-text('Not now')", "button:has-text('ليس الآن')",
    ])


async def _handle_review_screen(page, progress, account_task):
    logger.info("[POST-REG] Review account info screen detected -> clicking Next")
    _update_progress(progress, account_task, description="Confirming account details...")
    await _try_click(page, [
        "button:has-text('Next')", "button:has-text('التالي')",
        "button[type='submit']",
    ])
    await page.wait_for_timeout(2500)


async def _handle_personalization_screen(page, progress, account_task):
    logger.info("[POST-REG] Personalization settings detected -> selecting Express (1 step)")
    _update_progress(progress, account_task, description="Selecting express personalization...")
    try:
        for radio_sel in [
            "input[value='1']", "input[type='radio']",
            "div:has-text('Express personalization')",
            "span:has-text('Express personalization')",
        ]:
            r = await page.query_selector(radio_sel)
            if r and await r.is_visible():
                await r.click()
                await page.wait_for_timeout(500)
                break
    except Exception:
        pass

    await _try_click(page, [
        "button:has-text('Next')", "button:has-text('التالي')",
        "button:has-text('Confirm')", "button:has-text('تأكيد')",
        "button[type='submit']",
    ])
    await page.wait_for_timeout(2500)


async def _handle_terms_screen(page, progress, account_task):
    logger.info("[POST-REG] Privacy and terms screen detected -> accepting")
    _update_progress(progress, account_task, completed=92, description="Accepting terms of service...")

    # Solve Captcha if present
    try:
        captcha_frame = await page.query_selector('iframe[src*="recaptcha"], iframe[title*="reCAPTCHA"]')
        if captcha_frame:
            from core.captcha_solver import CaptchaSolver
            site_key = await page.evaluate("""() => {
                const el = document.querySelector('.g-recaptcha');
                return el ? el.getAttribute('data-sitekey') : null;
            }""")
            if site_key:
                token = await asyncio.to_thread(CaptchaSolver.solve, site_key, page.url)
                if token:
                    await page.evaluate("""(token) => {
                        const el = document.getElementById('g-recaptcha-response');
                        if (el) { el.value = token; el.style.display = 'none'; }
                    }""", token)
                    await page.wait_for_timeout(1000)
    except Exception:
        pass

    # Scroll to bottom of terms
    try:
        await page.mouse.wheel(0, 1500)
        await page.wait_for_timeout(800)
    except Exception:
        pass

    await _try_click(page, [
        "button:has-text('I agree')", "button:has-text('أوافق')",
        "button:has-text('Agree')", "button:has-text('Accept all')",
        "button:has-text('Confirm')", "button:has-text('تأكيد')",
        "button[type='submit']",
    ])
    await page.wait_for_timeout(3500)


async def _is_signup_lifecycle(url):
    return any(k in url for k in SIGNUP_LIFECYCLE_MARKERS)


async def handle_post_registration_steps(page, username, progress, account_task, is_mobile=False):
    """Walk through the post-signup screens until an authenticated page is reached."""
    logger.info("[POST-REG] Processing post-registration steps...")
    _update_progress(progress, account_task, completed=88, description="Configuring account settings...")

    for step_round in range(8):
        await page.wait_for_timeout(2000)
        try:
            current_url = page.url.lower()
            content = (await page.content()).lower()

            # Check if account is already complete / landed on authenticated dashboard
            is_signup_lifecycle = await _is_signup_lifecycle(current_url)
            if not is_signup_lifecycle:
                if current_url.startswith("https://myaccount.google.com") or current_url.startswith("https://mail.google.com"):
                    logger.info(f"[POST-REG] Reached authenticated destination URL: {current_url}")
                    return True

            # 1. Recovery Email Screen
            if any(s in content for s in RECOVERY_SIGNALS) or "recoveryemail" in current_url:
                await _handle_recovery_email_screen(page, progress, account_task)
                continue

            # 2. Add Phone Number (Optional) Screen
            if ("recoveryphone" in current_url or any(s in content for s in PHONE_OPTIONAL_SIGNALS)) and not ("verify your identity" in content or "confirm you're not a robot" in content):
                skip_clicked = await _handle_phone_optional_screen(page, progress, account_task)
                if skip_clicked:
                    await page.wait_for_timeout(2500)
                    continue

            # 3. Review Account Info Screen
            if any(s in content for s in REVIEW_SIGNALS) or "reviewaccount" in current_url:
                await _handle_review_screen(page, progress, account_task)
                continue

            # 4. Personalization Settings (Choose Express 1-step)
            if any(s in content for s in PERSONALIZATION_SIGNALS):
                await _handle_personalization_screen(page, progress, account_task)
                continue

            # 5. Terms & Privacy Agreement
            if any(s in content for s in TERMS_SIGNALS):
                await _handle_terms_screen(page, progress, account_task)
                continue

            # Generic Next / Confirm / Skip clicker for unexpected sub-screens
            clicked = await _try_click(page, GENERIC_SUBSCREEN_BUTTONS, timeout=1500)
            if not clicked:
                break

        except Exception as e:
            logger.debug(f"[POST-REG] Step error: {e}")
            break

    return True
