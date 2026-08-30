"""
Tests for core.strategy_engine — AdaptiveStrategyEngine scoring, pattern detection, cooldowns.
"""
from core.strategy_engine import AdaptiveStrategyEngine


class TestAdaptiveStrategyEngine:
    def test_default_neutral_score(self):
        engine = AdaptiveStrategyEngine()
        assert engine.get_strategy_score("standard") == 0.5

    def test_score_calculation_on_success(self):
        engine = AdaptiveStrategyEngine()
        # Record 10 fast successes
        for _ in range(10):
            engine.record_result("standard", success=True, duration=30.0)

        score = engine.get_strategy_score("standard")
        # 100% success rate with fast duration should score very high (> 0.9)
        assert score > 0.9

    def test_score_calculation_on_failure(self):
        engine = AdaptiveStrategyEngine()
        # Record failures
        for _ in range(3):
            engine.record_result("youtube", success=False, duration=100.0)

        score = engine.get_strategy_score("youtube")
        assert score < 0.3

    def test_cooldown_detection(self):
        engine = AdaptiveStrategyEngine()
        # Trigger 4 failures in last 5 attempts
        engine.record_result("workspace", True, 20.0)
        for _ in range(4):
            engine.record_result("workspace", False, 50.0)

        assert "workspace" in engine.cooldown_strategies
        score = engine.get_strategy_score("workspace")
        # Cooldown heavily penalizes score
        assert score < 0.2

    def test_temporary_ban_on_10_consecutive_failures(self):
        engine = AdaptiveStrategyEngine()
        for _ in range(10):
            engine.record_result("workspace", False, 50.0)

        assert "workspace" in engine.banned_strategies
        assert engine.get_strategy_score("workspace") == 0.0

    def test_select_strategy(self):
        engine = AdaptiveStrategyEngine()
        # Select from list returns one of the options
        strategies = ["standard", "youtube", "workspace"]
        selected = engine.select_strategy(strategies)
        assert selected in strategies

    def test_get_stats_summary(self):
        engine = AdaptiveStrategyEngine()
        engine.record_result("standard", True, 45.0)
        summary = engine.get_stats_summary()
        assert "standard" in summary
        assert summary["standard"]["attempts"] == 1
        assert summary["standard"]["successes"] == 1
        assert summary["standard"]["success_rate"] == 100.0
