"""
Strategy Engine - Machine learning-based adaptive strategy selection
"""
import time
import random
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict, deque

logger = logging.getLogger('gmail_creator_strategy')


class AdaptiveStrategyEngine:
    """Machine learning-based strategy selector that learns from success patterns."""

    def __init__(self, db=None):
        self.db = db
        self.strategy_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'failures': 0, 'avg_time': 0.0})
        self.session_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'failures': 0, 'avg_time': 0.0})
        self.recent_results = deque(maxlen=50)  # Last 50 results for pattern detection
        self.banned_strategies = set()
        self.cooldown_strategies = {}  # Strategy -> cooldown_until timestamp
        if self.db:
            self.load_historical_learning()

    def load_historical_learning(self):
        """Seed ML model from real historical strategy metrics across runs."""
        try:
            if hasattr(self.db, 'get_recent_strategy_stats'):
                recent_stats = self.db.get_recent_strategy_stats(limit_sessions=20)
                for r in recent_stats:
                    strat = r.get("strategy")
                    if strat:
                        self.strategy_stats[strat]['attempts'] += int(r.get("total_attempts", 0))
                        self.strategy_stats[strat]['successes'] += int(r.get("total_successes", 0))
                        self.strategy_stats[strat]['failures'] += int(r.get("total_failures", 0))
                        self.strategy_stats[strat]['avg_time'] = float(r.get("avg_time", 0.0))
                logger.debug(f"Loaded real strategy metrics across recent sessions: {list(self.strategy_stats.keys())}")
        except Exception as e:
            logger.debug(f"Could not load historical strategy learning: {e}")

    def get_strategy_score(self, strategy: str) -> float:
        """Calculate strategy score based on historical performance."""
        stats = self.strategy_stats[strategy]

        if stats['attempts'] == 0:
            return 0.5  # Neutral score for untried strategies

        # Calculate success rate
        success_rate = stats['successes'] / stats['attempts']

        # Factor in speed (lower time = better)
        time_penalty = min(stats['avg_time'] / 300, 1.0)  # Normalize to 5 minutes

        # Calculate final score
        score = success_rate * 0.7 + (1 - time_penalty) * 0.3

        # Penalize if in cooldown
        if strategy in self.cooldown_strategies:
            if time.time() < self.cooldown_strategies[strategy]:
                score *= 0.3  # Heavily penalize cooled-down strategies
            else:
                del self.cooldown_strategies[strategy]

        # Zero out banned strategies
        if strategy in self.banned_strategies:
            score = 0.0

        return score

    def select_strategy(self, available_strategies: List[str]) -> str:
        """Intelligently select the best strategy based on ML scoring."""
        if not available_strategies:
            return 'standard'

        # Calculate scores for all strategies
        scored = [(s, self.get_strategy_score(s)) for s in available_strategies]

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Epsilon-greedy: 80% best, 20% exploration
        if random.random() < 0.8 and scored[0][1] > 0:
            return scored[0][0]
        else:
            # Explore: weighted random selection
            weights = [max(score, 0.1) for _, score in scored]
            return random.choices([s for s, _ in scored], weights=weights)[0]

    @staticmethod
    def _apply_result(stats, success: bool, duration: float):
        """Increment a single aggregate dict with one execution result."""
        stats['attempts'] += 1
        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        # Exponential moving average for time
        if stats['avg_time'] == 0:
            stats['avg_time'] = duration
        else:
            stats['avg_time'] = 0.7 * stats['avg_time'] + 0.3 * duration

    def record_result(self, strategy: str, success: bool, duration: float):
        """Record strategy result for learning.

        strategy_stats is the cumulative estimate (seeded history + live
        results) used for scoring. session_stats is the session-local
        delta used for persistence — persisting the cumulative estimate
        re-wrote seeded history every session, inflating the aggregates.
        """
        self._apply_result(self.strategy_stats[strategy], success, duration)
        self._apply_result(self.session_stats[strategy], success, duration)

        # Add to recent results for pattern detection
        self.recent_results.append({'strategy': strategy, 'success': success, 'time': time.time()})

        # Detect failure patterns
        self._detect_failure_patterns(strategy)

    def get_session_stats(self):
        """Return the session-local (delta-only) aggregates for persistence."""
        return dict(self.session_stats)

    def _detect_failure_patterns(self, strategy: str):
        """Detect if a strategy is consistently failing and take action."""
        recent_strategy_results = [r for r in self.recent_results if r['strategy'] == strategy]

        if len(recent_strategy_results) >= 5:
            last_5 = recent_strategy_results[-5:]
            failures = sum(1 for r in last_5 if not r['success'])

            # If 4/5 or 5/5 failures, put in cooldown
            if failures >= 4:
                cooldown_until = time.time() + 1800  # 30 minutes cooldown
                self.cooldown_strategies[strategy] = cooldown_until
                logger.warning(f"Strategy '{strategy}' in cooldown until {datetime.fromtimestamp(cooldown_until)}")

            # If 10 consecutive failures, ban temporarily
            if len(recent_strategy_results) >= 10:
                last_10 = recent_strategy_results[-10:]
                if all(not r['success'] for r in last_10):
                    self.banned_strategies.add(strategy)
                    logger.error(f"Strategy '{strategy}' banned due to consecutive failures")

    def get_stats_summary(self) -> Dict:
        """Get summary of all strategies performance."""
        return {
            strategy: {
                'success_rate': (stats['successes'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0.0,
                'attempts': stats['attempts'],
                'successes': stats['successes'],
                'failures': stats['failures'],
                'avg_time': stats['avg_time'],
                'score': self.get_strategy_score(strategy)
            }
            for strategy, stats in self.strategy_stats.items()
        }
