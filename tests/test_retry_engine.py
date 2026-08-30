"""Tests for core.retry_engine — retry decisions, strategy rotation and scoring."""
import pytest

from core.retry_engine import CreationError, RetryEngine


@pytest.fixture
def engine():
    return RetryEngine()


class TestShouldRetry:
    def test_retries_below_max(self, engine):
        assert engine.should_retry(CreationError.TIMEOUT, 0) is True
        assert engine.should_retry(CreationError.TIMEOUT, RetryEngine.MAX_RETRIES - 1) is True

    def test_stops_at_max_retries(self, engine):
        assert engine.should_retry(CreationError.TIMEOUT, RetryEngine.MAX_RETRIES) is False

    def test_username_taken_always_retryable(self, engine):
        assert engine.should_retry(CreationError.USERNAME_TAKEN, 0) is True

    def test_ip_flagged_gives_up_after_two_attempts(self, engine):
        assert engine.should_retry(CreationError.IP_FLAGGED, 1) is True
        assert engine.should_retry(CreationError.IP_FLAGGED, 2) is False


class TestGetNextStrategy:
    def test_never_returns_the_failed_strategy(self, engine):
        for error_type in (CreationError.QR_BLOCKED, CreationError.TIMEOUT, CreationError.UNKNOWN):
            for failed in engine.STRATEGIES:
                nxt = engine.get_next_strategy(failed, error_type)
                assert nxt != failed
                assert nxt in engine.STRATEGIES

    def test_username_taken_keeps_same_strategy(self, engine):
        assert engine.get_next_strategy("youtube", CreationError.USERNAME_TAKEN) == "youtube"

    def test_error_specific_candidates_preferred(self, engine):
        nxt = engine.get_next_strategy("standard", CreationError.QR_BLOCKED)
        assert nxt in ["youtube", "workspace", "mobile_ua"]


class TestCooldown:
    def test_cooldown_scales_with_attempt_count(self, engine):
        short = engine.get_cooldown(0, CreationError.TIMEOUT)
        long = engine.get_cooldown(2, CreationError.TIMEOUT)
        assert long > short

    def test_ip_flagged_cooldown_is_longer(self, engine):
        base = engine.get_cooldown(1, CreationError.TIMEOUT)
        flagged = engine.get_cooldown(1, CreationError.IP_FLAGGED)
        assert flagged >= base * 2  # 3x multiplier, jitter floors at 0.8

    def test_cooldown_is_non_negative_int(self, engine):
        for error in CreationError.__dict__.values():
            assert isinstance(engine.get_cooldown(1, error), int)
            assert engine.get_cooldown(1, error) >= 0


class TestScoring:
    def test_success_raises_score(self, engine):
        before = engine._strategy_scores["standard"]
        engine.record_attempt("standard", success=True)
        assert engine._strategy_scores["standard"] == before + 15

    def test_failure_lowers_score(self, engine):
        before = engine._strategy_scores["standard"]
        engine.record_attempt("standard", success=False, error_type=CreationError.TIMEOUT)
        assert engine._strategy_scores["standard"] == before - 10

    def test_scores_clamped_to_bounds(self, engine):
        for _ in range(20):
            engine.record_attempt("standard", success=True)
        assert engine._strategy_scores["standard"] == 100
        for _ in range(20):
            engine.record_attempt("standard", success=False)
        assert engine._strategy_scores["standard"] == 0

    def test_stats_reflect_history(self, engine):
        engine.record_attempt("standard", True)
        engine.record_attempt("youtube", False, error_type=CreationError.CAPTCHA)
        stats = engine.get_stats()
        assert stats["total_attempts"] == 2
        assert stats["successes"] == 1
        assert stats["failures"] == 1
        assert stats["success_rate"] == 50.0
        assert stats["error_breakdown"] == {CreationError.CAPTCHA: 1}

    def test_best_initial_strategy_follows_scores(self, engine):
        engine._strategy_scores["workspace"] = 99
        assert engine.get_best_initial_strategy() == "workspace"


class TestShouldChangeProxy:
    @pytest.mark.parametrize("error", [CreationError.IP_FLAGGED, CreationError.QR_BLOCKED])
    def test_ip_related_errors_trigger_rotation(self, engine, error):
        assert engine.should_change_proxy(error) is True

    @pytest.mark.parametrize("error", [
        CreationError.USERNAME_TAKEN,
        CreationError.TIMEOUT,
        CreationError.BROWSER_CRASH,
    ])
    def test_other_errors_do_not(self, engine, error):
        assert engine.should_change_proxy(error) is False
