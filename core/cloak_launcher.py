#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLOAK_LAUNCHER.PY - CloakBrowser Wrapper                  ║
║           Drop-in stealth Chromium with C++-level fingerprint patches        ║
║                   30/30 bot-detection tests passed                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

CloakBrowser is a patched Chromium binary — NOT JavaScript injection.
It replaces playwright-stealth and undetected-playwright entirely.

API is identical to Playwright — all existing code works unchanged.
"""

import asyncio
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Availability check — graceful fallback to plain Playwright if not installed
# ─────────────────────────────────────────────────────────────────────────────

try:
    from cloakbrowser import (
        launch_async,
        launch_persistent_context_async,
        launch_context,
    )
    CLOAKBROWSER_AVAILABLE = True
    logger.info("✅ CloakBrowser available — C++ stealth mode ACTIVE")
except ImportError:
    CLOAKBROWSER_AVAILABLE = False
    logger.warning(
        "⚠️  CloakBrowser not installed — falling back to plain Playwright.\n"
        "    Run:  pip install cloakbrowser && python -m cloakbrowser install"
    )


def _parse_proxy(proxy: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Parse proxy string into a dict that both CloakBrowser and Playwright accept.

    Supported formats:
      • http://user:pass@host:port
      • host:port:user:pass            (legacy project format)
      • host:port
    """
    if not proxy:
        return None

    # Already a URL?
    if proxy.startswith(("http://", "https://", "socks5://")):
        return {"server": proxy}

    # Legacy format: host:port:user:pass
    parts = proxy.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return {
            "server": f"http://{host}:{port}",
            "username": user,
            "password": password,
        }

    if len(parts) == 2:
        return {"server": f"http://{proxy}"}

    return {"server": proxy}


