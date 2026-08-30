"""
Gmail Infinity Factory - Streamlined Auto Mode
Fully automated account creation with zero interaction required.
All best practices and stealth features enabled by default.
"""
import os
import sys
import time
import random
import logging
import argparse
from datetime import datetime

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
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from config.settings import Config
from core.account_manager import account_manager
from core.database import DatabaseManager
from core.proxy_manager import proxy_manager
from core.retry_engine import retry_engine

console = Console()


class StreamlinedCreator:
    """Automated Gmail account creator with optimal settings."""

    def __init__(self, num_accounts=1, use_sms=False, use_proxies=True,
                 warmup=True, export_format='json', flow_mode='auto'):
        self.num_accounts = num_accounts
        self.use_sms = use_sms
        self.use_proxies = use_proxies
        self.warmup = warmup
        self.export_format = export_format
        self.flow_mode = flow_mode

        self.successes = 0
        self.failures = 0
        self.created_accounts = []
        self.start_time = None

        # Initialize database
        self.db = DatabaseManager()

    def setup_logging(self):
        """Setup file logging."""
        if not Config.ENABLE_LOGGING:
            return

        try:
            log_dir = os.path.dirname(Config.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            logging.basicConfig(
                filename=Config.LOG_FILE,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not setup logging: {e}[/yellow]")

    def show_banner(self):
        """Display startup banner."""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold white]GMAIL INFINITY FACTORY - STREAMLINED MODE[/bold white]        [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [dim]Fully Automated • Zero Interaction Required[/dim]        [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]
"""
        console.print(banner)

    def validate_config(self):
        """Validate configuration and show warnings."""
        warnings = []

        # Check password
        if not Config.YOUR_PASSWORD:
            warnings.append("⚠️  No password set in .env - accounts will use generated passwords")

        # Check SMS if required
        if self.use_sms:
            has_sms = any([
                Config.FIVESIM_API_KEY,
                Config.SMS_ACTIVATE_API_KEY,
                Config.ONLINESIM_API_KEY,
                getattr(Config, 'GETSMS_API_KEY', ''),
            ])
            if not has_sms:
                warnings.append("⚠️  SMS mode enabled but no API keys configured!")
                console.print("[red]ERROR: SMS verification requires API keys in .env[/red]")
                return False

        # Check proxies if required
        if self.use_proxies and Config.ENABLE_PROXY:
            if proxy_manager.count == 0:
                warnings.append("⚠️  Proxy mode enabled but no proxies loaded from config/proxies.txt")

        # Display warnings
        if warnings:
            console.print("\n[yellow]Configuration Warnings:[/yellow]")
            for w in warnings:
                console.print(f"  {w}")
            console.print()

        return True

    def show_config_summary(self):
        """Display current configuration."""
        table = Table(title="Configuration Summary", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", width=25)
        table.add_column("Value", style="green")

        table.add_row("Accounts to Create", str(self.num_accounts))
        table.add_row("SMS Verification", "✓ Enabled" if self.use_sms else "✗ Disabled")
        table.add_row("Proxy Rotation", "✓ Enabled" if (self.use_proxies and Config.ENABLE_PROXY) else "✗ Disabled")
        table.add_row("Account Warming", "✓ Enabled" if self.warmup else "✗ Disabled")
        table.add_row("Flow Mode", self.flow_mode.upper())
        table.add_row("Engine", Config.ENGINE_MODE.upper())
        table.add_row("Headless Mode", "✓ Yes" if Config.HEADLESS_MODE else "✗ No")
        table.add_row("Fingerprint Masking", "✓ Enabled" if Config.ENABLE_FINGERPRINT_MASKING else "✗ Disabled")
        table.add_row("Human Typing", "✓ Enabled" if Config.ENABLE_HUMAN_TYPING_ERRORS else "✗ Disabled")
        table.add_row("Export Format", self.export_format.upper())

        if self.use_proxies and Config.ENABLE_PROXY:
            table.add_row("Loaded Proxies", f"{proxy_manager.count} total")
            stats = proxy_manager.get_stats()
            table.add_row("Healthy Proxies", f"{stats.get('healthy', 0)}")

        console.print("\n")
        console.print(table)
        console.print("\n")

    def generate_username(self):
        """Generate a unique username."""
        from core.selenium_runner import generate_name
        name = generate_name()
        parts = name.split()
        first = parts[0].lower() if parts else "user"
        last = parts[-1].lower() if len(parts) > 1 else "gmail"
        username = f"{first}{last}{random.randint(1000, 9999)}"
        return username, parts

    def select_flow_mode(self):
        """Intelligently select the best flow mode."""
        if self.flow_mode != 'auto':
            return self.flow_mode

        # Auto-select based on configuration
        if self.use_sms:
            return 'standard'  # Standard mode works best with SMS
        else:
            # Rotate between ghost methods for free mode
            modes = ['standard', 'youtube', 'workspace']
            return random.choice(modes)

    def create_single_account(self, index, progress, task_id):
        """Create a single account with all optimizations."""
        engine = Config.ENGINE_MODE.lower()
        password = Config.YOUR_PASSWORD

        # Generate credentials
        username, name_parts = self.generate_username()
        first_name = name_parts[0] if name_parts else "User"
        last_name = name_parts[-1] if len(name_parts) > 1 else "User"

        # Generate password if not set
        if not password:
            from core.selenium_runner import generate_password
            password = generate_password()

        # Get proxy
        proxy = None
        if self.use_proxies and Config.ENABLE_PROXY:
            proxy = proxy_manager.get_best() or proxy_manager.get_next()

        # Select flow mode
        flow_mode = self.select_flow_mode()

        progress.update(task_id, description=f"[cyan]Creating {username}@gmail.com...[/cyan]")

        # Retry logic
        max_retries = 2 if (proxy and proxy_manager.count > 1) else 1
        success = False

        for attempt in range(max_retries):
            if attempt > 0:
                # Retry with different proxy
                old_proxy = proxy
                if old_proxy:
                    proxy_manager.mark_failure(old_proxy, fatal=True)
                proxy = proxy_manager.get_next()

                # Regenerate credentials
                username, name_parts = self.generate_username()
                first_name = name_parts[0] if name_parts else "User"
                last_name = name_parts[-1] if len(name_parts) > 1 else "User"

                if not Config.YOUR_PASSWORD:
                    from core.selenium_runner import generate_password
                    password = generate_password()

                progress.update(task_id, description=f"[yellow]Retry {attempt+1}: {username}@gmail.com[/yellow]")
                time.sleep(random.randint(5, 15))

            try:
                # Execute creation based on engine
                if engine == 'playwright':
                    from core.runners import run_playwright_flow
                    success = run_playwright_flow(
                        index, self.num_accounts, username, first_name, last_name,
                        password, progress, task_id, proxy,
                        use_sms_api=self.use_sms, flow_mode=flow_mode,
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
                        mode=flow_mode, proxy=proxy,
                    )

                if success:
                    break

            except Exception as e:
                logging.error(f"Account {index+1} error: {e}")
                progress.update(task_id, description=f"[red]Error: {str(e)[:50]}...[/red]")

        # Mark proxy result
        if proxy:
            if success:
                proxy_manager.mark_success(proxy)
            else:
                proxy_manager.mark_failure(proxy)

        # Store result
        if success:
            self.successes += 1
            self.created_accounts.append({
                'email': f"{username}@gmail.com",
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'created_at': datetime.now().isoformat(),
                'flow_mode': flow_mode,
            })
            progress.update(task_id, description=f"[green]✓ {username}@gmail.com created[/green]")
        else:
            self.failures += 1
            progress.update(task_id, description=f"[red]✗ {username}@gmail.com failed[/red]")

        return success

    def run(self):
        """Execute the streamlined creation flow."""
        self.start_time = time.time()

        # Setup
        self.setup_logging()
        self.show_banner()

        # Validate
        if not self.validate_config():
            return False

        # Show config
        self.show_config_summary()

        console.print(f"[bold green]Starting creation of {self.num_accounts} account(s)...[/bold green]\n")

        # Create accounts with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            overall_task = progress.add_task(
                "[cyan]Overall Progress",
                total=self.num_accounts
            )

            for i in range(self.num_accounts):
                current_task = progress.add_task(
                    f"[cyan]Account {i+1}/{self.num_accounts}",
                    total=100
                )

                self.create_single_account(i, progress, current_task)

                progress.update(overall_task, advance=1)
                progress.remove_task(current_task)

                # Delay between accounts (except last one)
                if i < self.num_accounts - 1:
                    delay = Config.DELAY_BETWEEN_ACCOUNTS
                    progress.add_task(
                        f"[dim]Waiting {delay}s before next account...",
                        total=delay
                    )
                    time.sleep(delay)

        # Show results
        self.show_results()

        # Export accounts
        if self.created_accounts:
            self.export_accounts()

        # Save to database
        duration = time.time() - self.start_time
        self.db.save_session_stats(
            total_attempts=self.num_accounts,
            successes=self.successes,
            failures=self.failures,
            strategies_used={self.flow_mode: self.num_accounts},
            errors={},
            duration_seconds=duration,
        )

        # Telegram notification
        try:
            from core.telegram_notifier import notifier
            if notifier.enabled:
                notifier.notify_batch_complete(
                    self.num_accounts, self.successes, self.failures, duration
                )
        except Exception:
            pass

        return self.successes > 0

    def show_results(self):
        """Display final results."""
        duration = time.time() - self.start_time
        success_rate = (self.successes / self.num_accounts * 100) if self.num_accounts > 0 else 0

        # Results panel
        results = f"""
[bold green]✓ Successful:[/bold green] {self.successes}
[bold red]✗ Failed:[/bold red] {self.failures}
[bold cyan]Success Rate:[/bold cyan] {success_rate:.1f}%
[bold yellow]Duration:[/bold yellow] {duration:.1f}s ({duration/60:.1f} minutes)
"""

        if self.num_accounts > 0:
            avg_time = duration / self.num_accounts
            results += f"[bold magenta]Avg per Account:[/bold magenta] {avg_time:.1f}s\n"

        console.print("\n")
        console.print(Panel(
            results,
            title="[bold white]Final Results[/bold white]",
            border_style="green" if success_rate > 50 else "red",
            padding=(1, 2)
        ))

        # Show created accounts
        if self.created_accounts:
            console.print("\n[bold green]Created Accounts:[/bold green]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Email", style="green")
            table.add_column("Password", style="yellow")
            table.add_column("Name", style="cyan")

            for idx, acc in enumerate(self.created_accounts, 1):
                table.add_row(
                    str(idx),
                    acc['email'],
                    acc['password'],
                    f"{acc['first_name']} {acc['last_name']}"
                )

            console.print(table)
            console.print()

    def export_accounts(self):
        """Export created accounts to file."""
        if not self.created_accounts:
            return

        try:
            if self.export_format == 'json':
                path = account_manager.export_json()
                console.print(f"[green]✓ Exported to:[/green] {path}")
            elif self.export_format == 'csv':
                path = account_manager.export_csv()
                console.print(f"[green]✓ Exported to:[/green] {path}")
            elif self.export_format == 'txt':
                path = account_manager.export_txt()
                console.print(f"[green]✓ Exported to:[/green] {path}")
            else:
                # Export all formats
                paths = []
                paths.append(account_manager.export_json())
                paths.append(account_manager.export_csv())
                paths.append(account_manager.export_txt())
                console.print(f"[green]✓ Exported to multiple formats:[/green]")
                for p in paths:
                    console.print(f"  • {p}")
        except Exception as e:
            console.print(f"[red]Export error: {e}[/red]")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Gmail Infinity Factory - Streamlined Automated Creator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create 5 accounts without SMS (free mode)
  python streamlined_creator.py -n 5

  # Create 10 accounts with SMS verification
  python streamlined_creator.py -n 10 --sms

  # Create 3 accounts without proxies
  python streamlined_creator.py -n 3 --no-proxies

  # Create 20 accounts and export to all formats
  python streamlined_creator.py -n 20 --export all

  # Create 1 account with specific flow mode
  python streamlined_creator.py -n 1 --flow youtube
        """
    )

    parser.add_argument('-n', '--num-accounts', type=int, default=1,
                        help='Number of accounts to create (default: 1)')
    parser.add_argument('--sms', action='store_true',
                        help='Enable SMS verification (requires API keys)')
    parser.add_argument('--no-proxies', action='store_true',
                        help='Disable proxy rotation')
    parser.add_argument('--no-warmup', action='store_true',
                        help='Skip account warming phase')
    parser.add_argument('--export', choices=['json', 'csv', 'txt', 'all'], default='json',
                        help='Export format (default: json)')
    parser.add_argument('--flow', choices=['auto', 'standard', 'youtube', 'workspace'], default='auto',
                        help='Creation flow mode (default: auto)')
    parser.add_argument('--headless', action='store_true',
                        help='Force headless browser mode')

    args = parser.parse_args()

    # Override config if headless specified
    if args.headless:
        Config.HEADLESS_MODE = True

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Create and run
    creator = StreamlinedCreator(
        num_accounts=args.num_accounts,
        use_sms=args.sms,
        use_proxies=not args.no_proxies,
        warmup=not args.no_warmup,
        export_format=args.export,
        flow_mode=args.flow,
    )

    success = creator.run()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
