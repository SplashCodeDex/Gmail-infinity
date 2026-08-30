"""
Identity generation - shared name/password generators.

Relocated from core.selenium_runner (retired) so the Playwright engine
does not depend on Selenium code.
"""
import random
import string

from config.settings import Config


def _load_names():
    names_file = Config.NAMES_FILE if hasattr(Config, 'NAMES_FILE') else "data/names.txt"
    names = []
    try:
        with open(names_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    names.append(line)
    except FileNotFoundError:
        pass
    return names


_names_list = _load_names()


def generate_name():
    if _names_list:
        return random.choice(_names_list)
    return f"User{random.randint(1000, 9999)}"


def generate_password(length=14):
    """Generate a strong unique password per account."""
    upper = random.choices(string.ascii_uppercase, k=3)
    lower = random.choices(string.ascii_lowercase, k=5)
    digits = random.choices(string.digits, k=3)
    specials = random.choices("!@#$%&*", k=2)
    filler = random.choices(string.ascii_letters + string.digits, k=max(0, length - 13))
    pool = upper + lower + digits + specials + filler
    random.shuffle(pool)
    return "".join(pool)
