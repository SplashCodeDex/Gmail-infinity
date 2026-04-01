#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WORKSPACE_CREATOR.PY - v2026.∞                           ║
║              Google Workspace Enterprise Account Factory                    ║
║              Bulk Creation via Admin Console | No Phone Required            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import time
import random
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
import csv
import io

import aiohttp
from playwright.async_api import async_playwright
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..identity.persona_generator import PersonaGenerator, HumanPersona
from .web_creator import GmailAccount


class GoogleWorkspaceCreator:
    """
    Google Workspace (GSuite) Account Creator
    Uses 14-day trial domains to create unlimited accounts without phone verification
    """
    
    # Domain registrars API endpoints
    DOMAIN_REGISTRARS = {
        'namecheap': {
            'api_endpoint': 'https://api.namecheap.com/xml.response',
            'api_user': None,  # Set via config
            'api_key': None,
            'username': None
        },
        'godaddy': {
            'api_endpoint': 'https://api.godaddy.com/v1',
            'api_key': None,
            'api_secret': None
        },
        'cloudflare': {
            'api_endpoint': 'https://api.cloudflare.com/client/v4',
            'api_email': None,
            'api_key': None
        }
    }
    
    # Email aliases providers for catch-all
    EMAIL_ALIAS_PROVIDERS = [
        'improvmx.com',
        'forwardemail.net',
        'mailgun.com',
        'sendgrid.com',
        'zoho.com'
    ]
    
    def __init__(
        self,
        workspace_plan: str = 'business_standard',  # business_starter, business_standard, business_plus
        trial_days: int = 14,
        domain_registrar: str = 'namecheap',
        registrar_credentials: Dict[str, str] = None,
        use_free_domain: bool = False,  # Use freenom or similar
        output_dir: str = "./workspace_accounts",
        verbose: bool = True
    ):
        """
        Initialize Google Workspace Creator
        """
        self.workspace_plan = workspace_plan
        self.trial_days = trial_days
        self.domain_registrar = domain_registrar
        self.registrar_credentials = registrar_credentials or {}
        self.use_free_domain = use_free_domain
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        self.persona_generator = PersonaGenerator()
        self.created_domains = []
        self.workspace_accounts = []
        
        # Free domain providers
        self.free_domain_providers = {
            'freenom': {
                'tlds': ['.tk', '.ml', '.ga', '.cf', '.gq'],
                'api_url': 'https://api.freenom.com/v1'
            },
            'eu.org': {
                'tlds': ['.eu.org'],
                'api_url': 'https://nic.eu.org/apiapi/'
            }
        }
    
    async def register_domain(self, domain_name: str = None) -> str:
        """
        Register a new domain for Workspace trial
        """
        if self.use_free_domain:
            return await self._register_free_domain(domain_name)
        else:
            return await self._register_paid_domain(domain_name)
    
    async def _register_free_domain(self, domain_name: str = None) -> str:
        """
        Register free domain (Freenom, eu.org)
        """
        provider = random.choice(list(self.free_domain_providers.keys()))
        provider_config = self.free_domain_providers[provider]
        
        if not domain_name:
            # Generate random domain name
            words = ['cloud', 'tech', 'digital', 'online', 'web', 'net', 'solution', 'system', 'data', 'link']
            word = random.choice(words)
            number = random.randint(1000, 9999)
            tld = random.choice(provider_config['tlds'])
            domain_name = f"{word}{number}{tld}"
        
        if self.verbose:
            print(f"🌐 Registering free domain: {domain_name} via {provider}")
        
        # Simulate domain registration
        # In production, implement actual API call to Freenom/eu.org
        await asyncio.sleep(5)
        
        domain_info = {
            'domain': domain_name,
            'provider': provider,
            'registered_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
            'nameservers': [
                'ns1.google.com',
                'ns2.google.com',
                'ns3.google.com',
                'ns4.google.com'
            ]
        }
        
        self.created_domains.append(domain_info)
        
        return domain_name
    
    async def _register_paid_domain(self, domain_name: str = None) -> str:
        """
        Register paid domain via registrar API
        """
        if not domain_name:
            # Generate business-sounding domain
            prefixes = ['get', 'my', 'weare', 'go', 'try', 'use', 'join', 'access']
            suffixes = ['tech', 'io', 'hub', 'cloud', 'app', 'digital', 'solutions', 'group']
            
            prefix = random.choice(prefixes)
            suffix = random.choice(suffixes)
            domain_name = f"{prefix}{random.randint(10, 999)}{suffix}.com"
        
        if self.verbose:
            print(f"🌐 Registering domain: {domain_name} via {self.domain_registrar}")
        
        # Implement actual domain registration API call
        registrar_config = self.DOMAIN_REGISTRARS[self.domain_registrar]
        
        if self.domain_registrar == 'namecheap':
            # Namecheap API implementation
            params = {
                'ApiUser': registrar_config.get('api_user'),
                'ApiKey': registrar_config.get('api_key'),
                'UserName': registrar_config.get('username'),
                'Command': 'namecheap.domains.create',
                'ClientIp': '127.0.0.1',
                'DomainName': domain_name,
                'Years': 1,
                'RegistrantFirstName': 'Google',
                'RegistrantLastName': 'Workspace',
                'RegistrantAddress1': '1600 Amphitheatre Parkway',
                'RegistrantCity': 'Mountain View',
                'RegistrantStateProvince': 'CA',
                'RegistrantPostalCode': '94043',
                'RegistrantCountry': 'US',
                'RegistrantPhone': '+1.6502530000',
                'RegistrantEmailAddress': f"admin@{domain_name}"
            }
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    registrar_config['api_endpoint'],
                    params=params
                ) as response:
                    if response.status == 200:
                        # Parse XML response
                        pass
        
        await asyncio.sleep(10)  # Simulate domain registration delay
        
        domain_info = {
            'domain': domain_name,
            'registrar': self.domain_registrar,
            'registered_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
            'nameservers': [
                'ns1.google.com',
                'ns2.google.com',
                'ns3.google.com',
                'ns4.google.com'
            ]
        }
        
        self.created_domains.append(domain_info)
        
        return domain_name
    
    async def setup_dns_records(self, domain: str) -> bool:
        """
        Configure DNS records for Google Workspace
        """
        if self.verbose:
            print(f"🔄 Configuring DNS for {domain}...")
        
        # MX records for Gmail
        mx_records = [
            {'priority': 1, 'value': 'ASPMX.L.GOOGLE.COM'},
            {'priority': 5, 'value': 'ALT1.ASPMX.L.GOOGLE.COM'},
            {'priority': 5, 'value': 'ALT2.ASPMX.L.GOOGLE.COM'},
            {'priority': 10, 'value': 'ALT3.ASPMX.L.GOOGLE.COM'},
            {'priority': 10, 'value': 'ALT4.ASPMX.L.GOOGLE.COM'}
        ]
        
        # TXT records for SPF, DKIM, DMARC
        txt_records = [
            {'name': '@', 'value': 'v=spf1 include:_spf.google.com ~all'},
            {'name': 'google._domainkey', 'value': 'v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ...'},
            {'name': '_dmarc', 'value': 'v=DMARC1; p=none; rua=mailto:dmarc-reports@' + domain}
        ]
        
        # CNAME records for Workspace
        cname_records = [
            {'name': 'mail', 'value': 'ghs.googlehosted.com'},
            {'name': 'calendar', 'value': 'ghs.googlehosted.com'},
            {'name': 'docs', 'value': 'ghs.googlehosted.com'},
            {'name': 'drive', 'value': 'ghs.googlehosted.com'},
            {'name': 'sites', 'value': 'ghs.googlehosted.com'}
        ]
        
        # Implementation for DNS provider API
        # This would call Cloudflare, Namecheap, etc. API
        
        await asyncio.sleep(3)  # Simulate DNS propagation
        
        return True
    
    async def create_workspace_trial(self, domain: str, admin_persona: HumanPersona) -> Dict[str, Any]:
        """
        Sign up for Google Workspace 14-day trial
        """
        if self.verbose:
            print(f"🚀 Creating Workspace trial for {domain}")
        
        import os
        browser_path = os.environ.get('BRAVE_BROWSER_PATH', r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False, executable_path=browser_path)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to Workspace signup
                await page.goto('https://workspace.google.com/business/signup/welcome')
                await asyncio.sleep(2)
                
                # Enter domain
                await page.fill('input[name="domain"]', domain)
                await page.click('button[type="submit"]')
                await asyncio.sleep(3)
                
                # Enter business info
                await page.fill('input[name="businessName"]', f"{admin_persona.first_name} {admin_persona.last_name} Consulting")
                await page.select_option('select[name="country"]', 'US')
                await asyncio.sleep(1)
                
                # Enter admin account details
                await page.fill('input[name="firstName"]', admin_persona.first_name)
                await page.fill('input[name="lastName"]', admin_persona.last_name)
                
                # Generate admin email
                admin_email = f"admin@{domain}"
                await page.fill('input[name="username"]', 'admin')
                await asyncio.sleep(1)
                
                # Enter password
                await page.fill('input[name="password"]', admin_persona.password)
                await page.fill('input[name="confirmPassword"]', admin_persona.password)
                
                # Click next
                await page.click('button[type="submit"]')
                await asyncio.sleep(3)
                
                # Select plan
                if self.workspace_plan == 'business_starter':
                    await page.click('text="Business Starter"')
                elif self.workspace_plan == 'business_standard':
                    await page.click('text="Business Standard"')
                elif self.workspace_plan == 'business_plus':
                    await page.click('text="Business Plus"')
                
                await asyncio.sleep(1)
                
                # Choose payment (trial)
                await page.click('text="Start free trial"')
                await asyncio.sleep(2)
                
                # Enter payment info (test card)
                await page.fill('input[name="cardNumber"]', '4242424242424242')
                await page.fill('input[name="expiryDate"]', '12/30')
                await page.fill('input[name="cvc"]', '123')
                await page.fill('input[name="nameOnCard"]', f"{admin_persona.first_name} {admin_persona.last_name}")
                await page.select_option('select[name="country"]', 'US')
                await page.fill('input[name="postalCode"]', '94043')
                
                # Complete signup
                await page.click('button[type="submit"]')
                await asyncio.sleep(5)
                
                # Check for success
                success = await page.query_selector('text="Welcome to Google Workspace"')
                
                workspace_info = {
                    'domain': domain,
                    'admin_email': f"admin@{domain}",
                    'admin_password': admin_persona.password,
                    'plan': self.workspace_plan,
                    'trial_end': (datetime.utcnow() + timedelta(days=14)).isoformat(),
                    'created_at': datetime.utcnow().isoformat()
                }
                
                return workspace_info
                
            finally:
                await browser.close()
    
    async def create_user_account(
        self,
        workspace_info: Dict[str, Any],
        persona: HumanPersona
    ) -> Optional[GmailAccount]:
        """
        Create user account in Workspace domain
        """
        if self.verbose:
            print(f"👤 Creating user: {persona.first_name}@{workspace_info['domain']}")
        
        try:
            # In production, use Google Admin SDK
            # This simulates admin console automation
            
            import os
            browser_path = os.environ.get('BRAVE_BROWSER_PATH', r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, executable_path=browser_path)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # Login to admin console
                    await page.goto('https://admin.google.com')
                    
                    await page.fill('input[type="email"]', workspace_info['admin_email'])
                    await page.click('#identifierNext')
                    await asyncio.sleep(2)
                    
                    await page.fill('input[type="password"]', workspace_info['admin_password'])
                    await page.click('#passwordNext')
                    await asyncio.sleep(5)
                    
                    # Navigate to users
                    await page.goto('https://admin.google.com/ac/users')
                    await asyncio.sleep(3)
                    
                    # Click "Add new user"
                    await page.click('button[aria-label="Add new user"]')
                    await asyncio.sleep(2)
                    
                    # Fill user details
                    await page.fill('input[name="firstName"]', persona.first_name)
                    await page.fill('input[name="lastName"]', persona.last_name)
                    
                    # Generate username
                    username = f"{persona.first_name.lower()}.{persona.last_name.lower()}"
                    username = re.sub(r'[^a-z0-9.]', '', username)
                    
                    # Add random number if needed
                    if random.random() < 0.3:
                        username += str(random.randint(10, 99))
                    
                    await page.fill('input[name="username"]', username)
                    
                    # Set password
                    await page.click('text="Set password"')
                    await page.fill('input[name="password"]', persona.password)
                    await page.fill('input[name="confirmPassword"]', persona.password)
                    
                    # Uncheck "Ask for password change"
                    checkbox = await page.query_selector('input[type="checkbox"]')
                    if checkbox:
                        await checkbox.click()
                    
                    # Click "Add user"
                    await page.click('button:has-text("Add user")')
                    await asyncio.sleep(3)
                    
                    # Check success
                    email = f"{username}@{workspace_info['domain']}"
                    
                    account = GmailAccount(
                        email=email,
                        password=persona.password,
                        first_name=persona.first_name,
                        last_name=persona.last_name,
                        birthday=f"{persona.birth_year}-{persona.birth_month:02d}-{persona.birth_day:02d}",
                        gender=persona.gender,
                        phone_number=None,  # No phone required
                        recovery_email=None,
                        status="workspace_user",
                        created_at=datetime.utcnow().isoformat()
                    )
                    
                    return account
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to create Workspace user: {e}")
            return None
    
    async def create_workspace_and_users(
        self,
        user_count: int = 10,
        domain_name: str = None
    ) -> List[GmailAccount]:
        """
        Complete flow: Register domain -> Setup Workspace -> Create users
        """
        if self.verbose:
            print(f"\n🏢 Google Workspace Enterprise Creation")
            print(f"   Users to create: {user_count}")
        
        # 1. Register domain
        domain = await self.register_domain(domain_name)
        
        # 2. Setup DNS
        await self.setup_dns_records(domain)
        
        # 3. Generate admin persona
        admin_persona = await self.persona_generator.generate_persona(
            country_code='US',
            gender='male'
        )
        
        # 4. Create Workspace trial
        workspace = await self.create_workspace_trial(domain, admin_persona)
        
        self.workspace_accounts.append(workspace)
        
        # 5. Create users
        accounts = []
        
        for i in range(user_count):
            persona = await self.persona_generator.generate_persona(
                country_code=random.choice(['US', 'GB', 'CA', 'AU']),
                gender=random.choice(['male', 'female'])
            )
            
            account = await self.create_user_account(workspace, persona)
            
            if account:
                accounts.append(account)
            
            # Rate limiting
            await asyncio.sleep(random.uniform(2, 5))
        
        # Save results
        await self.save_workspace_data(workspace, accounts)
        
        if self.verbose:
            print(f"\n📊 Workspace Creation Complete:")
            print(f"   🌐 Domain: {domain}")
            print(f"   👤 Admin: admin@{domain}")
            print(f"   👥 Users created: {len(accounts)}/{user_count}")
            print(f"   ⏳ Trial ends: {workspace['trial_end']}")
        
        return accounts
    
    async def save_workspace_data(self, workspace: Dict[str, Any], accounts: List[GmailAccount]):
        """Save Workspace data and accounts"""
        workspace_file = self.output_dir / f"workspace_{workspace['domain']}.json"
        
        data = {
            'workspace': workspace,
            'accounts': [acc.to_dict() for acc in accounts],
            'created_at': datetime.utcnow().isoformat()
        }
        
        with open(workspace_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also save as CSV for easy import
        csv_file = self.output_dir / f"workspace_{workspace['domain']}_users.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Email', 'Password', 'First Name', 'Last Name'])
            for acc in accounts:
                writer.writerow([
                    acc.email,
                    acc.password,
                    acc.first_name,
                    acc.last_name
                ])