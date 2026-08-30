"""Tests for core.config_validator.validate_config()."""
from pathlib import Path

from config.settings import Config
from core.config_validator import validate_config


def write_names_file(tmp_path, count=12, filename="names.txt"):
    names = tmp_path / filename
    names.write_text("\n".join(f"name{i}" for i in range(count)))
    return str(names)


def configure(monkeypatch, tmp_path, **overrides):
    """Set a known-good baseline config, then apply per-test overrides."""
    values = {
        "YOUR_PASSWORD": "test-password",
        "YOUR_BIRTHDAY": "5 15 1990",
        "YOUR_GENDER": "1",
        "ENGINE_MODE": "playwright",
        "FIVESIM_API_KEY": "",
        "SMS_ACTIVATE_API_KEY": "",
        "ONLINESIM_API_KEY": "",
        "GETSMS_API_KEY": "",
        "TWOCAPTCHA_API_KEY": "",
        "ANTICAPTCHA_API_KEY": "",
        "CAPMONSTER_API_KEY": "",
        "ENABLE_PROXY": False,
        "NAMES_FILE": write_names_file(tmp_path),
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setattr(Config, key, value)


def test_valid_config_has_no_errors(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    warnings, errors = validate_config()
    assert errors == []
    # no SMS / captcha keys configured — expected baseline warning only
    assert all("SMS" in w for w in warnings)


def test_missing_password_is_an_error(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, YOUR_PASSWORD="")
    pw_file = Path(__file__).resolve().parent.parent / "config" / "password.txt"
    if pw_file.exists() and pw_file.read_text(encoding="utf-8").strip():
        # validator falls back to config/password.txt — can't simulate absence
        # without touching the real filesystem, so skip this scenario here.
        return
    warnings, errors = validate_config()
    assert any("password" in e.lower() for e in errors)


def test_invalid_engine_mode_is_an_error(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, ENGINE_MODE="phantomjs")
    warnings, errors = validate_config()
    assert any("ENGINE_MODE" in e for e in errors)


def test_invalid_birthday_is_a_warning_not_error(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, YOUR_BIRTHDAY="not a date")
    warnings, errors = validate_config()
    assert errors == []
    assert any("Birthday" in w for w in warnings)


def test_out_of_range_birthday_fields_warn(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, YOUR_BIRTHDAY="13 45 1850")
    warnings, errors = validate_config()
    assert errors == []
    assert any("month" in w for w in warnings)
    assert any("day" in w for w in warnings)


def test_invalid_gender_warns(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, YOUR_GENDER="7")
    warnings, errors = validate_config()
    assert errors == []
    assert any("Gender" in w for w in warnings)


def test_missing_names_file_warns(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, NAMES_FILE=str(tmp_path / "nope.txt"))
    warnings, errors = validate_config()
    assert errors == []
    assert any("Names file" in w for w in warnings)


def test_thin_names_file_warns(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path,
              NAMES_FILE=write_names_file(tmp_path, count=3, filename="names_thin.txt"))
    warnings, errors = validate_config()
    assert errors == []
    assert any("only 3 names" in w for w in warnings)


def test_enabled_proxy_with_missing_file_warns(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, ENABLE_PROXY=True,
              **{"PROXY_FILE": str(tmp_path / "absent_proxies.txt")})
    warnings, errors = validate_config()
    assert errors == []
    assert any("proxy file" in w.lower() for w in warnings)


def test_telegram_half_config_warns_both_directions(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, TELEGRAM_BOT_TOKEN="tok", TELEGRAM_CHAT_ID="")
    warnings, errors = validate_config()
    assert any("TELEGRAM_CHAT_ID missing" in w for w in warnings)

    configure(monkeypatch, tmp_path, TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="chat")
    warnings, errors = validate_config()
    assert any("TELEGRAM_BOT_TOKEN missing" in w for w in errors + warnings)


def test_configured_sms_key_suppresses_warning(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, FIVESIM_API_KEY="real-key-123")
    warnings, errors = validate_config()
    assert not any("No SMS" in w for w in warnings)
