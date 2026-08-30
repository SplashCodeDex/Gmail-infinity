"""
Flows Steps - Strict state-gated Google signup form interactions.

Extracted from runners.py: name entry, birthday & gender, username
selection with retry-on-taken, password entry, and the QR-escape
refill sequence. Each step blocks until the next screen is confirmed.
"""
import asyncio
import logging
import random
import string

from core.flows.shared import _try_click, _update_progress
from core.retry_engine import CreationError

logger = logging.getLogger('gmail_creator_runners')

NEXT_BUTTONS = [
    "button:has-text('Next')", "button:has-text('التالي')",
    "button[type='submit']",
]

NAME_NEXT_BUTTONS = [
    "#collectNameNext button", "button:has-text('Next')", "button:has-text('التالي')",
    "div[role='button']:has-text('Next')", "button[type='button']:has-text('Next')",
    "#collectNameNext", "button[type='submit']",
]

BIRTHDAY_NEXT_BUTTONS = [
    "button:has-text('Next')", "button:has-text('التالي')",
    "#birthdaygenderNext", "button[type='submit']",
]

USERNAME_NEXT_BUTTONS = [
    "button:has-text('Next')", "button:has-text('التالي')", "#next", "button[type='submit']",
]

PASSWORD_NEXT_BUTTONS = [
    "button:has-text('Next')", "button:has-text('التالي')", "#passwdNext", "button[type='submit']",
]

USERNAME_SELECTORS = [
    'input[name="Username"]', 'input[name="username"]', 'input[name="identifier"]',
    'input[name="GmailAddress"]', 'input[type="email"]',
    'input[type="text"][autocomplete="username"]',
    'input[aria-label*="username" i]', 'input[aria-label*="Gmail address" i]',
    'input[aria-label*="Create a Gmail address" i]', 'input[aria-label*="عنوان Gmail" i]',
    'input[placeholder*="username" i]', 'input[placeholder*="Gmail" i]',
]

TAKEN_SIGNALS = [
    "that username is taken", "username is taken", "try another",
    "اسم المستخدم مأخوذ", "جرب اسمًا آخر", "this username is not available",
]

GENDER_ERRORS = [
    "please select your gender", "select your gender",
    "يُرجى تحديد الجنس", "حدد جنسك",
    "enter your birthday", "أدخل تاريخ ميلادك",
]


async def _await_step(page, url_fragments, selector_list, repress_selectors, max_retries=20):
    """Poll until one of url_fragments matches or a selector in selector_list appears.

    Every 6th miss, presses Enter and clicks repress_selectors to unstick the flow.
    Returns True when the next step is ready, False on timeout.
    """
    for _retry in range(max_retries):
        for frag in url_fragments:
            if frag in page.url:
                return True
        for sel in selector_list:
            if await page.query_selector(sel):
                return True
        await page.wait_for_timeout(500)

        # Re-attempt click every 3 seconds if not ready
        if _retry % 6 == 5:
            await page.keyboard.press("Enter")
            await _try_click(page, repress_selectors)
    return False


async def fill_name_step(page, manager, first_name, last_name, username, progress, account_task):
    """Enter first/last name and advance. Returns (True, None) or (False, error)."""
    _update_progress(progress, account_task, completed=30, description="Entering name...")

    typed_first = await manager.natural_type("input[name='firstName']", first_name)
    if not typed_first:
        try:
            el = await page.query_selector("input[name='firstName']")
            if el:
                await el.fill(first_name)
        except Exception:
            pass
    await page.wait_for_timeout(400)

    # Dispatch events for React/Lit to register dirty state
    await page.evaluate("document.querySelector('input[name=\"firstName\"]')?.dispatchEvent(new Event('input', {bubbles: true}));")
    await page.evaluate("document.querySelector('input[name=\"firstName\"]')?.dispatchEvent(new Event('change', {bubbles: true}));")

    typed_last = await manager.natural_type("input[name='lastName']", last_name)
    if not typed_last:
        try:
            el = await page.query_selector("input[name='lastName']")
            if el:
                await el.fill(last_name)
        except Exception:
            pass
    await page.wait_for_timeout(600)

    await page.evaluate("document.querySelector('input[name=\"lastName\"]')?.dispatchEvent(new Event('input', {bubbles: true}));")
    await page.evaluate("document.querySelector('input[name=\"lastName\"]')?.dispatchEvent(new Event('change', {bubbles: true}));")

    # Fallback native submit
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(500)

    await _try_click(page, NAME_NEXT_BUTTONS)

    # STRICT STATE GATING: Actively wait for Birthday & Gender step
    birthday_ready = await _await_step(
        page,
        url_fragments=["signup/birthday"],
        selector_list=['select#month, select[name="month"], #month, input[name="day"], #day'],
        repress_selectors=NAME_NEXT_BUTTONS,
    )
    if not birthday_ready:
        logger.error("NAME_STEP_FAILED: Failed to advance past Name step.")
        return False, CreationError.FLOW_ERROR
    return True, None


