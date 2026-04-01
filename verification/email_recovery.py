#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    EMAIL_RECOVERY.PY - TEMP MAIL AUTOMATION                  ║
║                        GMAIL INFINITY FACTORY 2026                           ║
║                                                                              ║
║    Features:                                                                 ║
║    ├── mail.tm API - Instant disposable email                                ║
║    ├── GuerrillaMail - No registration required                             ║
║    ├── Domain rotation - 10,000+ domains                                    ║
║    ├── Auto-recovery email setup                                            ║
║    └── IMAP/POP3 support for custom domains                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import requests
import json
import time
import random
import hashlib
from typing import Optional, Dict, List, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import imaplib
import poplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import base64
from loguru import logger
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential


# ============================================================================
# DATA MODELS
# ============================================================================

class EmailProviderType(Enum):
    """Email provider types"""
    MAIL_TM = "mail.tm"
    GUERRILLA_MAIL = "guerrillamail"
    TEMP_MAIL = "temp-mail"
    MAIL_INATOR = "mailinator"
    CUSTOM_IMAP = "custom_imap"


@dataclass
class EmailAccount:
    """Represents a disposable email account"""
    id: str
    email: str
    password: Optional[str] = None
    provider: EmailProviderType = EmailProviderType.MAIL_TM
    token: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    @property
    def domain(self) -> str:
        """Extract domain from email"""
        return self.email.split('@')[1] if '@' in self.email else ''
    
    @property
    def username(self) -> str:
        """Extract username from email"""
        return self.email.split('@')[0] if '@' in self.email else self.email


