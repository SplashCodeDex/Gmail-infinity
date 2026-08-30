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
        assert flagged > base

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


class TestCircuitBreaker:
    def test_initial_state_not_tripped(self, engine):
        assert engine.circuit_breaker.is_tripped() is False
        assert engine.circuit_breaker.get_trip_reason() == ""

    def test_trips_on_consecutive_ip_blocks(self, engine):
        for _ in range(3):
            engine.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)

        assert engine.circuit_breaker.is_tripped() is True
        assert "IP/QR flag storm" in engine.circuit_breaker.get_trip_reason()
        assert engine.should_retry(CreationError.TIMEOUT, 0) is False

    def test_trips_on_consecutive_general_failures(self, engine):
        for _ in range(5):
            engine.record_attempt("standard", False, error_type=CreationError.TIMEOUT)

        assert engine.circuit_breaker.is_tripped() is True
        assert "failure threshold exceeded" in engine.circuit_breaker.get_trip_reason()

    def test_success_resets_circuit_breaker(self, engine):
        for _ in range(2):
            engine.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)

        engine.record_attempt("standard", True)
        assert engine.circuit_breaker.is_tripped() is False
        assert engine.circuit_breaker.consecutive_failures == 0

    def test_scoped_engines_isolation(self):
        engine_a = RetryEngine()
        engine_b = RetryEngine()

        for _ in range(3):
            engine_a.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)

        assert engine_a.circuit_breaker.is_tripped() is True
        assert engine_b.circuit_breaker.is_tripped() is False
        assert engine_b.should_retry(CreationError.TIMEOUT, 0) is True

    def test_half_open_probe_window_recovery(self, engine):
        for _ in range(3):
            engine.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)

        assert engine.circuit_breaker.is_tripped() is True

        # Simulate 10 minutes (601 seconds) passing
        engine.circuit_breaker._tripped_at -= 601.0
        assert engine.circuit_breaker.is_tripped() is False

        # If the probe succeeds, breaker resets to fully closed
        engine.record_attempt("standard", True)
        assert engine.circuit_breaker.is_tripped() is False
        assert engine.circuit_breaker.consecutive_ip_blocks == 0

    def test_probe_failure_retrips(self, engine):
        for _ in range(3):
            engine.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)

        # Expire probe window
        engine.circuit_breaker._tripped_at -= 601.0
        assert engine.circuit_breaker.is_tripped() is False

        # Probe fails -> immediately re-trips
        engine.record_attempt("standard", False, error_type=CreationError.IP_FLAGGED)
        assert engine.circuit_breaker.is_tripped() is True