async def fill_birthday_step(page, manager, month, day, year, gender, username, progress, account_task):
    """Fill birthday & gender, advance, and retry on validation errors."""
    _update_progress(progress, account_task, completed=50, description="Entering birthday & gender...")
    await manager.fill_birthday_gender(month, day, year, gender)
    await page.wait_for_timeout(600)

    await _try_click(page, BIRTHDAY_NEXT_BUTTONS)
    await page.wait_for_timeout(2000)

    # Check if gender error appeared — retry if so
    for _gender_retry in range(3):
        try:
            page_text = await page.content()
            if any(err in page_text.lower() for err in GENDER_ERRORS):
                logger.warning(f"Gender/birthday error detected (retry {_gender_retry+1})")
                _update_progress(progress, account_task, description="Retrying gender selection...")
                await manager.fill_birthday_gender(month, day, year, gender)
                await page.wait_for_timeout(800)
                await _try_click(page, BIRTHDAY_NEXT_BUTTONS)
                await page.wait_for_timeout(2500)
            else:
                break
        except Exception:
            break

    # STRICT GATING FOR USERNAME STEP
    username_ready = await _await_step(
        page,
        url_fragments=["signup/username", "signup/createpassword"],
        selector_list=['input[name="Username"], input[name="username"], input[type="radio"]'],
        repress_selectors=["#birthdaygenderNext button", "button:has-text('Next')"],
    )
    if not username_ready:
        logger.error("BIRTHDAY_STEP_FAILED: Failed to advance past Birthday step.")
        return False, CreationError.FLOW_ERROR
    return True, None


async def find_username_field(page):
    for sel in USERNAME_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                return el
        except Exception:
            continue
    return None


async def _reveal_custom_username_field(page):
    """Try the 'Create your own Gmail address' affordances when no input is visible."""
    try:
        loc = page.locator("text=Create your own Gmail address").or_(
            page.locator("text=إنشاء عنوان Gmail"))
        if await loc.count() > 0:
            await loc.first.click()
            await page.wait_for_timeout(1500)
    except Exception:
        pass

    if not await find_username_field(page):
        try:
            radios = await page.query_selector_all("input[type='radio']")
            if radios:
                await radios[-1].scroll_into_view_if_needed()
                await radios[-1].click()
                await page.wait_for_timeout(1500)
        except Exception:
            pass

    if not await find_username_field(page):
        try:
            await page.evaluate("""() => {
                for (const el of document.querySelectorAll('label,span,div')) {
                    if (el.textContent.trim().includes('Create your own') ||
                        el.textContent.trim().includes('إنشاء عنوان Gmail')) {
                        el.click(); break;
                    }
                }
            }""")
            await page.wait_for_timeout(1500)
        except Exception:
            pass

    for _ in range(16):
        if await find_username_field(page):
            return
        await asyncio.sleep(0.5)


def _make_alt_username(base, attempt, first_name, last_name):
    suffixes = [
        str(random.randint(100, 9999)),
        "".join(random.choices(string.ascii_lowercase, k=3)),
        str(random.randint(10, 99)) + random.choice(string.ascii_lowercase),
        first_name.lower() + str(random.randint(10, 999)),
        last_name.lower() + str(random.randint(10, 999)),
    ]
    return base.rstrip("0123456789") + suffixes[attempt % len(suffixes)]


async def choose_username_step(page, username, first_name, last_name, progress, account_task):
    """Choose a Gmail username, retrying with variations when taken.

    Returns (True, final_username) or (False, error_code).
    """
    _update_progress(progress, account_task, completed=60, description="Choosing Gmail username...")
    await page.wait_for_timeout(2000)

    username_field = await find_username_field(page)
    if not username_field:
        await _reveal_custom_username_field(page)

    current_username = username
    max_username_retries = 5

    for attempt in range(max_username_retries):
        username_field = await find_username_field(page)
        if not username_field:
            await page.evaluate("""(u) => {
                const sels = ['input[name="Username"]','input[name="username"]',
                              'input[autocomplete="username"]','input[type="text"]'];
                for (const s of sels) {
                    const el = document.querySelector(s);
                    if (el && el.offsetParent !== null) {
                        el.focus(); el.value = u;
                        el.dispatchEvent(new Event('input',{bubbles:true}));
                        el.dispatchEvent(new Event('change',{bubbles:true}));
                        break;
                    }
                }
            }""", current_username)
        else:
            await username_field.scroll_into_view_if_needed()
            await username_field.click()
            await page.wait_for_timeout(200)
            await username_field.click(click_count=3)
            await page.wait_for_timeout(100)
            await username_field.fill(current_username)
            await username_field.dispatch_event("input")
            await username_field.dispatch_event("change")
            await page.wait_for_timeout(800)

        await page.wait_for_timeout(600)
        await _try_click(page, USERNAME_NEXT_BUTTONS)
        await page.wait_for_timeout(3000)

        try:
            page_text = await page.content()
            if any(s.lower() in page_text.lower() for s in TAKEN_SIGNALS):
                if attempt < max_username_retries - 1:
                    current_username = _make_alt_username(current_username, attempt, first_name, last_name)
                    _update_progress(progress, account_task,
                                     description=f"[yellow]Username taken -> retrying: {current_username}[/]")
                    await page.wait_for_timeout(1200)
                    continue
                else:
                    return False, CreationError.USERNAME_TAKEN
            else:
                username = current_username
                break
        except Exception:
            break

    # STRICT GATING FOR PASSWORD STEP
    password_ready = await _await_step(
        page,
        url_fragments=["signup/createpassword"],
        selector_list=['input[name="Passwd"], input[type="password"]'],
        repress_selectors=["button:has-text('Next')", "#next"],
    )
    if not password_ready:
        logger.error("USERNAME_STEP_FAILED: Failed to advance past Username step.")
        return False, CreationError.FLOW_ERROR
    return True, username


