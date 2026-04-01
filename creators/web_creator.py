#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WEB_CREATOR.PY - v2026.∞                                 ║
║              Primary Gmail Account Creation Engine                          ║
║              Quantum Stealth | Human Emulation | Anti-Detection             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import re
import json
import time
import base64
import threading
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml

import playwright
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
from playwright_stealth import stealth_async

from ..core.fingerprint_generator import QuantumFingerprint, QuantumFingerprintFactory
from ..core.stealth_browser import StealthBrowserEngine, StealthConfig
from ..verification.sms_providers import SMSProviderFactory, SMSProviderType
from ..verification.captcha_solver import CaptchaSolverFactory
from ..identity.persona_generator import PersonaGenerator, HumanPersona


@dataclass
class GmailAccount:
    """Represents a created Gmail account with full metadata"""
    email: str
    password: str
    first_name: str
    last_name: str
    birthday: str
    gender: str
    phone_number: Optional[str] = None
    recovery_email: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    fingerprint_id: str = ""
    proxy_ip: str = ""
    user_agent: str = ""
    cookies: str = ""
    tokens: Dict[str, str] = field(default_factory=dict)
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "email": self.email,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birthday": self.birthday,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "recovery_email": self.recovery_email,
            "created_at": self.created_at,
            "fingerprint_id": self.fingerprint_id,
            "proxy_ip": self.proxy_ip,
            "user_agent": self.user_agent,
            "status": self.status
        }
    
    def to_encrypted_dict(self, encryption_key: bytes) -> Dict[str, str]:
        """Encrypt sensitive data for storage"""
        from cryptography.fernet import Fernet
        cipher = Fernet(encryption_key)
        
        encrypted = {}
        for key, value in self.to_dict().items():
            if value:
                if key in ['password', 'cookies', 'tokens']:
                    encrypted[key] = cipher.encrypt(str(value).encode()).decode()
                else:
                    encrypted[key] = str(value)
            else:
                encrypted[key] = ""
        
        return encrypted


