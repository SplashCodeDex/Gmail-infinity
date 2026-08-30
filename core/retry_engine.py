"""
Retry Engine - Smart retry with strategy rotation for account creation
"""
import logging
import random
import time

logger = logging.getLogger('gmail_creator_retry')


class CreationError:
    PHONE_REQUIRED = "phone_required"
    QR_BLOCKED = "qr_blocked"
    IP_FLAGGED = "ip_flagged"
    USERNAME_TAKEN = "username_taken"
    BROWSER_CRASH = "browser_crash"
    TIMEOUT = "timeout"
    CAPTCHA = "captcha"
    FLOW_ERROR = "flow_error"
    UNKNOWN = "unknown"


class CircuitBreaker:
    """Detects IP/QR flag storms or mass failure cascades to halt burn-out."""

    def __init__(self, failure_threshold: int = 5, ip_block_threshold: int = 3, probe_window_seconds: float = 600.0):
        self.failure_threshold = failure_threshold
        self.ip_block_threshold = ip_block_threshold
        self.probe_window_seconds = probe_window_seconds
        self.consecutive_failures = 0
        self.consecutive_ip_blocks = 0
        self._tripped = False
        self._tripped_at = 0.0
        self._trip_reason = ""

    def record(self, success: bool, error_type: str = None):
        if success:
            self.consecutive_failures = 0
            self.consecutive_ip_blocks = 0
            self._tripped = False
            self._tripped_at = 0.0
            self._trip_reason = ""
            return

        self.consecutive_failures += 1
        if error_type in (CreationError.IP_FLAGGED, CreationError.QR_BLOCKED):
            self.consecutive_ip_blocks += 1
        else:
            self.consecutive_ip_blocks = 0

        now = time.time()
        if self.consecutive_ip_blocks >= self.ip_block_threshold:
            self._tripped = True
            self._tripped_at = now
            self._trip_reason = f"IP/QR flag storm detected ({self.consecutive_ip_blocks} consecutive blocks)"
            logger.error(f"[CIRCUIT_BREAKER] {self._trip_reason}")
        elif self.consecutive_failures >= self.failure_threshold:
            self._tripped = True
            self._tripped_at = now
            self._trip_reason = f"Consecutive failure threshold exceeded ({self.consecutive_failures} failures)"
            logger.error(f"[CIRCUIT_BREAKER] {self._trip_reason}")

    def is_tripped(self) -> bool:
        if self._tripped:
            # Half-open probe window: allow next attempt through to probe health
            if self._tripped_at > 0 and (time.time() - self._tripped_at >= self.probe_window_seconds):
                logger.info("[CIRCUIT_BREAKER] Half-open probe window reached; allowing probe attempt.")
                return False
            return True
        return False

    def get_trip_reason(self) -> str:
        return self._trip_reason

    def reset(self):
        self.consecutive_failures = 0
        self.consecutive_ip_blocks = 0
        self._tripped = False
        self._tripped_at = 0.0
        self._trip_reason = ""


class RetryEngine:
    STRATEGIES = ["standard", "youtube", "workspace", "mobile_ua"]

    MAX_RETRIES = 3
    COOLDOWN_BASE = 15

    STRATEGY_MAP = {
        CreationError.QR_BLOCKED: ["youtube", "workspace", "mobile_ua"],
        CreationError.PHONE_REQUIRED: ["youtube", "mobile_ua", "workspace"],
        CreationError.IP_FLAGGED: ["standard", "youtube"],
        CreationError.USERNAME_TAKEN: None,
        CreationError.BROWSER_CRASH: ["standard"],
        CreationError.TIMEOUT: ["standard"],
        CreationError.FLOW_ERROR: ["standard", "youtube"],
        CreationError.CAPTCHA: ["youtube", "workspace"],
        CreationError.UNKNOWN: ["youtube", "standard"],
    }

    def __init__(self):
        self._attempt_history = []
        self._strategy_scores = {s: 50 for s in self.STRATEGIES}
        self.circuit_breaker = CircuitBreaker()

    def should_retry(self, error_type, attempt_count):
        if self.circuit_breaker.is_tripped():
            return False
        if attempt_count >= self.MAX_RETRIES:
            return False
        if error_type == CreationError.USERNAME_TAKEN:
            return True
        if error_type == CreationError.IP_FLAGGED and attempt_count >= 2:
            return False
        return True

    def get_next_strategy(self, failed_strategy, error_type):
        preferred = self.STRATEGY_MAP.get(error_type, self.STRATEGIES)
        if preferred is None:
            return failed_strategy

        candidates = [s for s in preferred if s != failed_strategy]
        if not candidates:
            candidates = [s for s in self.STRATEGIES if s != failed_strategy]
        if not candidates:
            return random.choice(self.STRATEGIES)

        return max(candidates, key=lambda s: self._strategy_scores.get(s, 50))

    def get_cooldown(self, attempt_count, error_type):
        base = self.COOLDOWN_BASE * (attempt_count + 1)
        if error_type == CreationError.IP_FLAGGED:
            base *= 3
        elif error_type == CreationError.QR_BLOCKED:
            base *= 2
        jitter = random.uniform(0.8, 1.5)
        return int(base * jitter)

    def record_attempt(self, strategy, success, error_type=None):
        self._attempt_history.append({
            "strategy": strategy,
            "success": success,
            "error_type": error_type,
            "timestamp": time.time(),
        })
        self.circuit_breaker.record(success, error_type)
        if success:
            self._strategy_scores[strategy] = min(100, self._strategy_scores[strategy] + 15)
        else:
            self._strategy_scores[strategy] = max(0, self._strategy_scores[strategy] - 10)

    def get_best_initial_strategy(self):
        return max(self.STRATEGIES, key=lambda s: self._strategy_scores.get(s, 50))

    def get_stats(self):
        total = len(self._attempt_history)
        successes = sum(1 for a in self._attempt_history if a["success"])
        failures = total - successes
        error_counts = {}
        for a in self._attempt_history:
            if a["error_type"]:
                error_counts[a["error_type"]] = error_counts.get(a["error_type"], 0) + 1

        return {
            "total_attempts": total,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "strategy_scores": dict(self._strategy_scores),
            "error_breakdown": error_counts,
        }

    def should_change_proxy(self, error_type):
        return error_type in (
            CreationError.IP_FLAGGED,
            CreationError.QR_BLOCKED,
        )


retry_engine = RetryEngine()
