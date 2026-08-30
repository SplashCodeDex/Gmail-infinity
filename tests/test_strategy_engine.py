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

    def test_load_historical_learning_from_db(self):
        class MockDB:
            def get_recent_strategy_stats(self, limit_sessions=20):
                return [
                    {
                        "strategy": "standard",
                        "total_attempts": 10,
                        "total_successes": 9,
                        "total_failures": 1,
                        "avg_time": 25.0,
                    },
                    {
                        "strategy": "youtube",
                        "total_attempts": 10,
                        "total_successes": 1,
                        "total_failures": 9,
                        "avg_time": 60.0,
                    }
                ]

        engine = AdaptiveStrategyEngine(db=MockDB())
        assert engine.strategy_stats["standard"]["attempts"] == 10
        assert engine.strategy_stats["standard"]["successes"] == 9
        assert engine.strategy_stats["youtube"]["attempts"] == 10
        assert engine.strategy_stats["youtube"]["successes"] == 1

        # Real scoring: standard (90% success) >> youtube (10% success)
        assert engine.get_strategy_score("standard") > 0.8
        assert engine.get_strategy_score("youtube") < 0.35


class TestSessionDeltaPersistence:
    """Session-local deltas must not be contaminated by seeded history."""

    def test_session_stats_are_delta_only(self):
        class MockDB:
            def get_recent_strategy_stats(self, limit_sessions=20):
                return [{
                    "strategy": "standard",
                    "total_attempts": 10,
                    "total_successes": 9,
                    "total_failures": 1,
                    "avg_time": 25.0,
                }]

        engine = AdaptiveStrategyEngine(db=MockDB())
        # Seeded history feeds scoring...
        assert engine.strategy_stats["standard"]["attempts"] == 10
        # ...but must NOT appear in the session delta intended for persistence
        assert "standard" not in engine.get_session_stats()

        engine.record_result("standard", True, 30.0)
        engine.record_result("standard", False, 60.0)

        delta = engine.get_session_stats()["standard"]
        assert delta["attempts"] == 2
        assert delta["successes"] == 1
        assert delta["failures"] == 1
        # EMA mixing for the two new results
        assert delta["avg_time"] == 0.7 * 30.0 + 0.3 * 60.0

        # Cumulative estimate still includes the seed for scoring
        total = engine.strategy_stats["standard"]
        assert total["attempts"] == 12
        assert total["successes"] == 10

    def test_session_stats_empty_before_any_results(self):
        class MockDB:
            def get_recent_strategy_stats(self, limit_sessions=20):
                return [{
                    "strategy": "standard",
                    "total_attempts": 10,
                    "total_successes": 9,
                    "total_failures": 1,
                    "avg_time": 25.0,
                }]

        engine = AdaptiveStrategyEngine(db=MockDB())
        assert engine.get_session_stats() == {}

    def test_avg_time_ema_across_results(self):
        engine = AdaptiveStrategyEngine()
        engine.record_result("standard", True, 10.0)
        engine.record_result("standard", True, 30.0)
        delta = engine.get_session_stats()["standard"]
        assert delta["attempts"] == 2
        assert delta["avg_time"] == 16.0  # 0.7 * 10 + 0.3 * 30