async def fill_password_step(page, password, progress, account_task):
    """Fill password + confirmation and advance to verification."""
    _update_progress(progress, account_task, completed=70, description="Entering password...")

    for sel in ['input[name="Passwd"]', 'input[type="password"]', 'input[aria-label*="password" i]']:
        try:
            pw_el = await page.wait_for_selector(sel, timeout=10000)
            if pw_el and await pw_el.is_visible():
                await pw_el.click()
                await page.wait_for_timeout(200)
                await pw_el.fill(password)
                break
        except Exception:
            continue

    for sel in ['input[name="PasswdAgain"]', 'input[name="ConfirmPasswd"]',
                'input[aria-label*="Confirm" i]']:
        try:
            cp_el = await page.query_selector(sel)
            if cp_el and await cp_el.is_visible():
                await cp_el.click()
                await page.wait_for_timeout(200)
                await cp_el.fill(password)
                break
        except Exception:
            continue

    await page.wait_for_timeout(600)
    await _try_click(page, PASSWORD_NEXT_BUTTONS)
    await page.wait_for_timeout(4000)


async def refill_after_qr_escape(page, manager, first_name, last_name, username,
                                 password, month, day, year, gender, is_mobile,
                                 progress, account_task, method):
    """Re-fill name, birthday, username, and password after a QR escape restart.

    Returns (True, None) or (False, error_code).
    """
    _update_progress(progress, account_task, completed=25,
                     description=f"[green]Escaped {method} — restarting from name...[/]")
    await page.wait_for_timeout(1200)

    try:
        typed = await manager.natural_type("input[name='firstName']", first_name)
        if not typed:
            el = await page.query_selector("input[name='firstName']")
            if el:
                await el.fill(first_name)
        await page.wait_for_timeout(400)
        typed = await manager.natural_type("input[name='lastName']", last_name)
        if not typed:
            el = await page.query_selector("input[name='lastName']")
            if el:
                await el.fill(last_name)
        await page.wait_for_timeout(600)
        await _try_click(page, [
            "button:has-text('Next')", "button:has-text('التالي')",
            "#collectNameNext", "button[type='submit']",
        ])
        await page.wait_for_timeout(3000)
    except Exception as e:
        logger.error(f"Failed to re-enter name after QR escape: {e}")
        return False, CreationError.QR_BLOCKED

    await manager.fill_birthday_gender(month, day, year, gender)
    await page.wait_for_timeout(600)
    await _try_click(page, ["button:has-text('Next')", "button:has-text('التالي')", "#birthdaygenderNext", "button[type='submit']"],
                     is_mobile=is_mobile)
    await page.wait_for_timeout(3000)

    # Re-enter username
    try:
        radios = await page.query_selector_all("input[type='radio']")
        if radios:
            await radios[-1].scroll_into_view_if_needed()
            await radios[-1].click()
            await page.wait_for_timeout(1000)

        for sel in ['input[name="Username"]', 'input[name="username"]', 'input[type="text"]']:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(username)
                await page.wait_for_timeout(500)
                break

        await _try_click(page, USERNAME_NEXT_BUTTONS)
        await page.wait_for_timeout(3000)
    except Exception:
        pass

    # Re-enter password
    try:
        for sel in ['input[name="Passwd"]', 'input[type="password"]']:
            pw_el = await page.query_selector(sel)
            if pw_el and await pw_el.is_visible():
                await pw_el.fill(password)
                break
        for sel in ['input[name="PasswdAgain"]', 'input[aria-label*="Confirm" i]']:
            pw2_el = await page.query_selector(sel)
            if pw2_el and await pw2_el.is_visible():
                await pw2_el.fill(password)
                break
        await page.wait_for_timeout(500)
        await _try_click(page, PASSWORD_NEXT_BUTTONS)
        await page.wait_for_timeout(3000)
    except Exception:
        pass

    return True, None
