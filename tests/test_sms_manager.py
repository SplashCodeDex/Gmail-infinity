"""Tests for services.sms_manager — check_balance key normalization."""
import asyncio

from config.settings import Config
from services import sms_manager


def _fake_async(value):
    async def _fn(*args, **kwargs):
        return value
    return _fn


class TestCheckBalanceKeys:
    def test_returns_canonical_keys(self, monkeypatch):
        monkeypatch.setattr(Config, "FIVESIM_API_KEY", "k5")
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "ksa")
        monkeypatch.setattr(sms_manager, "_get_5sim_balance", _fake_async(1.5))
        monkeypatch.setattr(sms_manager, "_get_sms_activate_balance", _fake_async(2.5))

        balances = asyncio.run(sms_manager.check_balance())

        # 'sms-activate' (not 'sms_activate') — matches /api/config key
        # used by the dashboard's SMS gateways card and the preflight check.
        assert balances == {"5sim": 1.5, "sms-activate": 2.5}

    def test_accepts_legacy_underscore_alias(self, monkeypatch):
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "ksa")
        monkeypatch.setattr(sms_manager, "_get_sms_activate_balance", _fake_async(2.5))

        balances = asyncio.run(sms_manager.check_balance("sms_activate"))
        assert balances == {"sms-activate": 2.5}

    def test_skips_unconfigured_services(self, monkeypatch):
        monkeypatch.setattr(Config, "FIVESIM_API_KEY", "")
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "ksa")
        monkeypatch.setattr(sms_manager, "_get_sms_activate_balance", _fake_async(9.0))

        balances = asyncio.run(sms_manager.check_balance())
        assert balances == {"sms-activate": 9.0}

    def test_swallows_provider_errors_to_none(self, monkeypatch):
        monkeypatch.setattr(Config, "FIVESIM_API_KEY", "k5")
        monkeypatch.setattr(Config, "SMS_ACTIVATE_API_KEY", "ksa")

        async def _boom(*args, **kwargs):
            raise RuntimeError("network down")

        monkeypatch.setattr(sms_manager, "_get_5sim_balance", _boom)
        monkeypatch.setattr(sms_manager, "_get_sms_activate_balance", _fake_async(2.5))

        balances = asyncio.run(sms_manager.check_balance())
        assert balances["5sim"] is None
        assert balances["sms-activate"] == 2.5