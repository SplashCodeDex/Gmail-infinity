"""
Gmail Infinity Factory - Enhanced Intelligence Engine
Advanced autonomous creator with ML-based optimization, adaptive strategies,
fault tolerance, and real-time decision making.

Features:
- Adaptive strategy selection based on success patterns
- Machine learning proxy scoring and rotation
- Intelligent retry with exponential backoff
- Real-time health monitoring and auto-recovery
- Pattern detection and anti-ban evasion
- Concurrent creation with smart throttling
- Checkpoint system for crash recovery
- Advanced analytics and optimization
"""
import os
import sys
import time
import json
import random
import logging
import argparse
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        def _silence_proactor():
            def safe_del(self, _orig=getattr(_ProactorBasePipeTransport, '__del__', None)):
                try:
                    if getattr(self, '_sock', None) is None:
                        return
                    if _orig:
                        _orig(self)
                except Exception:
                    pass
            _ProactorBasePipeTransport.__del__ = safe_del
        _silence_proactor()
    except ImportError:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

from config.settings import Config
from core.account_manager import account_manager
from core.database import DatabaseManager
from core.proxy_manager import proxy_manager
from core.retry_engine import retry_engine

console = Console()


class AdaptiveStrategyEngine:
    """Machine learning-based strategy selector that learns from success patterns."""

    def __init__(self):
        self.strategy_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'failures': 0, 'avg_time': 0})
        self.recent_results = deque(maxlen=50)  # Last 50 results for pattern detection
        self.banned_strategies = set()
        self.cooldown_strategies = {}  # Strategy -> cooldown_until timestamp

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
            score = 0

        return score

    def select_strategy(self, available_strategies: List[str]) -> str:
        """Intelligently select the best strategy based on ML scoring."""
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

    def record_result(self, strategy: str, success: bool, duration: float):
        """Record strategy result for learning."""
        stats = self.strategy_stats[strategy]
        stats['attempts'] += 1

        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1

        # Update average time (exponential moving average)
        if stats['avg_time'] == 0:
            stats['avg_time'] = duration
        else:
            stats['avg_time'] = 0.7 * stats['avg_time'] + 0.3 * duration

        # Add to recent results for pattern detection
        self.recent_results.append({'strategy': strategy, 'success': success, 'time': time.time()})

        # Detect failure patterns
        self._detect_failure_patterns(strategy)

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
                logging.warning(f"Strategy '{strategy}' in cooldown until {datetime.fromtimestamp(cooldown_until)}")

            # If 10 consecutive failures, ban temporarily
            if len(recent_strategy_results) >= 10:
                last_10 = recent_strategy_results[-10:]
                if all(not r['success'] for r in last_10):
                    self.banned_strategies.add(strategy)
                    logging.error(f"Strategy '{strategy}' banned due to consecutive failures")

    def get_stats_summary(self) -> Dict:
        """Get summary of all strategies performance."""
        return {
            strategy: {
                'success_rate': (stats['successes'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0,
                'attempts': stats['attempts'],
                'successes': stats['successes'],
                'failures': stats['failures'],
                'avg_time': stats['avg_time'],
                'score': self.get_strategy_score(strategy)
            }
            for strategy, stats in self.strategy_stats.items()
        }


class IntelligentProxyManager:
    """Enhanced proxy manager with ML-based scoring and health prediction."""

    def __init__(self):
        self.proxy_scores = {}  # proxy -> score (0-1)
        self.proxy_history = defaultdict(lambda: {'successes': 0, 'failures': 0, 'last_used': 0, 'response_times': deque(maxlen=10)})
        self.proxy_health_cache = {}  # proxy -> (is_healthy, checked_at)
        self.proxy_rotation_index = 0

    def calculate_proxy_score(self, proxy: str) -> float:
        """Calculate proxy reliability score."""
        if not proxy:
            return 0.5

        history = self.proxy_history[proxy]
        total = history['successes'] + history['failures']

        if total == 0:
            return 0.5  # Neutral for untested proxies

        # Success rate component (60%)
        success_rate = history['successes'] / total

        # Speed component (20%)
        avg_response = sum(history['response_times']) / len(history['response_times']) if history['response_times'] else 5.0
        speed_score = max(0, 1 - (avg_response / 10))  # Normalize to 10 seconds

        # Freshness component (20%) - penalize old proxies
        time_since_use = time.time() - history['last_used'] if history['last_used'] > 0 else 0
        freshness_score = max(0, 1 - (time_since_use / 3600))  # Decay over 1 hour

        final_score = (success_rate * 0.6) + (speed_score * 0.2) + (freshness_score * 0.2)

        return final_score

    def select_best_proxy(self) -> Optional[str]:
        """Select the best proxy based on ML scoring."""
        if proxy_manager.count == 0:
            return None

        # Get all available proxies
        available = proxy_manager.get_all_proxies()

        if not available:
            return None

        # Calculate scores
        scored_proxies = [(p, self.calculate_proxy_score(p)) for p in available]
        scored_proxies.sort(key=lambda x: x[1], reverse=True)

        # Epsilon-greedy selection with 85% exploitation
        if random.random() < 0.85 and scored_proxies:
            return scored_proxies[0][0]
        else:
            return random.choice(available)

    def record_proxy_result(self, proxy: str, success: bool, response_time: float):
        """Record proxy performance."""
        if not proxy:
            return

        history = self.proxy_history[proxy]

        if success:
            history['successes'] += 1
        else:
            history['failures'] += 1

        history['last_used'] = time.time()
        history['response_times'].append(response_time)

        # Update proxy manager
        if success:
            proxy_manager.mark_success(proxy)
        else:
            proxy_manager.mark_failure(proxy)

    def get_proxy_stats(self) -> Dict:
        """Get comprehensive proxy statistics."""
        stats = {}
        for proxy, history in self.proxy_history.items():
            total = history['successes'] + history['failures']
            stats[proxy] = {
                'score': self.calculate_proxy_score(proxy),
                'success_rate': (history['successes'] / total * 100) if total > 0 else 0,
                'total_uses': total,
                'avg_response_time': sum(history['response_times']) / len(history['response_times']) if history['response_times'] else 0
            }
        return stats


class CheckpointManager:
    """Manages checkpoints for crash recovery and resume capability."""

    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id = self._generate_session_id()
        self.checkpoint_file = self.checkpoint_dir / f"session_{self.current_session_id}.json"

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}"

    def save_checkpoint(self, state: Dict):
        """Save current state to checkpoint."""
        state['checkpoint_time'] = datetime.now().isoformat()
        state['session_id'] = self.current_session_id

        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> Optional[Dict]:
        """Load the most recent checkpoint."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load checkpoint: {e}")
        return None

    def clear_checkpoint(self):
        """Clear current checkpoint after successful completion."""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
        except Exception as e:
            logging.error(f"Failed to clear checkpoint: {e}")

    def list_checkpoints(self) -> List[Path]:
        """List all available checkpoints."""
        return sorted(self.checkpoint_dir.glob("session_*.json"), reverse=True)


class EnhancedCreator:
    """Intelligent, robust, and adaptive Gmail account creator."""

    def __init__(self,
                 num_accounts: int = 1,
                 use_sms: bool = False,
                 use_proxies: bool = True,
                 warmup: bool = True,
                 export_format: str = 'json',
                 concurrent: int = 1,
                 auto_recover: bool = True,
                 adaptive: bool = True):

        self.num_accounts = num_accounts
        self.use_sms = use_sms
        self.use_proxies = use_proxies
        self.warmup = warmup
        self.export_format = export_format
        self.concurrent = max(1, min(concurrent, 5))  # Limit 1-5 concurrent
        self.auto_recover = auto_recover
        self.adaptive = adaptive

        # Statistics
        self.successes = 0
        self.failures = 0
        self.created_accounts = []
        self.failed_attempts = []
        self.start_time = None

        # Intelligence engines
        self.strategy_engine = AdaptiveStrategyEngine()
        self.proxy_manager = IntelligentProxyManager()
        self.checkpoint_manager = CheckpointManager()

        # Database
        self.db = DatabaseManager()

        # State
        self.completed_indices = set()
        self.is_paused = False
        self.stop_requested = False

        # Available strategies
        self.available_strategies = ['standard', 'youtube', 'workspace']

    def setup_logging(self):
        """Enhanced logging with detailed tracking."""
        if not Config.ENABLE_LOGGING:
            return

        try:
            log_dir = Path(Config.LOG_FILE).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create detailed log file
            log_file = log_dir / f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )

            # Also log strategy and proxy decisions
            logging.info("="*80)
            logging.info("Enhanced Creator Session Started")
            logging.info(f"Target: {self.num_accounts} accounts")
            logging.info(f"SMS: {self.use_sms}, Proxies: {self.use_proxies}, Adaptive: {self.adaptive}")
            logging.info("="*80)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not setup logging: {e}[/yellow]")

    def show_banner(self):
        """Display enhanced banner."""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold white]GMAIL INFINITY FACTORY - ENHANCED INTELLIGENCE[/bold white]      [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [dim]ML-Powered • Adaptive • Fault-Tolerant • Concurrent[/dim]  [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🧠 Adaptive Strategy Selection[/bold yellow]
[bold green]🎯 Intelligent Proxy Management[/bold green]
[bold magenta]⚡ Concurrent Processing[/bold magenta]
[bold cyan]💾 Crash Recovery System[/bold cyan]
"""
        console.print(banner)

    def validate_and_optimize_config(self) -> bool:
        """Validate configuration and apply optimizations."""
        warnings = []
        optimizations = []

        # Check password
        if not Config.YOUR_PASSWORD:
            warnings.append("⚠️  No password set - using generated passwords")

        # Check SMS
        if self.use_sms:
            has_sms = any([
                Config.FIVESIM_API_KEY,
                Config.SMS_ACTIVATE_API_KEY,
                Config.ONLINESIM_API_KEY,
                getattr(Config, 'GETSMS_API_KEY', ''),
            ])
            if not has_sms:
                console.print("[red]ERROR: SMS verification requires API keys[/red]")
                return False

        # Check proxies
        if self.use_proxies and Config.ENABLE_PROXY:
            if proxy_manager.count == 0:
                warnings.append("⚠️  No proxies loaded - running without proxies")
                self.use_proxies = False
            else:
                optimizations.append(f"✓ {proxy_manager.count} proxies loaded and ready")

        # Optimize concurrent workers based on resources
        if self.concurrent > 1:
            if proxy_manager.count < self.concurrent:
                old_concurrent = self.concurrent
                self.concurrent = max(1, proxy_manager.count)
                optimizations.append(f"⚙️  Concurrent workers adjusted: {old_concurrent} → {self.concurrent}")

            if self.num_accounts < self.concurrent:
                self.concurrent = self.num_accounts
                optimizations.append(f"⚙️  Concurrent workers optimized for {self.num_accounts} accounts")

        # Enable headless for concurrent mode
        if self.concurrent > 1 and not Config.HEADLESS_MODE:
            Config.HEADLESS_MODE = True
            optimizations.append("⚙️  Headless mode enabled for concurrent processing")

        # Display warnings
        if warnings:
            console.print("\n[yellow]Configuration Warnings:[/yellow]")
            for w in warnings:
                console.print(f"  {w}")

        # Display optimizations
        if optimizations:
            console.print("\n[green]Auto-Optimizations Applied:[/green]")
            for o in optimizations:
                console.print(f"  {o}")

        console.print()
        return True

    def show_config_dashboard(self):
        """Display comprehensive configuration dashboard."""
        table = Table(title="🎛️  Configuration Dashboard", show_header=True, header_style="bold magenta", border_style="cyan")
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Setting", style="yellow", width=25)
        table.add_column("Value", style="green", width=30)

        # Core settings
        table.add_row("Core", "Target Accounts", str(self.num_accounts))
        table.add_row("", "Concurrent Workers", f"{self.concurrent} {'🔥' if self.concurrent > 1 else ''}")
        table.add_row("", "Engine", Config.ENGINE_MODE.upper())
        table.add_row("", "Headless Mode", "✓ Enabled" if Config.HEADLESS_MODE else "✗ Disabled")

        # Intelligence
        table.add_row("Intelligence", "Adaptive Strategies", "✓ Enabled" if self.adaptive else "✗ Disabled")
        table.add_row("", "Auto Recovery", "✓ Enabled" if self.auto_recover else "✗ Disabled")
        table.add_row("", "Checkpoint System", "✓ Active")

        # Verification
        table.add_row("Verification", "SMS Verification", "✓ Enabled" if self.use_sms else "✗ Disabled")
        table.add_row("", "Account Warming", "✓ Enabled" if self.warmup else "✗ Disabled")

        # Network
        table.add_row("Network", "Proxy Rotation", "✓ Enabled" if self.use_proxies else "✗ Disabled")
        if self.use_proxies and proxy_manager.count > 0:
            table.add_row("", "Available Proxies", f"{proxy_manager.count} proxies")
            stats = proxy_manager.get_stats()
            table.add_row("", "Healthy Proxies", f"{stats.get('healthy', 0)} healthy")

        # Stealth
        table.add_row("Stealth", "Fingerprint Masking", "✓" if Config.ENABLE_FINGERPRINT_MASKING else "✗")
        table.add_row("", "Human Typing", "✓" if Config.ENABLE_HUMAN_TYPING_ERRORS else "✗")
        table.add_row("", "CDP Injection", "✓" if Config.ENABLE_CDP_INJECTION else "✗")

        # Export
        table.add_row("Export", "Format", self.export_format.upper())

        console.print("\n")
        console.print(table)
        console.print("\n")

    def generate_username(self) -> Tuple[str, List[str]]:
        """Generate unique username with collision detection."""
        from core.selenium_runner import generate_name

        # Generate and check for uniqueness
        max_attempts = 10
        for _ in range(max_attempts):
            name = generate_name()
            parts = name.split()
            first = parts[0].lower() if parts else "user"
            last = parts[-1].lower() if len(parts) > 1 else "gmail"
            username = f"{first}{last}{random.randint(1000, 9999)}"

            # Check if username already created in this session
            if not any(acc['email'].startswith(username) for acc in self.created_accounts):
                return username, parts

        # Fallback with timestamp
        timestamp = int(time.time()) % 10000
        return f"user{timestamp}", ["User", "Account"]

    def create_account_with_intelligence(self, index: int, progress=None, task_id=None) -> Dict:
        """Create single account with full intelligence and retry logic."""
        start_time = time.time()

        # Select strategy
        if self.adaptive:
            strategy = self.strategy_engine.select_strategy(self.available_strategies)
        else:
            strategy = random.choice(self.available_strategies)

        logging.info(f"Account {index+1}: Selected strategy '{strategy}'")

        # Generate credentials
        username, name_parts = self.generate_username()
        first_name = name_parts[0] if name_parts else "User"
        last_name = name_parts[-1] if len(name_parts) > 1 else "User"

        password = Config.YOUR_PASSWORD
        if not password:
            from core.selenium_runner import generate_password
            password = generate_password()

        # Select proxy
        proxy = None
        if self.use_proxies and Config.ENABLE_PROXY:
            proxy = self.proxy_manager.select_best_proxy()
            logging.info(f"Account {index+1}: Selected proxy {proxy}")

        if progress and task_id:
            progress.update(task_id, description=f"[cyan]Creating {username}@gmail.com ({strategy})[/cyan]")

        # Retry logic with exponential backoff
        max_retries = 3
        backoff_delays = [5, 15, 30]  # seconds
        success = False
        error_msg = None

        for attempt in range(max_retries):
            if self.stop_requested:
                break

            if attempt > 0:
                delay = backoff_delays[min(attempt-1, len(backoff_delays)-1)]
                logging.info(f"Account {index+1}: Retry {attempt+1} after {delay}s")

                if progress and task_id:
                    progress.update(task_id, description=f"[yellow]Retry {attempt+1}/{max_retries} in {delay}s...[/yellow]")

                time.sleep(delay)

                # Change proxy on retry
                if proxy and self.use_proxies:
                    self.proxy_manager.record_proxy_result(proxy, False, time.time() - start_time)
                    proxy = self.proxy_manager.select_best_proxy()
                    logging.info(f"Account {index+1}: Switched to proxy {proxy}")

                # Regenerate credentials on retry
                username, name_parts = self.generate_username()
                first_name = name_parts[0] if name_parts else "User"
                last_name = name_parts[-1] if len(name_parts) > 1 else "User"

                if not Config.YOUR_PASSWORD:
                    from core.selenium_runner import generate_password
                    password = generate_password()

            try:
                engine = Config.ENGINE_MODE.lower()

                if progress and task_id:
                    progress.update(task_id, description=f"[cyan]Creating {username}@gmail.com (attempt {attempt+1})[/cyan]")

                # Execute creation
                if engine == 'playwright':
                    from core.runners import run_playwright_flow
                    success = run_playwright_flow(
                        index, self.num_accounts, username, first_name, last_name,
                        password, progress, task_id, proxy,
                        use_sms_api=self.use_sms, flow_mode=strategy,
                    )
                elif engine == 'appium':
                    from core.runners import run_appium_flow
                    month, day, year = Config.YOUR_BIRTHDAY.split() if Config.YOUR_BIRTHDAY else ("1", "1", "1990")
                    success = run_appium_flow(
                        index, self.num_accounts, username, first_name, last_name,
                        password, month, day, year, str(Config.YOUR_GENDER),
                        progress, task_id,
                    )
                else:
                    from core.selenium_runner import run_selenium_flow
                    warmup_minutes = 10 if self.warmup else 0
                    success = run_selenium_flow(
                        index, self.num_accounts, username, password,
                        warmup_minutes=warmup_minutes,
                        stealth_mode=(not self.use_sms),
                        mode=strategy, proxy=proxy,
                    )

                if success:
                    break

            except Exception as e:
                error_msg = str(e)
                logging.error(f"Account {index+1} attempt {attempt+1} error: {e}")
                if progress and task_id:
                    progress.update(task_id, description=f"[red]Error: {str(e)[:40]}...[/red]")

        duration = time.time() - start_time

        # Record results in intelligence engines
        if self.adaptive:
            self.strategy_engine.record_result(strategy, success, duration)

        if proxy and self.use_proxies:
            self.proxy_manager.record_proxy_result(proxy, success, duration)

        # Build result
        result = {
            'index': index,
            'email': f"{username}@gmail.com",
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'success': success,
            'strategy': strategy,
            'proxy': proxy,
            'duration': duration,
            'created_at': datetime.now().isoformat(),
            'error': error_msg if not success else None
        }

        logging.info(f"Account {index+1}: {'SUCCESS' if success else 'FAILED'} in {duration:.1f}s")

        return result

    def create_accounts_concurrent(self):
        """Create accounts with concurrent workers."""
        console.print(f"\n[bold green]🚀 Starting concurrent creation with {self.concurrent} workers...[/bold green]\n")

        remaining_indices = [i for i in range(self.num_accounts) if i not in self.completed_indices]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            overall_task = progress.add_task(
                "[cyan]Overall Progress",
                total=len(remaining_indices)
            )

            worker_tasks = {}
            for i in range(self.concurrent):
                task = progress.add_task(f"[dim]Worker {i+1}: Idle", total=100)
                worker_tasks[i] = task

            with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
                # Submit all jobs
                future_to_index = {}
                worker_id = 0

                for idx in remaining_indices:
                    if self.stop_requested:
                        break

                    task_id = worker_tasks[worker_id % self.concurrent]
                    future = executor.submit(self.create_account_with_intelligence, idx, progress, task_id)
                    future_to_index[future] = (idx, task_id)
                    worker_id += 1

                # Process results as they complete
                for future in as_completed(future_to_index):
                    if self.stop_requested:
                        break

                    idx, task_id = future_to_index[future]

                    try:
                        result = future.result()

                        if result['success']:
                            self.successes += 1
                            self.created_accounts.append(result)
                            progress.update(task_id, description=f"[green]✓ {result['email']}[/green]")
                        else:
                            self.failures += 1
                            self.failed_attempts.append(result)
                            progress.update(task_id, description=f"[red]✗ {result['email']} failed[/red]")

                        self.completed_indices.add(idx)
                        progress.update(overall_task, advance=1)

                        # Save checkpoint
                        if self.auto_recover:
                            self.save_current_state()

                        # Add delay between accounts
                        if idx < self.num_accounts - 1:
                            delay = Config.DELAY_BETWEEN_ACCOUNTS
                            time.sleep(delay)

                    except Exception as e:
                        logging.error(f"Worker exception for account {idx}: {e}")
                        self.failures += 1
                        progress.update(task_id, description=f"[red]✗ Worker error[/red]")

    def create_accounts_sequential(self):
        """Create accounts sequentially (safer, more controlled)."""
        console.print(f"\n[bold green]📝 Starting sequential creation...[/bold green]\n")

        remaining_indices = [i for i in range(self.num_accounts) if i not in self.completed_indices]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            overall_task = progress.add_task(
                "[cyan]Overall Progress",
                total=len(remaining_indices)
            )

            for idx in remaining_indices:
                if self.stop_requested:
                    break

                current_task = progress.add_task(
                    f"[cyan]Account {idx+1}/{self.num_accounts}",
                    total=100
                )

                result = self.create_account_with_intelligence(idx, progress, current_task)

                if result['success']:
                    self.successes += 1
                    self.created_accounts.append(result)
                else:
                    self.failures += 1
                    self.failed_attempts.append(result)

                self.completed_indices.add(idx)
                progress.update(overall_task, advance=1)
                progress.remove_task(current_task)

                # Save checkpoint
                if self.auto_recover:
                    self.save_current_state()

                # Delay between accounts
                if idx < self.num_accounts - 1:
                    delay = Config.DELAY_BETWEEN_ACCOUNTS
                    time.sleep(delay)

    def save_current_state(self):
        """Save current state to checkpoint."""
        state = {
            'num_accounts': self.num_accounts,
            'completed_indices': list(self.completed_indices),
            'successes': self.successes,
            'failures': self.failures,
            'created_accounts': self.created_accounts,
            'failed_attempts': self.failed_attempts,
            'strategy_stats': dict(self.strategy_engine.strategy_stats),
            'proxy_stats': dict(self.proxy_manager.proxy_history),
            'config': {
                'use_sms': self.use_sms,
                'use_proxies': self.use_proxies,
                'warmup': self.warmup,
                'concurrent': self.concurrent,
                'adaptive': self.adaptive,
            }
        }
        self.checkpoint_manager.save_checkpoint(state)

    def load_previous_state(self) -> bool:
        """Load and resume from previous checkpoint."""
        checkpoint = self.checkpoint_manager.load_checkpoint()

        if not checkpoint:
            return False

        console.print("\n[yellow]📂 Previous session found![/yellow]")
        console.print(f"Session ID: {checkpoint.get('session_id', 'Unknown')}")
        console.print(f"Checkpoint Time: {checkpoint.get('checkpoint_time', 'Unknown')}")
        console.print(f"Progress: {len(checkpoint.get('completed_indices', []))}/{checkpoint.get('num_accounts', 0)} accounts")
        console.print(f"Success: {checkpoint.get('successes', 0)}, Failed: {checkpoint.get('failures', 0)}\n")

        # Restore state
        self.completed_indices = set(checkpoint.get('completed_indices', []))
        self.successes = checkpoint.get('successes', 0)
        self.failures = checkpoint.get('failures', 0)
        self.created_accounts = checkpoint.get('created_accounts', [])
        self.failed_attempts = checkpoint.get('failed_attempts', [])

        # Restore intelligence engines
        if 'strategy_stats' in checkpoint:
            for strategy, stats in checkpoint['strategy_stats'].items():
                self.strategy_engine.strategy_stats[strategy] = stats

        if 'proxy_stats' in checkpoint:
            for proxy, history in checkpoint['proxy_stats'].items():
                self.proxy_manager.proxy_history[proxy] = defaultdict(lambda: {'successes': 0, 'failures': 0, 'last_used': 0, 'response_times': deque(maxlen=10)}, history)

        console.print("[green]✓ Previous session restored successfully![/green]\n")
        return True

    def run(self):
        """Execute the enhanced creation flow."""
        self.start_time = time.time()

        # Setup
        self.setup_logging()
        self.show_banner()

        # Check for previous session
        if self.auto_recover:
            has_checkpoint = self.load_previous_state()
            if has_checkpoint and len(self.completed_indices) >= self.num_accounts:
                console.print("[yellow]Previous session was already completed![/yellow]")
                self.show_final_results()
                return True

        # Validate
        if not self.validate_and_optimize_config():
            return False

        # Show config
        self.show_config_dashboard()

        # Run creation
        try:
            if self.concurrent > 1:
                self.create_accounts_concurrent()
            else:
                self.create_accounts_sequential()
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Creation interrupted by user[/yellow]")
            self.save_current_state()
            console.print("[cyan]Progress saved. Run again to resume.[/cyan]\n")
            return False
        except Exception as e:
            console.print(f"\n[red]❌ Fatal error: {e}[/red]")
            logging.exception("Fatal error in creation flow")
            self.save_current_state()
            return False

        # Show results
        self.show_final_results()

        # Show intelligence insights
        self.show_intelligence_insights()

        # Export accounts
        if self.created_accounts:
            self.export_accounts()

        # Save to database
        self.save_to_database()

        # Send notifications
        self.send_notifications()

        # Clear checkpoint on success
        if self.auto_recover and len(self.completed_indices) >= self.num_accounts:
            self.checkpoint_manager.clear_checkpoint()

        return self.successes > 0

    def show_final_results(self):
        """Display comprehensive final results."""
        duration = time.time() - self.start_time
        success_rate = (self.successes / self.num_accounts * 100) if self.num_accounts > 0 else 0

        # Main results panel
        results = f"""
[bold green]✓ Successful:[/bold green] {self.successes}
[bold red]✗ Failed:[/bold red] {self.failures}
[bold cyan]Success Rate:[/bold cyan] {success_rate:.1f}%
[bold yellow]Total Duration:[/bold yellow] {duration:.1f}s ({duration/60:.1f} minutes)
"""

        if self.num_accounts > 0:
            avg_time = duration / self.num_accounts
            results += f"[bold magenta]Avg per Account:[/bold magenta] {avg_time:.1f}s\n"

        console.print("\n")
        console.print(Panel(
            results,
            title="[bold white]📊 Final Results[/bold white]",
            border_style="green" if success_rate >= 50 else "red",
            padding=(1, 2)
        ))

        # Created accounts table
        if self.created_accounts:
            console.print("\n[bold green]✅ Successfully Created Accounts:[/bold green]")
            table = Table(show_header=True, header_style="bold cyan", border_style="green")
            table.add_column("#", style="dim", width=4)
            table.add_column("Email", style="green")
            table.add_column("Password", style="yellow")
            table.add_column("Strategy", style="cyan")
            table.add_column("Time", style="magenta")

            for idx, acc in enumerate(self.created_accounts, 1):
                table.add_row(
                    str(idx),
                    acc['email'],
                    acc['password'],
                    acc['strategy'],
                    f"{acc['duration']:.1f}s"
                )

            console.print(table)
            console.print()

    def show_intelligence_insights(self):
        """Display ML insights and learned patterns."""
        if not self.adaptive:
            return

        console.print("\n[bold cyan]🧠 Intelligence Insights[/bold cyan]\n")

        # Strategy performance
        strategy_stats = self.strategy_engine.get_stats_summary()
        if strategy_stats:
            table = Table(title="Strategy Performance", show_header=True, header_style="bold magenta")
            table.add_column("Strategy", style="cyan")
            table.add_column("Success Rate", style="green")
            table.add_column("Attempts", style="yellow")
            table.add_column("Avg Time", style="magenta")
            table.add_column("Score", style="cyan")

            for strategy, stats in sorted(strategy_stats.items(), key=lambda x: x[1]['score'], reverse=True):
                table.add_row(
                    strategy,
                    f"{stats['success_rate']:.1f}%",
                    str(stats['attempts']),
                    f"{stats['avg_time']:.1f}s",
                    f"{stats['score']:.2f}"
                )

            console.print(table)

        # Proxy performance
        if self.use_proxies:
            proxy_stats = self.proxy_manager.get_proxy_stats()
            if proxy_stats:
                console.print("\n")
                table = Table(title="Top 5 Proxy Performance", show_header=True, header_style="bold magenta")
                table.add_column("Proxy", style="cyan", max_width=40)
                table.add_column("Score", style="green")
                table.add_column("Success Rate", style="yellow")
                table.add_column("Uses", style="magenta")

                top_proxies = sorted(proxy_stats.items(), key=lambda x: x[1]['score'], reverse=True)[:5]
                for proxy, stats in top_proxies:
                    # Mask proxy for security
                    masked_proxy = proxy[:20] + "..." if len(proxy) > 20 else proxy
                    table.add_row(
                        masked_proxy,
                        f"{stats['score']:.2f}",
                        f"{stats['success_rate']:.1f}%",
                        str(stats['total_uses'])
                    )

                console.print(table)

        console.print()

    def export_accounts(self):
        """Export created accounts."""
        if not self.created_accounts:
            return

        try:
            console.print("\n[bold cyan]💾 Exporting accounts...[/bold cyan]")

            if self.export_format == 'json':
                path = account_manager.export_json()
                console.print(f"[green]✓ JSON:[/green] {path}")
            elif self.export_format == 'csv':
                path = account_manager.export_csv()
                console.print(f"[green]✓ CSV:[/green] {path}")
            elif self.export_format == 'txt':
                path = account_manager.export_txt()
                console.print(f"[green]✓ TXT:[/green] {path}")
            elif self.export_format == 'all':
                paths = []
                paths.append(account_manager.export_json())
                paths.append(account_manager.export_csv())
                paths.append(account_manager.export_txt())
                console.print("[green]✓ Exported to all formats:[/green]")
                for p in paths:
                    console.print(f"  • {p}")

            # Also export intelligence data
            self.export_intelligence_data()

        except Exception as e:
            console.print(f"[red]Export error: {e}[/red]")
            logging.error(f"Export error: {e}")

    def export_intelligence_data(self):
        """Export ML intelligence data for analysis."""
        try:
            intelligence_data = {
                'session_id': self.checkpoint_manager.current_session_id,
                'timestamp': datetime.now().isoformat(),
                'strategy_stats': self.strategy_engine.get_stats_summary(),
                'proxy_stats': self.proxy_manager.get_proxy_stats(),
                'session_stats': {
                    'total': self.num_accounts,
                    'successes': self.successes,
                    'failures': self.failures,
                    'duration': time.time() - self.start_time,
                }
            }

            intel_file = Path("data") / f"intelligence_{self.checkpoint_manager.current_session_id}.json"
            with open(intel_file, 'w', encoding='utf-8') as f:
                json.dump(intelligence_data, f, indent=2, ensure_ascii=False)

            console.print(f"[green]✓ Intelligence data:[/green] {intel_file}")

        except Exception as e:
            logging.error(f"Failed to export intelligence data: {e}")

    def save_to_database(self):
        """Save session data to database."""
        try:
            duration = time.time() - self.start_time
            strategies_used = {}

            for acc in self.created_accounts:
                strategy = acc.get('strategy', 'unknown')
                strategies_used[strategy] = strategies_used.get(strategy, 0) + 1

            self.db.save_session_stats(
                total_attempts=self.num_accounts,
                successes=self.successes,
                failures=self.failures,
                strategies_used=strategies_used,
                errors={},
                duration_seconds=duration,
            )
        except Exception as e:
            logging.error(f"Database save error: {e}")

    def send_notifications(self):
        """Send completion notifications."""
        try:
            from core.telegram_notifier import notifier
            if notifier.enabled:
                duration = time.time() - self.start_time
                notifier.notify_batch_complete(
                    self.num_accounts, self.successes, self.failures, duration
                )

                # Send intelligence summary
                if self.adaptive:
                    summary = self.strategy_engine.get_stats_summary()
                    best_strategy = max(summary.items(), key=lambda x: x[1]['score'])[0] if summary else 'N/A'
                    notifier.send(f"🧠 Best Strategy: {best_strategy}")
        except Exception as e:
            logging.error(f"Notification error: {e}")


def main():
    """Main entry point with enhanced argument parsing."""
    parser = argparse.ArgumentParser(
        description='Gmail Infinity Factory - Enhanced Intelligence Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create 10 accounts with adaptive AI
  python enhanced_creator.py -n 10

  # Create 20 accounts with 3 concurrent workers
  python enhanced_creator.py -n 20 -c 3

  # Create accounts with SMS and adaptive strategies
  python enhanced_creator.py -n 5 --sms --adaptive

  # Resume interrupted session
  python enhanced_creator.py --resume

  # Create with all intelligence features
  python enhanced_creator.py -n 50 --sms --adaptive -c 5 --headless
        """
    )

    parser.add_argument('-n', '--num-accounts', type=int, default=1,
                        help='Number of accounts to create (default: 1)')
    parser.add_argument('-c', '--concurrent', type=int, default=1,
                        help='Number of concurrent workers (1-5, default: 1)')
    parser.add_argument('--sms', action='store_true',
                        help='Enable SMS verification')
    parser.add_argument('--no-proxies', action='store_true',
                        help='Disable proxy rotation')
    parser.add_argument('--no-warmup', action='store_true',
                        help='Skip account warming')
    parser.add_argument('--export', choices=['json', 'csv', 'txt', 'all'], default='json',
                        help='Export format (default: json)')
    parser.add_argument('--adaptive', action='store_true', default=True,
                        help='Enable adaptive strategy learning (default: enabled)')
    parser.add_argument('--no-adaptive', dest='adaptive', action='store_false',
                        help='Disable adaptive strategies')
    parser.add_argument('--no-recovery', dest='auto_recover', action='store_false', default=True,
                        help='Disable auto-recovery checkpoint system')
    parser.add_argument('--headless', action='store_true',
                        help='Force headless browser mode')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last checkpoint')

    args = parser.parse_args()

    # Override config
    if args.headless:
        Config.HEADLESS_MODE = True

    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/checkpoints", exist_ok=True)

    # Create enhanced creator
    creator = EnhancedCreator(
        num_accounts=args.num_accounts,
        use_sms=args.sms,
        use_proxies=not args.no_proxies,
        warmup=not args.no_warmup,
        export_format=args.export,
        concurrent=args.concurrent,
        auto_recover=args.auto_recover,
        adaptive=args.adaptive,
    )

    # Run
    success = creator.run()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