async def get_cloak_browser(
    proxy: Optional[str] = None,
    headless: bool = False,
    humanize: bool = True,
    human_preset: str = "careful",
    geoip: bool = True,
    timezone: Optional[str] = None,
    locale: Optional[str] = None,
    fingerprint_seed: Optional[int] = None,
    extra_args: Optional[list] = None,
    stealth_args: bool = True,
):
    """
    Launch a stealth CloakBrowser instance (async).

    Returns a standard Playwright ``Browser`` object — all Playwright methods
    work identically: ``new_page()``, ``new_context()``, ``close()``, etc.

    Falls back transparently to plain Playwright when CloakBrowser is not
    installed, so the rest of the codebase never needs an ``if`` check.

    Parameters
    ----------
    proxy : str, optional
        Proxy in any supported format (URL or ``host:port:user:pass``).
    headless : bool
        Run headless. For Gmail creation keep ``False``.
    humanize : bool
        Bézier mouse curves, per-character typing delays, realistic scroll.
    human_preset : str
        ``"default"`` (normal speed) or ``"careful"`` (slower, more deliberate).
    geoip : bool
        Auto-detect timezone & locale from proxy IP.
        Requires:  ``pip install "cloakbrowser[geoip]"``
    timezone : str, optional
        Override timezone (e.g. ``"America/New_York"``). Wins over geoip.
    locale : str, optional
        Override locale (e.g. ``"en-US"``). Wins over geoip.
    fingerprint_seed : int, optional
        Fixed seed → consistent fingerprint across sessions (good for reCAPTCHA v3).
        ``None`` → random seed every launch (different device every time).
    extra_args : list, optional
        Additional Chrome flags.
    stealth_args : bool
        Use CloakBrowser's built-in stealth args. Set ``False`` only to bring
        your own ``--fingerprint=...`` flags.
    """
    proxy_dict = _parse_proxy(proxy)

    if CLOAKBROWSER_AVAILABLE:
        kwargs: Dict[str, Any] = {
            "headless": headless,
            "humanize": humanize,
            "human_preset": human_preset,
            "stealth_args": stealth_args,
        }

        # Proxy
        if proxy_dict:
            kwargs["proxy"] = proxy_dict

        # GeoIP auto-detection (requires cloakbrowser[geoip])
        if proxy_dict and geoip:
            kwargs["geoip"] = True

        # Explicit timezone/locale override
        if timezone:
            kwargs["timezone"] = timezone
        if locale:
            kwargs["locale"] = locale

        # Fixed fingerprint seed
        if fingerprint_seed is not None:
            args = extra_args or []
            args.append(f"--fingerprint={fingerprint_seed}")
            kwargs["args"] = args
        elif extra_args:
            kwargs["args"] = extra_args

        browser = await launch_async(**kwargs)
        logger.info("🔒 CloakBrowser launched — stealth level: MAXIMUM (C++ patches)")
        return browser

    # ── Fallback: plain Playwright ─────────────────────────────────────────
    logger.warning("🟡 Using plain Playwright (no CloakBrowser stealth)")
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    launch_opts: Dict[str, Any] = {
        "headless": headless,
        "ignore_default_args": ["--enable-automation"],
        "args": (extra_args or []) + [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    }
    if proxy_dict:
        launch_opts["proxy"] = proxy_dict
    browser = await pw.chromium.launch(**launch_opts)
    return browser


async def get_cloak_persistent_context(
    profile_dir: Union[str, Path],
    proxy: Optional[str] = None,
    headless: bool = False,
    humanize: bool = True,
    human_preset: str = "careful",
    geoip: bool = True,
    timezone: Optional[str] = None,
    locale: Optional[str] = None,
    color_scheme: str = "light",
    viewport: Optional[Dict[str, int]] = None,
    user_agent: Optional[str] = None,
    fingerprint_seed: Optional[int] = None,
    storage_quota: Optional[int] = None,
):
    """
    Launch a persistent browser context (keeps cookies + localStorage across runs).

    Use this when you need to:
    - Stay logged in between sessions
    - Bypass incognito detection
    - Build a realistic browsing history

    Returns a Playwright ``BrowserContext`` object.
    """
    profile_dir = str(profile_dir)
    os.makedirs(profile_dir, exist_ok=True)
    proxy_dict = _parse_proxy(proxy)

    if CLOAKBROWSER_AVAILABLE:
        kwargs: Dict[str, Any] = {
            "headless": headless,
            "humanize": humanize,
            "human_preset": human_preset,
            "color_scheme": color_scheme,
        }
        if proxy_dict:
            kwargs["proxy"] = proxy_dict
        if proxy_dict and geoip:
            kwargs["geoip"] = True
        if timezone:
            kwargs["timezone"] = timezone
        if locale:
            kwargs["locale"] = locale
        if viewport:
            kwargs["viewport"] = viewport
        if user_agent:
            kwargs["user_agent"] = user_agent
        if fingerprint_seed is not None:
            kwargs["args"] = [f"--fingerprint={fingerprint_seed}"]
        # Adjust storage quota to avoid incognito detection on aggressive sites
        if storage_quota:
            existing_args = kwargs.get("args", [])
            existing_args.append(f"--fingerprint-storage-quota={storage_quota}")
            kwargs["args"] = existing_args

        ctx = await launch_persistent_context_async(profile_dir, **kwargs)
        logger.info(f"🔒 CloakBrowser persistent context: {profile_dir}")
        return ctx

    # ── Fallback: plain Playwright persistent context ──────────────────────
    logger.warning("🟡 Persistent context via plain Playwright (no CloakBrowser stealth)")
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    ctx_opts: Dict[str, Any] = {
        "headless": headless,
        "ignore_default_args": ["--enable-automation"],
        "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    }
    if proxy_dict:
        ctx_opts["proxy"] = proxy_dict
    if viewport:
        ctx_opts["viewport"] = viewport
    if locale:
        ctx_opts["locale"] = locale
    if timezone:
        ctx_opts["timezone_id"] = timezone
    if user_agent:
        ctx_opts["user_agent"] = user_agent
    if color_scheme:
        ctx_opts["color_scheme"] = color_scheme

    ctx = await pw.chromium.launch_persistent_context(profile_dir, **ctx_opts)
    return ctx


def is_available() -> bool:
    """Return True if CloakBrowser binary is installed and ready."""
    return CLOAKBROWSER_AVAILABLE