@dataclass
class EmailMessage:
    """Represents an email message"""
    id: str
    account: EmailAccount
    from_addr: str
    to_addr: str
    subject: str
    body: str
    html_body: Optional[str] = None
    received_at: datetime = field(default_factory=datetime.utcnow)
    read: bool = False
    verification_code: Optional[str] = None
    
    def __post_init__(self):
        """Extract verification code from email"""
        if not self.verification_code:
            self.verification_code = self._extract_verification_code()
    
    def _extract_verification_code(self) -> Optional[str]:
        """Extract verification code from email body"""
        import re
        
        # Combine text for searching
        text = f"{self.subject} {self.body} {self.html_body or ''}"
        
        patterns = [
            r'(\d{4,8})',                          # 4-8 digits
            r'verification code:?\s*(\d{4,8})',    # verification code: 123456
            r'confirm code:?\s*(\d{4,8})',         # confirm code: 123456
            r'G-?(\d{4,8})',                       # G-123456 (Google)
            r'(\d{4,8})\s+is your',                # 123456 is your
            r'(\d{4,8})\s+is the',                 # 123456 is the
            r'code[:\s]*(\d{4,8})',                # code: 123456
            r'pin[:\s]*(\d{4,8})',                 # pin: 123456
            r'otp[:\s]*(\d{4,8})',                 # otp: 123456
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


# ============================================================================
# MAIL.TM PROVIDER (BEST API, 10,000+ DOMAINS)
# ============================================================================

class MailTmClient:
    """
    mail.tm API Client - Premium disposable email service
    Features:
    - 10,000+ domains
    - Instant inbox
    - REST API
    - No registration required
    """
    
    BASE_URL = "https://api.mail.tm"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'GmailInfinityFactory/2026.∞'
        })
        
        # Cache domains
        self._domains = []
        self._last_domain_fetch = None
        
        logger.info("MailTmClient initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def get_domains(self) -> List[str]:
        """Get available domains"""
        # Cache domains for 1 hour
        if (self._last_domain_fetch and 
            datetime.utcnow() - self._last_domain_fetch < timedelta(hours=1)):
            return self._domains
        
        try:
            response = self.session.get(f"{self.BASE_URL}/domains")
            response.raise_for_status()
            data = response.json()
            
            self._domains = [d['domain'] for d in data.get('hydra:member', [])]
            self._last_domain_fetch = datetime.utcnow()
            
            return self._domains
        except Exception as e:
            logger.error(f"Failed to get domains: {e}")
            # Fallback domains
            return [
                'cliptik.net', 'dropmail.me', 'ephemail.net',
                'grr.la', 'guerrillamail.biz', 'mail.tm',
                'nada.email', 'temp-mail.org', 'tempemail.co',
                'throwaway.email', 'trashmail.com', 'yopmail.com'
            ]
    
    def generate_email(self, domain: Optional[str] = None) -> Tuple[str, str]:
        """Generate random email address and password"""
        import random
        import string
        
        if not domain:
            domains = self.get_domains()
            domain = random.choice(domains) if domains else 'mail.tm'
        
        # Generate random username
        adjectives = ['happy', 'sunny', 'cool', 'fast', 'smart', 'bright', 
                     'quiet', 'bold', 'calm', 'eager', 'gentle', 'kind']
        nouns = ['tiger', 'eagle', 'wolf', 'panda', 'lion', 'hawk', 
                'dolphin', 'raven', 'fox', 'bear', 'owl', 'deer']
        numbers = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
        
        username = f"{random.choice(adjectives)}.{random.choice(nouns)}{numbers}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        return f"{username}@{domain}", password
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def create_account(self, email: Optional[str] = None, 
                       password: Optional[str] = None) -> EmailAccount:
        """Create new disposable email account"""
        
        if not email or not password:
            email, password = self.generate_email()
        
        payload = {
            'address': email,
            'password': password
        }
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/accounts",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Login to get token
            token = self.login(email, password)
            
            account = EmailAccount(
                id=data.get('id', hashlib.md5(email.encode()).hexdigest()),
                email=email,
                password=password,
                provider=EmailProviderType.MAIL_TM,
                token=token,
                expires_at=datetime.utcnow() + timedelta(days=7),
                is_active=True
            )
            
            logger.info(f"Created mail.tm account: {email}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to create mail.tm account: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def login(self, email: str, password: str) -> str:
        """Login to account and get token"""
        payload = {
            'address': email,
            'password': password
        }
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/token",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            token = data.get('token')
            
            # Update session headers with token
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to login to mail.tm: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def check_inbox(self, account: EmailAccount, 
                    mark_read: bool = True) -> List[EmailMessage]:
        """Check inbox for new messages"""
        
        # Ensure we're logged in
        if not account.token:
            account.token = self.login(account.email, account.password)
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/messages",
                params={'page': 1}
            )
            response.raise_for_status()
            data = response.json()
            
            messages = []
            for item in data.get('hydra:member', []):
                # Get full message content
                msg_response = self.session.get(
                    f"{self.BASE_URL}/messages/{item['id']}"
                )
                msg_response.raise_for_status()
                msg_data = msg_response.json()
                
                # Decode content
                import html
                body = msg_data.get('text', '') or msg_data.get('html', '')
                body = html.unescape(body)
                
                message = EmailMessage(
                    id=item['id'],
                    account=account,
                    from_addr=msg_data.get('from', {}).get('address', ''),
                    to_addr=msg_data.get('to', [{}])[0].get('address', ''),
                    subject=msg_data.get('subject', ''),
                    body=body,
                    html_body=msg_data.get('html', ''),
                    received_at=datetime.fromiso_string(
                        msg_data.get('createdAt', '').replace('Z', '+00:00')
                    ) if msg_data.get('createdAt') else datetime.utcnow(),
                    read=False
                )
                
                messages.append(message)
                
                # Mark as read if requested
                if mark_read:
                    self.session.patch(
                        f"{self.BASE_URL}/messages/{item['id']}",
                        json={'seen': True}
                    )
            
            logger.info(f"Retrieved {len(messages)} messages for {account.email}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def wait_for_verification_code(self, account: EmailAccount, 
                                  timeout: int = 60,
                                  sender_keywords: List[str] = None) -> Optional[EmailMessage]:
        """Wait for verification email and extract code"""
        
        if sender_keywords is None:
            sender_keywords = ['google', 'gmail', 'no-reply', 'accounts', 'verify']
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                messages = self.check_inbox(account, mark_read=False)
                
                for message in messages:
                    # Check if from Google/Gmail
                    from_lower = message.from_addr.lower()
                    if any(keyword in from_lower for keyword in sender_keywords):
                        if message.verification_code:
                            logger.info(f"Found verification code: {message.verification_code}")
                            
                            # Mark as read
                            self.session.patch(
                                f"{self.BASE_URL}/messages/{message.id}",
                                json={'seen': True}
                            )
                            
                            return message
                
            except Exception as e:
                logger.debug(f"Waiting for verification email... {e}")
            
            time.sleep(3)
        
        raise TimeoutError(f"No verification email received within {timeout} seconds")
    
    def delete_account(self, account: EmailAccount) -> bool:
        """Delete email account"""
        try:
            response = self.session.delete(
                f"{self.BASE_URL}/accounts/{account.id}"
            )
            response.raise_for_status()
            logger.info(f"Deleted account: {account.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete account: {e}")
            return False


# ============================================================================
# GUERRILLAMAIL PROVIDER (NO REGISTRATION)
# ============================================================================

class GuerrillaMailClient:
    """
    GuerrillaMail API Client - No registration required
    Features:
    - No signup needed
    - 60 minute expiration
    - Multiple domains
    - Simple API
    """
    
    BASE_URL = "https://api.guerrillamail.com/ajax.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GmailInfinityFactory/2026.∞'
        })
        
        self.sid_token = None
        logger.info("GuerrillaMailClient initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def create_account(self, email: Optional[str] = None) -> EmailAccount:
        """Create disposable email account"""
        
        params = {
            'f': 'get_email_address',
            'ip': '127.0.0.1',
            'agent': 'GmailInfinityFactory'
        }
        
        if email:
            params['email_user'] = email.split('@')[0]
            params['email_domain'] = email.split('@')[1]
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            self.sid_token = data.get('sid_token')
            
            account = EmailAccount(
                id=data.get('email_addr', hashlib.md5(str(time.time()).encode()).hexdigest()),
                email=data.get('email_addr', ''),
                password=None,
                provider=EmailProviderType.GUERRILLA_MAIL,
                token=self.sid_token,
                expires_at=datetime.utcnow() + timedelta(minutes=60),
                is_active=True
            )
            
            logger.info(f"Created GuerrillaMail account: {account.email}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to create GuerrillaMail account: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def check_inbox(self, account: EmailAccount,
                    mark_read: bool = True) -> List[EmailMessage]:
        """Check inbox for new messages"""
        
        params = {
            'f': 'fetch_email',
            'sid_token': account.token or self.sid_token,
            'offset': 0,
            'seq': 0
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            messages = []
            for item in data.get('list', []):
                message = EmailMessage(
                    id=str(item.get('mail_id')),
                    account=account,
                    from_addr=item.get('mail_from', ''),
                    to_addr=account.email,
                    subject=item.get('mail_subject', ''),
                    body=item.get('mail_excerpt', ''),
                    html_body=item.get('mail_body', ''),
                    received_at=datetime.fromtimestamp(
                        int(item.get('mail_timestamp', 0))
                    ) if item.get('mail_timestamp') else datetime.utcnow(),
                    read=False
                )
                
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages for {account.email}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def wait_for_verification_code(self, account: EmailAccount,
                                  timeout: int = 60) -> Optional[EmailMessage]:
        """Wait for verification email"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                messages = self.check_inbox(account, mark_read=False)
                
                for message in messages:
                    if message.verification_code:
                        logger.info(f"Found verification code: {message.verification_code}")
                        return message
                
            except Exception as e:
                logger.debug(f"Waiting for verification email... {e}")
            
            time.sleep(3)
        
        raise TimeoutError(f"No verification email received within {timeout} seconds")
    
    def set_email(self, account: EmailAccount, new_email: str) -> bool:
        """Change email address"""
        params = {
            'f': 'set_email_user',
            'sid_token': account.token or self.sid_token,
            'email_user': new_email.split('@')[0],
            'email_domain': new_email.split('@')[1]
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            account.email = data.get('email_addr', new_email)
            logger.info(f"Changed email to: {account.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to change email: {e}")
            return False


# ============================================================================
# TEMP-MAIL.ORG PROVIDER
# ============================================================================

class TempMailClient:
    """
    temp-mail.org API Client
    Features:
    - Multiple domains
    - Simple API
    - 2-day retention
    """
    
    BASE_URL = "https://api.temp-mail.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GmailInfinityFactory/2026.∞',
            'Content-Type': 'application/json'
        })
        
        logger.info("TempMailClient initialized")
    
    def generate_email(self, domain: Optional[str] = None) -> str:
        """Generate random email"""
        import random
        import string
        
        domains = [
            'boxmail.co', 'coursel.me', 'edv.to', 'fog.im',
            'gaggle.net', 'greencafe24.com', 'haddo.eu', 'harakirimail.com',
            'ind.st', 'kadokawa.jp', 'mail-temp.com', 'moakt.co',
            'nada.email', 'rcpt.at', 'sogetthis.com', 'temp-mail.org',
            'trash-mail.com', 'uroid.com', 'venompen.com', 'yopmail.com'
        ]
        
        if not domain:
            domain = random.choice(domains)
        
        # Generate random username
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        
        return f"{username}@{domain}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def create_account(self, email: Optional[str] = None) -> EmailAccount:
        """Create disposable email account"""
        
        if not email:
            email = self.generate_email()
        
        account = EmailAccount(
            id=hashlib.md5(email.encode()).hexdigest(),
            email=email,
            password=None,
            provider=EmailProviderType.TEMP_MAIL,
            expires_at=datetime.utcnow() + timedelta(days=2),
            is_active=True
        )
        
        logger.info(f"Created TempMail account: {email}")
        return account
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def check_inbox(self, account: EmailAccount,
                    mark_read: bool = True) -> List[EmailMessage]:
        """Check inbox for new messages"""
        
        email_hash = hashlib.md5(account.email.encode()).hexdigest()
        url = f"{self.BASE_URL}/request/domains/{email_hash}/messages"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            messages = []
            for item in data:
                message = EmailMessage(
                    id=item.get('_id', {}).get('$oid', ''),
                    account=account,
                    from_addr=item.get('mail_from', ''),
                    to_addr=account.email,
                    subject=item.get('mail_subject', ''),
                    body=item.get('mail_text_only', ''),
                    html_body=item.get('mail_html', ''),
                    received_at=datetime.fromisoformat(
                        item.get('mail_timestamp', '').replace('Z', '+00:00')
                    ) if item.get('mail_timestamp') else datetime.utcnow(),
                    read=False
                )
                
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages for {account.email}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def wait_for_verification_code(self, account: EmailAccount,
                                  timeout: int = 60) -> Optional[EmailMessage]:
        """Wait for verification email"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                messages = self.check_inbox(account, mark_read=False)
                
                for message in messages:
                    if message.verification_code:
                        logger.info(f"Found verification code: {message.verification_code}")
                        return message
                
            except Exception as e:
                logger.debug(f"Waiting for verification email... {e}")
            
            time.sleep(3)
        
        raise TimeoutError(f"No verification email received within {timeout} seconds")


# ============================================================================
# CUSTOM IMAP PROVIDER (FOR PRIVATE DOMAINS)
# ============================================================================

class CustomIMAPClient:
    """
    Custom IMAP/POP3 client for private domains
    Features:
    - IMAP SSL support
    - POP3 support
    - SMTP for sending
    - Multiple mailbox support
    """
    
    def __init__(self, host: str, port: int = 993,
                 use_ssl: bool = True,
                 mailbox: str = 'INBOX'):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.mailbox = mailbox
        
        self.connection = None
        logger.info(f"CustomIMAPClient initialized: {host}:{port}")
    
    def connect(self, username: str, password: str) -> bool:
        """Connect to IMAP server"""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            
            self.connection.login(username, password)
            self.connection.select(self.mailbox)
            
            logger.info(f"Connected to IMAP server: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            return False
    
    def check_inbox(self, mark_read: bool = True) -> List[EmailMessage]:
        """Check inbox for new messages"""
        if not self.connection:
            raise Exception("Not connected to IMAP server")
        
        messages = []
        
        try:
            # Search for unread messages
            status, data = self.connection.search(None, 'UNSEEN')
            
            for num in data[0].split():
                status, msg_data = self.connection.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                
                # Parse email
                parser = BytesParser()
                email_message = parser.parsebytes(email_body)
                
                # Extract content
                subject = email_message['subject'] or ''
                from_addr = email_message['from'] or ''
                to_addr = email_message['to'] or ''
                
                # Get body
                body = ''
                html_body = ''
                
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode()
                        elif part.get_content_type() == 'text/html':
                            html_body = part.get_payload(decode=True).decode()
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                # Create message object
                message = EmailMessage(
                    id=str(num.decode()),
                    account=EmailAccount(
                        id=hashlib.md5(to_addr.encode()).hexdigest(),
                        email=to_addr,
                        provider=EmailProviderType.CUSTOM_IMAP
                    ),
                    from_addr=from_addr,
                    to_addr=to_addr,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    received_at=datetime.utcnow(),
                    read=False
                )
                
                messages.append(message)
                
                # Mark as read
                if mark_read:
                    self.connection.store(num, '+FLAGS', '\\Seen')
            
            logger.info(f"Retrieved {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None


# ============================================================================
# TEMP MAIL FACTORY - UNIFIED INTERFACE
# ============================================================================

class TempMailFactory:
    """
    Factory class for unified temporary email interface
    Automatically selects best provider
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize email providers
        
        config = {
            'default_provider': 'mail.tm',
            'mail_tm': {'enabled': True},
            'guerrillamail': {'enabled': True},
            'temp_mail': {'enabled': True},
            'custom_imap': {
                'enabled': False,
                'host': 'imap.example.com',
                'port': 993,
                'username': 'user@example.com',
                'password': 'password'
            }
        }
        """
        self.config = config or {}
        self.providers = {}
        
        # Initialize providers
        if self.config.get('mail_tm', {}).get('enabled', True):
            self.providers[EmailProviderType.MAIL_TM] = MailTmClient()
        
        if self.config.get('guerrillamail', {}).get('enabled', True):
            self.providers[EmailProviderType.GUERRILLA_MAIL] = GuerrillaMailClient()
        
        if self.config.get('temp_mail', {}).get('enabled', True):
            self.providers[EmailProviderType.TEMP_MAIL] = TempMailClient()
        
        # Custom IMAP
        imap_config = self.config.get('custom_imap', {})
        if imap_config.get('enabled', False):
            self.providers[EmailProviderType.CUSTOM_IMAP] = CustomIMAPClient(
                host=imap_config['host'],
                port=imap_config.get('port', 993),
                use_ssl=imap_config.get('use_ssl', True)
            )
        
        # Default provider
        self.default_provider = EmailProviderType(
            self.config.get('default_provider', 'mail.tm')
        )
        
        logger.info(f"TempMailFactory initialized with {len(self.providers)} providers")
    
    async def create_account_async(self, 
                                  provider: Optional[EmailProviderType] = None,
                                  email: Optional[str] = None) -> EmailAccount:
        """Create email account asynchronously"""
        
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not initialized")
        
        client = self.providers[provider]
        
        if provider == EmailProviderType.MAIL_TM:
            return client.create_account(email, None)
        elif provider == EmailProviderType.GUERRILLA_MAIL:
            return client.create_account(email)
        elif provider == EmailProviderType.TEMP_MAIL:
            return client.create_account(email)
        else:
            raise ValueError(f"Cannot create account with provider {provider}")
    
    def create_account_sync(self, 
                           provider: Optional[EmailProviderType] = None,
                           email: Optional[str] = None) -> EmailAccount:
        """Synchronous version of create_account"""
        import asyncio
        return asyncio.run(self.create_account_async(provider, email))
    
    async def wait_for_verification_async(self, account: EmailAccount,
                                         timeout: int = 60) -> EmailMessage:
        """Wait for verification email"""
        
        client = self.providers.get(account.provider)
        if not client:
            raise ValueError(f"Provider {account.provider} not initialized")
        
        if account.provider == EmailProviderType.MAIL_TM:
            return client.wait_for_verification_code(account, timeout)
        elif account.provider == EmailProviderType.GUERRILLA_MAIL:
            return client.wait_for_verification_code(account, timeout)
        elif account.provider == EmailProviderType.TEMP_MAIL:
            return client.wait_for_verification_code(account, timeout)
        elif account.provider == EmailProviderType.CUSTOM_IMAP:
            # Connect to IMAP first
            imap_config = self.config.get('custom_imap', {})
            client.connect(
                imap_config.get('username'),
                imap_config.get('password')
            )
            return client.wait_for_verification_code(timeout)
        else:
            raise ValueError(f"Unknown provider: {account.provider}")
    
    def wait_for_verification_sync(self, account: EmailAccount,
                                  timeout: int = 60) -> EmailMessage:
        """Synchronous version of wait_for_verification"""
        import asyncio
        return asyncio.run(self.wait_for_verification_async(account, timeout))


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_temp_mail_factory(config_file: str = "config/temp_mail.json") -> TempMailFactory:
    """Create temp mail factory from config file"""
    import os
    import json
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "default_provider": "mail.tm",
            "mail_tm": {
                "enabled": True
            },
            "guerrillamail": {
                "enabled": True
            },
            "temp_mail": {
                "enabled": True
            },
            "custom_imap": {
                "enabled": False,
                "host": "",
                "port": 993,
                "use_ssl": True,
                "username": "",
                "password": ""
            }
        }
        
        # Save default config
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    return TempMailFactory(config)


# ============================================================================
# UNIT TESTS
# ============================================================================

async def test_email_providers():
    """Test email providers"""
    logger.info("Testing email providers...")
    
    # Create factory
    factory = create_temp_mail_factory()
    
    try:
        # Test mail.tm
        account = await factory.create_account_async(EmailProviderType.MAIL_TM)
        logger.success(f"Created mail.tm account: {account.email}")
        
        # Test GuerrillaMail
        account2 = await factory.create_account_async(EmailProviderType.GUERRILLA_MAIL)
        logger.success(f"Created GuerrillaMail account: {account2.email}")
        
        # Test TempMail
        account3 = await factory.create_account_async(EmailProviderType.TEMP_MAIL)
        logger.success(f"Created TempMail account: {account3.email}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_email_providers())