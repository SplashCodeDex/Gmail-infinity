import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Project root = parent of this config/ directory. Anchors all relative
# paths regardless of the working directory the app was started from
# (root scripts, api/, web/, etc.).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env file (project root)
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger('gmail_creator_config')


class Config:
    # ═══════════════════════════════════════════════════════════════
    #                  ACCOUNT CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    YOUR_BIRTHDAY = os.getenv("YOUR_BIRTHDAY", "2 4 1990")
    YOUR_GENDER = os.getenv("YOUR_GENDER", "1")           # 1=Male, 2=Female, 3=Other
    YOUR_PASSWORD = os.getenv("YOUR_PASSWORD", "")
    RECOVERY_EMAIL = os.getenv("RECOVERY_EMAIL", "")

    # ═══════════════════════════════════════════════════════════════
    #                  SMS SERVICES
    # ═══════════════════════════════════════════════════════════════
    # 5sim
    FIVESIM_API_KEY = os.getenv("FIVESIM_API_KEY", "")
    FIVESIM_COUNTRY = os.getenv("FIVESIM_COUNTRY", "usa")
    FIVESIM_OPERATOR = os.getenv("FIVESIM_OPERATOR", "any")

    # SMS-Activate
    SMS_ACTIVATE_API_KEY = os.getenv("SMS_ACTIVATE_API_KEY", "")
    SMS_ACTIVATE_COUNTRY = os.getenv("SMS_ACTIVATE_COUNTRY", "0")

    # OnlineSIM
    ONLINESIM_API_KEY = os.getenv("ONLINESIM_API_KEY", "")
    ONLINESIM_COUNTRY = os.getenv("ONLINESIM_COUNTRY", "7")

    # GetSMS
    GETSMS_API_KEY = os.getenv("GETSMS_API_KEY", "")
    GETSMS_COUNTRY = os.getenv("GETSMS_COUNTRY", "us")

    # ═══════════════════════════════════════════════════════════════
    #                  CAPTCHA SERVICES
    # ═══════════════════════════════════════════════════════════════
    TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "")
    ANTICAPTCHA_API_KEY = os.getenv("ANTICAPTCHA_API_KEY", "")
    CAPMONSTER_API_KEY = os.getenv("CAPMONSTER_API_KEY", "")

    # ═══════════════════════════════════════════════════════════════
    #                  PROXY CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    ENABLE_PROXY = os.getenv("ENABLE_PROXY", "False").lower() == "true"
    PROXY_FILE = str(PROJECT_ROOT / os.getenv("PROXY_FILE", "config/proxies.txt"))
    PROXY_TYPE = os.getenv("PROXY_TYPE", "residential")  # residential / mobile / datacenter

    # Mobile Proxy
    MOBILE_PROXY_IP_CHANGE_URL = os.getenv("MOBILE_PROXY_IP_CHANGE_URL", "")
    PROXY_CHANGE_WAIT_TIME = int(os.getenv("PROXY_CHANGE_WAIT_TIME", "10"))

    # ═══════════════════════════════════════════════════════════════
    #                  BROWSER & ENGINE
    # ═══════════════════════════════════════════════════════════════
    ENGINE_MODE = os.getenv("ENGINE_MODE", "playwright")   # "appium", "playwright"
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "False").lower() == "true"
    BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30"))

    # ═══════════════════════════════════════════════════════════════
    #                  ANTI-DETECTION & BEHAVIOR
    # ═══════════════════════════════════════════════════════════════
    ENABLE_SESSION_WARMING = os.getenv("ENABLE_SESSION_WARMING", "True").lower() == "true"
    ENABLE_FINGERPRINT_MASKING = os.getenv("ENABLE_FINGERPRINT_MASKING", "True").lower() == "true"
    ENABLE_HUMAN_TYPING_ERRORS = os.getenv("ENABLE_HUMAN_TYPING_ERRORS", "True").lower() == "true"
    DELAY_BETWEEN_ACCOUNTS = int(os.getenv("DELAY_BETWEEN_ACCOUNTS", "30"))

    # ═══════════════════════════════════════════════════════════════
    #                  MAC ADDRESS ROTATION
    # ═══════════════════════════════════════════════════════════════
    ENABLE_MAC_ROTATION = os.getenv("ENABLE_MAC_ROTATION", "True").lower() == "true"

    # ═══════════════════════════════════════════════════════════════
    #                  RECOVERY CHAIN
    # ═══════════════════════════════════════════════════════════════
    ENABLE_RECOVERY_CHAIN = os.getenv("ENABLE_RECOVERY_CHAIN", "True").lower() == "true"

    # ═══════════════════════════════════════════════════════════════
    #                  ADVANCED STEALTH MODULES
    # ═══════════════════════════════════════════════════════════════
    ENABLE_CDP_INJECTION = os.getenv("ENABLE_CDP_INJECTION", "True").lower() == "true"
    ENABLE_GHOST_TYPER = os.getenv("ENABLE_GHOST_TYPER", "True").lower() == "true"
    ENABLE_POLTERGEIST = os.getenv("ENABLE_POLTERGEIST", "True").lower() == "true"

    # ═══════════════════════════════════════════════════════════════
    #                  NAMES & PATHS
    # ═══════════════════════════════════════════════════════════════
    USE_ARABIC_NAMES = os.getenv("USE_ARABIC_NAMES", "True").lower() == "true"
    NAMES_FILE = str(PROJECT_ROOT / os.getenv("NAMES_FILE", "data/names.txt"))

    # ═══════════════════════════════════════════════════════════════
    #                  LOGGING & EXPORT
    # ═══════════════════════════════════════════════════════════════
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
    LOG_FILE = str(PROJECT_ROOT / os.getenv("LOG_FILE", "data/gmail_creator.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    EXPORT_FORMAT = os.getenv("EXPORT_FORMAT", "txt")

    # ═══════════════════════════════════════════════════════════════
    #                  TELEGRAM NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    @classmethod
    def validate(cls):
        """Validate critical config on startup and warn about insecure defaults."""
        warnings = []

        if not cls.YOUR_PASSWORD:
            warnings.append("⚠️  YOUR_PASSWORD is empty in .env — accounts may use a default password!")

        sms_keys = [
            cls.FIVESIM_API_KEY, cls.SMS_ACTIVATE_API_KEY,
            cls.ONLINESIM_API_KEY, cls.GETSMS_API_KEY,
        ]
        if not any(sms_keys):
            warnings.append(
                "ℹ️  No SMS API key configured — Ghost Mode (free bypass) only. "
                "Add a key to .env for Premium Mode."
            )

        for w in warnings:
            logger.warning(w)

        return warnings