class WebGmailCreator:
    """
    Advanced Gmail account creator with quantum-grade stealth
    Implements full human behavior simulation and anti-detection
    """
    
    def __init__(
        self,
        headless: bool = False,
        proxy_list: List[str] = None,
        sms_provider: SMSProviderType = SMSProviderType.FIVESIM,
        captcha_api_key: str = None,
        fingerprint_factory: QuantumFingerprintFactory = None,
        persona_generator: PersonaGenerator = None,
        output_dir: str = "./accounts",
        encryption_key: bytes = None,
        max_concurrent: int = 3,
        verbose: bool = True
    ):
        """
        Initialize the Web Gmail Creator with full configuration
        """
        self.headless = headless
        self.proxy_list = proxy_list or []
        self.proxy_index = 0
        self.sms_provider = SMSProviderFactory.create(sms_provider)
        self.captcha_solver = CaptchaSolverFactory.create(captcha_api_key) if captcha_api_key else None
        self.fingerprint_factory = fingerprint_factory or QuantumFingerprintFactory()
        self.persona_generator = persona_generator or PersonaGenerator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.max_concurrent = max_concurrent
        self.verbose = verbose
        
        # Statistics
        self.stats = {
            "created": 0,
            "failed": 0,
            "captcha_solved": 0,
            "sms_received": 0,
            "total_time": 0
        }
        
        # Browser engine
        self.stealth_engine = StealthBrowserEngine()
        
        # Create session file
        self.session_file = self.output_dir / "created_accounts.enc"
        self.accounts = []
        
        # Thread lock for proxy selection
        self._proxy_lock = threading.Lock()
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.playwright.stop()
    
    def _get_next_proxy(self) -> Optional[str]:
        """Thread-safe round-robin proxy selection"""
        if not self.proxy_list:
            return None
        
        with self._proxy_lock:
            proxy = self.proxy_list[self.proxy_index % len(self.proxy_list)]
            self.proxy_index += 1
            return proxy
    
    async def _create_browser_context(
        self,
        fingerprint: QuantumFingerprint,
        proxy: str = None
    ) -> Tuple[BrowserContext, Page, Browser]:
        """
        Create a stealth browser context with quantum fingerprint
        """
        browser_args = []
        
        # Proxy configuration
        if proxy:
            browser_args.append(f'--proxy-server={proxy}')
        
        # Anti-detection arguments
        browser_args.extend([
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-web-security',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            '--disable-features=OutOfBlinkCors',
            '--disable-webgl',
            '--disable-2d-canvas-clip-aa',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu-memory-buffer-video-frames',
            '--disable-canvas-aa',
            '--disable-accelerated-mjpeg-decode',
            '--disable-accelerated-video-decode',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ])
        
        # Launch browser - configurable via settings.yaml or environment variable
        import os
        import yaml
        browser_path = os.environ.get('BRAVE_BROWSER_PATH', '')
        if not browser_path:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.yaml')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'stealth' in config:
                            browser_path = config['stealth'].get('browser_path', '')
                except:
                    pass
        browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args,
            executable_path=browser_path or None
        )

        # Create context with fingerprint
        context = await browser.new_context(
            viewport={
                'width': fingerprint.screen_width,
                'height': fingerprint.screen_height
            },
            user_agent=fingerprint.user_agent,
            locale=fingerprint.language,
            timezone_id=fingerprint.timezone,
            permissions=['geolocation'],
            device_scale_factor=fingerprint.screen_pixel_ratio,
            has_touch=False,
            color_scheme='light',
            reduced_motion='no-preference',
            forced_colors='none',
            is_mobile=False,
            screen={
                'width': fingerprint.screen_width,
                'height': fingerprint.screen_height
            }
        )

        # Add stealth scripts
        page = await context.new_page()
        await stealth_async(page)

        # Inject fingerprint overrides
        await self._inject_fingerprint_overrides(page, fingerprint)

        return context, page, browser
    
    async def _inject_fingerprint_overrides(self, page: Page, fingerprint: QuantumFingerprint):
        """
        Inject JavaScript to override fingerprinting APIs
        """
        override_script = f"""
        // Override WebGL fingerprinting
        const getParameterProxyHandler = {{
            apply: function(target, thisArg, argumentsList) {{
                const param = argumentsList[0];
                if (param === 37445) {{ // UNMASKED_VENDOR_WEBGL
                    return '{fingerprint.gpu_vendor}';
                }}
                if (param === 37446) {{ // UNMASKED_RENDERER_WEBGL
                    return '{fingerprint.gpu_renderer}';
                }}
                return Reflect.apply(target, thisArg, argumentsList);
            }}
        }};
        
        // Override Canvas fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
            const canvas = this;
            const context = canvas.getContext('2d');
            
            // Add deterministic noise to make fingerprint unique
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {{
                data[i] ^= {hash(fingerprint.canvas_hash) % 3};     // R
                data[i+1] ^= {(hash(fingerprint.canvas_hash) >> 8) % 3}; // G
                data[i+2] ^= {(hash(fingerprint.canvas_hash) >> 16) % 3}; // B
            }}
            context.putImageData(imageData, 0, 0);
            
            return originalToDataURL.call(this, type, quality);
        }};
        
        // Override navigator properties
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint.hardware_concurrency}
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fingerprint.device_memory}
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint.platform}'
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{fingerprint.language}'
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => {json.dumps(fingerprint.languages)}
        }});
        
        // Remove webdriver property
        delete navigator.__proto__.webdriver;
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = {json.dumps(fingerprint.plugins)};
                plugins.length = plugins.length;
                plugins.item = (i) => plugins[i];
                plugins.namedItem = (name) => plugins.find(p => p.includes(name));
                return plugins;
            }}
        }});
        
        console.log('[STEALTH] Fingerprint overrides injected');
        """
        
        await page.add_init_script(override_script)
    
    async def _human_type(self, page: Page, selector: str, text: str, delay_range: Tuple[int, int] = (80, 220)):
        """
        Human-like typing with random delays and occasional mistakes
        """
        element = await page.wait_for_selector(selector, state='visible')
        await element.click()
        
        # Clear existing text
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')
        
        # Type with human-like speed and errors
        for char in text:
            # Random typing speed (80-220ms per character)
            await asyncio.sleep(random.randint(*delay_range) / 1000)
            
            # Occasional typo (5% chance)
            if random.random() < 0.05 and len(text) > 5:
                typo_char = chr(ord(char) + random.choice([-1, 1]))
                await page.keyboard.type(typo_char)
                await asyncio.sleep(0.15)
                await page.keyboard.press('Backspace')
                await asyncio.sleep(0.1)
            
            await page.keyboard.type(char)
            
            # Random pause after certain characters
            if char in ['.', ',', ' ', '@']:
                await asyncio.sleep(random.uniform(0.2, 0.5))
    
    async def _human_mouse_movement(self, page: Page, target_x: int, target_y: int):
        """
        Simulate human mouse movement with Bezier curves
        """
        current_pos = await page.evaluate('''() => {
            return {x: window.mouseX || 0, y: window.mouseY || 0};
        }''')
        
        start_x, start_y = current_pos.get('x', 100), current_pos.get('y', 100)
        
        # Generate Bezier curve control points
        cp1_x = start_x + (target_x - start_x) * random.uniform(0.2, 0.4)
        cp1_y = start_y + (target_y - start_y) * random.uniform(0.1, 0.3)
        cp2_x = start_x + (target_x - start_x) * random.uniform(0.6, 0.8)
        cp2_y = start_y + (target_y - start_y) * random.uniform(0.7, 0.9)
        
        # Move in steps
        steps = random.randint(15, 30)
        for i in range(steps + 1):
            t = i / steps
            
            # Cubic Bezier interpolation
            x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
            y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y
            
            await page.mouse.move(x, y)
            
            # Variable speed based on distance
            distance = ((target_x - start_x)**2 + (target_y - start_y)**2)**0.5
            delay = random.uniform(0.005, 0.015) * (1 - distance / 2000)
            await asyncio.sleep(delay)
    
    async def _solve_captcha(self, page: Page) -> bool:
        """
        Detect and solve reCAPTCHA v2/v3/invisible
        """
        if not self.captcha_solver:
            if self.verbose:
                print("⚠️ No captcha solver configured, attempting manual detection...")
            
            # Check for reCAPTCHA iframe
            try:
                recaptcha_iframe = await page.wait_for_selector(
                    'iframe[src*="recaptcha"], iframe[src*="captcha"]',
                    timeout=5000
                )
                
                if recaptcha_iframe:
                    # Wait for user to solve (for headful mode)
                    await asyncio.sleep(15)
                    return True
            except:
                pass
            
            return True  # Assume no captcha
        
        # Automated solving via API
        try:
            # Get site key
            site_key = await page.evaluate('''() => {
                const recaptcha = document.querySelector('[data-sitekey]');
                return recaptcha ? recaptcha.getAttribute('data-sitekey') : null;
            }''')
            
            if not site_key:
                # Try to find in iframe src
                iframe = await page.query_selector('iframe[src*="recaptcha"]')
                if iframe:
                    src = await iframe.get_attribute('src')
                    match = re.search(r'[?&]k=([^&]+)', src)
                    if match:
                        site_key = match.group(1)
            
            if site_key:
                current_url = page.url
                token = await self.captcha_solver.solve_recaptcha_v2(
                    site_key=site_key,
                    page_url=current_url
                )
                
                if token:
                    # Inject token
                    await page.evaluate(f'''
                        document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                        window.___grecaptcha_cfg.clients[0].callback('{token}');
                    ''')
                    
                    self.stats['captcha_solved'] += 1
                    return True
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Captcha solving failed: {e}")
        
        return False
    
    async def _handle_phone_verification(self, page: Page, country_code: str = "US") -> Optional[str]:
        """
        Handle phone number verification via SMS provider
        Improved with retry logic and better error handling
        """
        if not self.sms_provider:
            raise ValueError("No SMS provider configured for phone verification")
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            if self.verbose:
                print(f"📱 Requesting phone number from SMS provider (attempt {attempt}/{max_attempts})...")
            
            try:
                # Get phone number from provider
                phone_number = await self.sms_provider.get_number(country_code)
                
                if not phone_number:
                    if self.verbose:
                        print(f"⚠️ Failed to get phone number, retrying...")
                    continue
                
                # Try to find and fill the phone input
                phone_input_selectors = [
                    'input[type="tel"]',
                    'input[name="phoneNumberId"]',
                    'input[aria-label*="Phone"]',
                    'input[id="phoneNumberId"]',
                    'input[name="phoneNumber"]'
                ]
                
                phone_filled = False
                for selector in phone_input_selectors:
                    try:
                        phone_input = await page.wait_for_selector(selector, timeout=3000)
                        if phone_input:
                            await self._human_type(page, selector, phone_number)
                            phone_filled = True
                            break
                    except:
                        continue
                
                if not phone_filled:
                    if self.verbose:
                        print(f"⚠️ Could not find phone input, trying different approach...")
                    # Try clicking first then typing
                    await page.click('body')
                    await asyncio.sleep(0.5)
                    await self._human_type(page, 'input[type="tel"]', phone_number)
                
                await asyncio.sleep(0.5)
                
                # Click next
                next_button_selectors = [
                    'button:has-text("Next")',
                    'button[jsname="LgbsSe"]',
                    'button[type="submit"]'
                ]
                
                for selector in next_button_selectors:
                    try:
                        next_button = await page.wait_for_selector(selector, timeout=3000)
                        if next_button:
                            await self._human_mouse_movement(page, 
                                (await next_button.bounding_box()['x']) + 50,
                                (await next_button.bounding_box()['y']) + 20)
                            await next_button.click()
                            break
                    except:
                        continue
                
                # Wait a bit for potential errors
                await asyncio.sleep(2)
                
                # Check for errors that indicate the number is banned
                error_indicators = await page.query_selector_all('[role="alert"], .o6cuMc, [jsname="ry3kDd"]')
                for error in error_indicators:
                    error_text = await error.text_content()
                    if error_text and ('cannot be used' in error_text.lower() or 'invalid' in error_text.lower()):
                        if self.verbose:
                            print(f"⚠️ Phone number rejected by Google: {error_text[:50]}...")
                        # Ban this number and try again
                        if hasattr(self.sms_provider, 'ban_number'):
                            await self.sms_provider.ban_number(phone_number)
                        continue
                
                # Wait for SMS with extended timeout
                if self.verbose:
                    print(f"⏳ Waiting for SMS to {phone_number}...")
                
                code = await self.sms_provider.wait_for_code(
                    phone_number,
                    timeout=180  # 3 minute timeout
                )
                
                if not code:
                    if self.verbose:
                        print(f"⚠️ No SMS code received, trying new number...")
                    continue
                
                # Enter verification code
                code_input_selectors = [
                    'input[type="tel"]',
                    'input[name="code"]',
                    'input[aria-label*="code"]',
                    'input[id="code"]',
                    'input[name="verificationCode"]'
                ]
                
                code_filled = False
                for selector in code_input_selectors:
                    try:
                        code_input = await page.wait_for_selector(selector, timeout=3000)
                        if code_input:
                            await self._human_type(page, selector, code)
                            code_filled = True
                            break
                    except:
                        continue
                
                if not code_filled:
                    # Try typing anywhere on the page
                    await self._human_type(page, 'body', code)
                
                await asyncio.sleep(0.5)
                
                # Click verify
                verify_button_selectors = [
                    'button:has-text("Verify")',
                    'button:has-text("Next")',
                    'button[jsname="LgbsSe"]'
                ]
                
                for selector in verify_button_selectors:
                    try:
                        verify_button = await page.wait_for_selector(selector, timeout=3000)
                        if verify_button:
                            await verify_button.click()
                            break
                    except:
                        continue
                
                # Wait and check for success
                await asyncio.sleep(2)
                
                # Check if we're past phone verification
                current_url = page.url
                if 'phoneNumberId' not in current_url:
                    self.stats['sms_received'] += 1
                    return phone_number
                    
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Phone verification error: {str(e)[:50]}...")
                continue
        
        raise RuntimeError(f"Phone verification failed after {max_attempts} attempts")
    
    async def _handle_recovery_email(self, page: Page, recovery_email: str = None) -> str:
        """
        Handle recovery email setup (optional)
        """
        if not recovery_email:
            # Generate temp email
            from ..verification.email_recovery import TempMailGenerator
            temp_mail = TempMailGenerator()
            recovery_email = await temp_mail.create_inbox()
        
        try:
            # Check if recovery email is requested
            recovery_selector = 'input[type="email"][aria-label*="recovery"], input[name="recoveryEmail"]'
            recovery_input = await page.query_selector(recovery_selector)
            
            if recovery_input:
                await self._human_type(page, recovery_selector, recovery_email)
                
                # Click next/skip
                next_btn = await page.query_selector('button:has-text("Next"), button[jsname="LgbsSe"]')
                if next_btn:
                    await next_btn.click()
                
                if self.verbose:
                    print(f"📧 Recovery email set: {recovery_email}")
        except:
            pass  # Recovery email not required
        
        return recovery_email
    
    async def _check_for_errors(self, page: Page) -> bool:
        """
        Check for any Google error messages
        """
        error_selectors = [
            '[role="alert"]',
            '.OyEIQ .o6cuMc',
            'div[jsname="ry3kDd"]',
            'span[jsname="V67aGc"]',
            'div:has-text("This phone number cannot be used")',
            'div:has-text("This email address is already associated")',
            'div:has-text("Couldn\'t sign you up")',
            'div:has-text("Something went wrong")'
        ]
        
        for selector in error_selectors:
            try:
                error_element = await page.query_selector(selector)
                if error_element:
                    error_text = await error_element.text_content()
                    if self.verbose:
                        print(f"❌ Google error: {error_text}")
                    return False
            except:
                pass
        
        return True
    
    async def _generate_username(self, page: Page, first_name: str, last_name: str) -> str:
        """
        Generate and check availability of Gmail username
        """
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        base_username = re.sub(r'[^a-z0-9.]', '', base_username)
        
        # Try different variations
        variations = [
            base_username,
            f"{base_username}{random.randint(10, 99)}",
            f"{base_username}{random.randint(100, 999)}",
            f"{first_name[0].lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name[0].lower()}",
            f"{first_name.lower()}{random.randint(10, 99)}",
            f"{last_name.lower()}{random.randint(10, 99)}",
            f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}"
        ]
        
        for username in variations:
            # Type username
            username_input = await page.wait_for_selector('input[type="email"], input[name="Username"]')
            await username_input.click()
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Backspace')
            await self._human_type(page, 'input[type="email"], input[name="Username"]', username)
            
            # Wait for availability check
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Check if available
            try:
                available_indicator = await page.wait_for_selector(
                    'span[jsname="V67aGc"]:has-text("@gmail.com is available")',
                    timeout=2000
                )
                if available_indicator:
                    return f"{username}@gmail.com"
            except:
                continue
        
        # If all taken, generate random username
        random_username = f"user.{random.randint(10000, 99999)}.{random.randint(1000, 9999)}"
        return f"{random_username}@gmail.com"
    
    async def create_single_account(
        self,
        persona: Optional[HumanPersona] = None,
        fingerprint: Optional[QuantumFingerprint] = None,
        proxy: Optional[str] = None,
        use_recovery_email: bool = True,
        use_phone: bool = True,
        country_code: str = "US"
    ) -> Optional[GmailAccount]:
        """
        Create a single Gmail account with full stealth
        """
        start_time = time.time()
        context = None
        page = None
        browser = None
        
        try:
            # 1. Generate persona if not provided
            if not persona:
                persona = await self.persona_generator.generate_persona(
                    country_code=country_code,
                    gender=random.choice(['male', 'female'])
                )
            
            # 2. Generate fingerprint if not provided
            if not fingerprint:
                fingerprint = self.fingerprint_factory.generate_fingerprint(
                    ip_address=proxy.split('@')[-1] if proxy and '@' in proxy else None,
                    country_code=country_code
                )
            
            # 3. Get proxy
            if not proxy:
                proxy = self._get_next_proxy()
            
            # 4. Create browser context
            try:
                context, page, browser = await self._create_browser_context(fingerprint, proxy)
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Failed to initialize browser: {e}")
                return None
            
            try:
                # 5. Navigate to Gmail signup
                if self.verbose:
                    print(f"\n🚀 Creating account for {persona.first_name} {persona.last_name}")
                    print(f"   🌐 Proxy: {proxy or 'None'}")
                    print(f"   🖥️  Browser: {fingerprint.user_agent[:50]}...")
                
                await page.goto(
                    'https://accounts.google.com/signup',
                    wait_until='networkidle',
                    timeout=30000
                )
                
                # Random human-like delay before starting
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                # 6. Fill first name
                await self._human_type(page, 'input[name="firstName"]', persona.first_name)
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                # 7. Fill last name
                await self._human_type(page, 'input[name="lastName"]', persona.last_name)
                await asyncio.sleep(random.uniform(0.5, 1.2))
                
                # 8. Click next
                next_button = await page.wait_for_selector('button:has-text("Next"), button[jsname="LgbsSe"]')
                await next_button.click()
                
                # 9. Wait for navigation and check errors
                await page.wait_for_load_state('networkidle')
                if not await self._check_for_errors(page):
                    raise Exception("Error after name submission")
                
                # 10. Generate and set username
                email = await self._generate_username(page, persona.first_name, persona.last_name)
                if self.verbose:
                    print(f"   📧 Email: {email}")
                
                # 11. Click next
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                
                # 12. Set password
                password = persona.password
                await self._human_type(page, 'input[name="Passwd"]', password)
                await asyncio.sleep(random.uniform(0.3, 0.8))
                await self._human_type(page, 'input[name="ConfirmPasswd"]', password)
                
                # 13. Click next
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                
                # 14. Handle birthday
                month_select = await page.wait_for_selector('select[id="month"], select[aria-label*="Month"]')
                await month_select.select_option(value=str(persona.birth_month))
                
                await self._human_type(page, 'input[id="day"], input[aria-label*="Day"]', str(persona.birth_day))
                await self._human_type(page, 'input[id="year"], input[aria-label*="Year"]', str(persona.birth_year))
                
                # 15. Handle gender
                gender_select = await page.wait_for_selector('select[id="gender"], select[aria-label*="Gender"]')
                gender_value = '1' if persona.gender == 'male' else '2'
                await gender_select.select_option(value=gender_value)
                
                # 16. Click next
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                
                # 17. Handle recovery email if enabled
                recovery_email = None
                if use_recovery_email:
                    try:
                        recovery_email = await self._handle_recovery_email(page)
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Recovery email skipped: {e}")
                
                # 18. Click next
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                
                # 19. Handle phone verification if enabled
                phone_number = None
                if use_phone:
                    try:
                        phone_number = await self._handle_phone_verification(page, country_code)
                        if self.verbose:
                            print(f"   ✅ Phone verified: {phone_number}")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️ Phone verification failed: {e}")
                
                # 20. Handle captcha if present
                await self._solve_captcha(page)
                
                # 21. Click "I Agree" or final button
                try:
                    agree_button = await page.wait_for_selector(
                        'button:has-text("I agree"), button:has-text("Accept"), button[jsname="LgbsSe"]',
                        timeout=5000
                    )
                    await agree_button.click()
                except:
                    pass
                
                # 22. Wait for successful creation
                await page.wait_for_url('**/account**', timeout=15000)
                
                # 23. Create account object
                account = GmailAccount(
                    email=email,
                    password=password,
                    first_name=persona.first_name,
                    last_name=persona.last_name,
                    birthday=f"{persona.birth_year}-{persona.birth_month:02d}-{persona.birth_day:02d}",
                    gender=persona.gender,
                    phone_number=phone_number,
                    recovery_email=recovery_email,
                    fingerprint_id=fingerprint.fingerprint_id,
                    proxy_ip=proxy,
                    user_agent=fingerprint.user_agent,
                    status="created"
                )
                
                # 24. Save cookies
                cookies = await context.cookies()
                account.cookies = json.dumps(cookies)
                
                self.stats['created'] += 1
                self.stats['total_time'] += (time.time() - start_time)
                
                if self.verbose:
                    print(f"   ✅ Account created successfully in {time.time()-start_time:.1f}s")
                
                return account
                
            finally:
                if context: await context.close()
                if browser: await browser.close()
                
        except Exception as e:
            self.stats['failed'] += 1
            if self.verbose:
                print(f"   ❌ Failed: {str(e)[:100]}")
            return None
    
    async def create_bulk(
        self,
        count: int,
        country_codes: List[str] = None,
        use_recovery_email: bool = True,
        use_phone: bool = True,
        max_concurrent: int = None
    ) -> List[GmailAccount]:
        """
        Create multiple Gmail accounts in parallel
        """
        max_concurrent = max_concurrent or self.max_concurrent
        country_codes = country_codes or ['US', 'GB', 'CA', 'AU'] * (count // 4 + 1)
        
        # Generate personas in advance
        if self.verbose:
            print(f"\n🎭 Generating {count} personas...")
        
        personas = []
        for i in range(count):
            country = country_codes[i % len(country_codes)]
            persona = await self.persona_generator.generate_persona(
                country_code=country,
                gender=random.choice(['male', 'female'])
            )
            personas.append(persona)
        
        # Generate fingerprints in advance
        if self.verbose:
            print(f"🖥️  Generating {count} quantum fingerprints...")
        
        fingerprints = self.fingerprint_factory.generate_batch(count)
        
        # Create accounts in parallel
        if self.verbose:
            print(f"⚡ Creating {count} accounts ({max_concurrent} concurrent)...\n")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def create_with_semaphore(index):
            async with semaphore:
                async with self.__class__(
                    headless=self.headless,
                    proxy_list=self.proxy_list,
                    sms_provider=self.sms_provider,
                    captcha_api_key=self.captcha_solver.api_key if self.captcha_solver else None,
                    verbose=False  # Silence per-account output during bulk
                ) as creator:
                    return await creator.create_single_account(
                        persona=personas[index],
                        fingerprint=fingerprints[index],
                        use_recovery_email=use_recovery_email,
                        use_phone=use_phone,
                        country_code=personas[index].country_code
                    )
        
        tasks = [create_with_semaphore(i) for i in range(count)]
        results = await asyncio.gather(*tasks)
        
        # Filter successful accounts
        accounts = [acc for acc in results if acc]
        
        # Save accounts
        self.accounts.extend(accounts)
        await self.save_accounts()
        
        if self.verbose:
            print(f"\n📊 BULK CREATION COMPLETE:")
            print(f"   ✅ Success: {len(accounts)}/{count}")
            print(f"   ❌ Failed: {count - len(accounts)}")
            print(f"   ⏱️  Avg time: {self.stats['total_time']/max(1, self.stats['created']):.1f}s")
            print(f"   📁 Saved to: {self.session_file}")
        
        return accounts
    
    async def save_accounts(self):
        """
        Save created accounts to encrypted file
        """
        from cryptography.fernet import Fernet
        
        # Convert to encrypted dicts
        encrypted_accounts = [
            acc.to_encrypted_dict(self.encryption_key)
            for acc in self.accounts
        ]
        
        data = {
            "created_at": datetime.utcnow().isoformat(),
            "count": len(self.accounts),
            "accounts": encrypted_accounts,
            "stats": self.stats
        }
        
        # Save to file
        with open(self.session_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also save plaintext JSON for immediate use (optional)
        plain_file = self.output_dir / "created_accounts.json"
        with open(plain_file, 'w') as f:
            json.dump([acc.to_dict() for acc in self.accounts], f, indent=2)
    
    async def load_accounts(self) -> List[GmailAccount]:
        """
        Load previously created accounts from file
        """
        if not self.session_file.exists():
            return []
        
        with open(self.session_file, 'r') as f:
            data = json.load(f)
        
        # Decrypt and recreate accounts
        from cryptography.fernet import Fernet
        cipher = Fernet(self.encryption_key)
        
        accounts = []
        for enc_acc in data['accounts']:
            account = GmailAccount(
                email=enc_acc['email'],
                password=cipher.decrypt(enc_acc['password'].encode()).decode(),
                first_name=enc_acc['first_name'],
                last_name=enc_acc['last_name'],
                birthday=enc_acc['birthday'],
                gender=enc_acc['gender'],
                phone_number=enc_acc.get('phone_number'),
                recovery_email=enc_acc.get('recovery_email'),
                created_at=enc_acc['created_at'],
                fingerprint_id=enc_acc['fingerprint_id'],
                proxy_ip=enc_acc['proxy_ip'],
                user_agent=enc_acc['user_agent'],
                status=enc_acc['status']
            )
            accounts.append(account)
        
        self.accounts = accounts
        return accounts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get creation statistics"""
        return {
            **self.stats,
            "success_rate": f"{(self.stats['created'] / max(1, (self.stats['created'] + self.stats['failed'])) * 100):.1f}%",
            "avg_time": f"{self.stats['total_time'] / max(1, self.stats['created']):.1f}s"
        }


def hash(s: str) -> int:
    """Simple hash function for deterministic noise"""
    return sum(ord(c) for c in s) * 0x9e3779b97f4a7c15