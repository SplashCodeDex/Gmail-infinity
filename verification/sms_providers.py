#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SMS_PROVIDERS.PY - REAL SIM CARD RENTAL                   ║
║                        GMAIL INFINITY FACTORY 2026                           ║
║                                                                              ║
║    ⚠️  NOT VOIP - REAL PHYSICAL SIM CARDS FROM 60+ COUNTRIES ⚠️              ║
║    Integrated Providers:                                                     ║
║    ├── 5sim.net          → 80+ countries, instant delivery                  ║
║    ├── sms-activate.ru   → 40+ countries, cheapest rates                    ║
║    ├── textverified.com  → US/UK/CA, highest success rate                   ║
║    └── onlinesim.io      → 30+ countries, no API key required               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import requests
import json
import time
import random
import hashlib
from typing import Optional, Dict, List, Tuple, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import base64
from loguru import logger
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# ============================================================================
# DATA MODELS
# ============================================================================

class ProviderType(Enum):
    """SMS provider types"""
    FIVESIM = "5sim"
    SMS_ACTIVATE = "sms-activate"
    TEXTVERIFIED = "textverified"
    ONLINESIM = "onlinesim"


class CountryCode(Enum):
    """Supported country codes (ISO 3166-1 alpha-2)"""
    US = "us"
    GB = "gb"
    CA = "ca"
    AU = "au"
    DE = "de"
    FR = "fr"
    ES = "es"
    IT = "it"
    NL = "nl"
    SE = "se"
    NO = "no"
    DK = "dk"
    FI = "fi"
    PL = "pl"
    CZ = "cz"
    AT = "at"
    CH = "ch"
    BR = "br"
    MX = "mx"
    AR = "ar"
    ZA = "za"
    NG = "ng"
    EG = "eg"
    SA = "sa"
    AE = "ae"
    IL = "il"
    TR = "tr"
    RU = "ru"
    UA = "ua"
    KZ = "kz"
    BY = "by"
    JP = "jp"
    KR = "kr"
    IN = "in"
    ID = "id"
    MY = "my"
    SG = "sg"
    PH = "ph"
    VN = "vn"
    TH = "th"
    YE = "ye"  # Yemen - no verification often
    SY = "sy"  # Syria - limited infrastructure
    CU = "cu"  # Cuba - restricted
    KP = "kp"  # North Korea - theoretical


class ServiceType(Enum):
    """Service types for SMS activation"""
    GOOGLE = "google"
    GMAIL = "gmail"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    FACEBOOK = "fb"
    INSTAGRAM = "ig"
    TWITTER = "tw"
    MICROSOFT = "ms"
    AMAZON = "amzn"
    TIKTOK = "tiktok"
    DISCORD = "discord"


@dataclass
class PhoneNumber:
    """Represents a rented phone number"""
    id: str
    number: str
    country: CountryCode
    provider: ProviderType
    cost: float
    currency: str = "USD"
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, active, expired, cancelled
    
    @property
    def international_format(self) -> str:
        """Return number in international format"""
        return f"+{self.number}" if not self.number.startswith('+') else self.number
    
    @property
    def e164_format(self) -> str:
        """Return number in E.164 format"""
        num = self.number.replace('+', '').replace(' ', '').replace('-', '')
        return f"+{num}"
    
    @property
    def local_format(self) -> str:
        """Return number in local format"""
        return self.number.replace('+', '').replace(' ', '').replace('-', '')[1:]


@dataclass
class SMSMessage:
    """Represents an SMS message received"""
    id: str
    phone_number: PhoneNumber
    sender: str
    text: str
    code: Optional[str] = None
    received_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Extract verification code from message text"""
        if not self.code:
            self.code = self._extract_verification_code()
    
    def _extract_verification_code(self) -> Optional[str]:
        """Extract numeric/digit verification code from SMS text"""
        import re
        
        # Common patterns for verification codes
        patterns = [
            r'(\d{4,8})',                          # 4-8 digits
            r'code:?\s*(\d{4,8})',                 # code: 123456
            r'verification code:?\s*(\d{4,8})',    # verification code: 123456
            r'is\s*(\d{4,8})',                     # is 123456
            r'G-?(\d{4,8})',                       # G-123456 (Google)
            r'(\d{4,8})\s+is your',                # 123456 is your
            r'(\d{4,8})\s+is the',                 # 123456 is the
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


# ============================================================================
# 5SIM.NET PROVIDER (80+ COUNTRIES, INSTANT DELIVERY)
# ============================================================================

class FiveSimClient:
    """
    5sim.net API Client - Premium SMS provider
    Features:
    - 80+ countries
    - Instant SMS delivery (1-10 seconds)
    - Google Voice numbers available
    - API key authentication
    """
    
    BASE_URL = "https://5sim.net/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'GmailInfinityFactory/2026.∞'
        })
        
        self.balance = 0.0
        self.currency = "USD"
        
        # Cache for product prices
        self._price_cache = {}
        self._last_price_update = None
        
        logger.info(f"5SimClient initialized with API key: {api_key[:8]}...")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def get_balance(self) -> float:
        """Get account balance"""
        try:
            response = self.session.get(f"{self.BASE_URL}/user/profile")
            response.raise_for_status()
            data = response.json()
            self.balance = float(data.get('balance', 0))
            self.currency = data.get('currency', 'USD')
            return self.balance
        except Exception as e:
            logger.error(f"Failed to get 5sim balance: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def search_phone(self, country: Union[str, CountryCode], operator: str = "any", 
                     product: str = "google") -> Dict:
        """Search for available phone numbers"""
        if isinstance(country, CountryCode):
            country = country.value
        
        url = f"{self.BASE_URL}/guest/products/{country}/{operator}/{product}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Cache the prices
            if country not in self._price_cache:
                self._price_cache[country] = {}
            self._price_cache[country][product] = data
            
            return data
        except Exception as e:
            logger.error(f"Failed to search 5sim phones: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def purchase_phone(self, country: Union[str, CountryCode], operator: str = "any",
                       product: str = "google") -> PhoneNumber:
        """Purchase a phone number for activation"""
        if isinstance(country, CountryCode):
            country = country.value
        
        url = f"{self.BASE_URL}/user/buy/activation/{country}/{operator}/{product}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            phone = PhoneNumber(
                id=str(data.get('id')),
                number=data.get('phone', ''),
                country=CountryCode(country),
                provider=ProviderType.FIVESIM,
                cost=float(data.get('price', 0)),
                currency=self.currency,
                expires_at=datetime.utcnow() + timedelta(minutes=20),
                status="active"
            )
            
            logger.info(f"Purchased 5sim phone: {phone.number} for ${phone.cost}")
            return phone
            
        except Exception as e:
            logger.error(f"Failed to purchase 5sim phone: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def wait_for_sms(self, phone_id: str, timeout: int = 120) -> SMSMessage:
        """Wait for SMS verification code"""
        url = f"{self.BASE_URL}/user/check/{phone_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                sms_data = data.get('sms', [])
                if sms_data:
                    latest_sms = sms_data[-1]  # Most recent SMS
                    
                    # Create phone number object
                    phone = PhoneNumber(
                        id=phone_id,
                        number=data.get('phone', ''),
                        country=CountryCode(data.get('country', 'us')),
                        provider=ProviderType.FIVESIM,
                        cost=float(data.get('price', 0)),
                        currency=self.currency,
                        status="completed"
                    )
                    
                    sms = SMSMessage(
                        id=str(latest_sms.get('id', phone_id)),
                        phone_number=phone,
                        sender=latest_sms.get('from', ''),
                        text=latest_sms.get('text', ''),
                        received_at=datetime.utcnow()
                    )
                    
                    logger.info(f"Received SMS from {sms.sender}: {sms.code}")
                    return sms
                
            except Exception as e:
                logger.debug(f"Waiting for SMS... {e}")
            
            time.sleep(3)
        
        raise TimeoutError(f"No SMS received within {timeout} seconds")
    
    def release_phone(self, phone_id: str) -> bool:
        """Release/cancel phone number"""
        url = f"{self.BASE_URL}/user/cancel/{phone_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            logger.info(f"Released phone {phone_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to release phone {phone_id}: {e}")
            return False
    
    def get_available_countries(self) -> List[str]:
        """Get list of available countries"""
        url = f"{self.BASE_URL}/guest/countries"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return list(data.keys())
        except Exception as e:
            logger.error(f"Failed to get countries: {e}")
            return []


# ============================================================================
# SMS-ACTIVATE.RU PROVIDER (CHEAPEST RATES)
# ============================================================================

class SmsActivateClient:
    """
    sms-activate.ru API Client - Budget-friendly SMS provider
    Features:
    - 40+ countries
    - Lowest prices ($0.10-$0.50 per verification)
    - API key authentication
    - Russian/Ukrainian numbers available
    """
    
    BASE_URL = "https://api.sms-activate.org/stubs/handler_api.php"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.balance = 0.0
        
        # Country code mapping (sms-activate uses numeric codes)
        self.COUNTRY_CODES = {
            'ru': 0, 'ua': 1, 'kz': 2, 'us': 187, 'gb': 72,
            'de': 43, 'fr': 68, 'es': 64, 'it': 83, 'nl': 115,
            'pl': 131, 'cz': 56, 'il': 82, 'tr': 160, 'jp': 89,
            'cn': 44, 'in': 86, 'br': 33, 'za': 150, 'ng': 199,
        }
        
        logger.info(f"SmsActivateClient initialized with API key: {api_key[:8]}...")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_balance(self) -> float:
        """Get account balance"""
        params = {
            'api_key': self.api_key,
            'action': 'getBalance'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            text = response.text
            
            if 'ACCESS_BALANCE' in text:
                self.balance = float(text.split(':')[1])
                return self.balance
            else:
                raise Exception(f"Failed to get balance: {text}")
                
        except Exception as e:
            logger.error(f"Failed to get sms-activate balance: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_number(self, country: Union[str, CountryCode], service: str = "go") -> PhoneNumber:
        """Request phone number for activation"""
        if isinstance(country, CountryCode):
            country = country.value
        
        country_code = self.COUNTRY_CODES.get(country, 187)  # Default to US
        
        params = {
            'api_key': self.api_key,
            'action': 'getNumber',
            'service': service,
            'country': country_code
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            text = response.text
            
            if 'ACCESS_NUMBER' in text:
                parts = text.split(':')
                activation_id = parts[1]
                number = parts[2]
                
                phone = PhoneNumber(
                    id=activation_id,
                    number=number,
                    country=CountryCode(country),
                    provider=ProviderType.SMS_ACTIVATE,
                    cost=self._get_service_cost(country, service),
                    currency="RUB",  # API returns RUB
                    expires_at=datetime.utcnow() + timedelta(minutes=20),
                    status="active"
                )
                
                logger.info(f"Purchased sms-activate phone: {phone.number}")
                return phone
            else:
                raise Exception(f"Failed to get number: {text}")
                
        except Exception as e:
            logger.error(f"Failed to get sms-activate number: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def wait_for_sms(self, activation_id: str, timeout: int = 120) -> SMSMessage:
        """Wait for SMS verification code"""
        params = {
            'api_key': self.api_key,
            'action': 'getStatus',
            'id': activation_id
        }
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                text = response.text
                
                if 'STATUS_OK' in text:
                    code = text.split(':')[1]
                    
                    # Create dummy phone object
                    phone = PhoneNumber(
                        id=activation_id,
                        number="unknown",
                        country=CountryCode.US,
                        provider=ProviderType.SMS_ACTIVATE,
                        cost=0,
                        status="completed"
                    )
                    
                    sms = SMSMessage(
                        id=activation_id,
                        phone_number=phone,
                        sender="Google",
                        text=f"Your Google verification code is {code}",
                        code=code,
                        received_at=datetime.utcnow()
                    )
                    
                    logger.info(f"Received SMS code: {code}")
                    return sms
                
            except Exception as e:
                logger.debug(f"Waiting for SMS... {e}")
            
            time.sleep(2)
        
        raise TimeoutError(f"No SMS received within {timeout} seconds")
    
    def set_status(self, activation_id: str, status: int) -> bool:
        """
        Set activation status
        1: Ready for SMS
        3: Request another SMS
        6: Complete activation
        8: Cancel activation
        """
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': activation_id,
            'status': status
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return 'ACCESS' in response.text
        except Exception as e:
            logger.error(f"Failed to set status: {e}")
            return False
    
    def _get_service_cost(self, country: str, service: str = "go") -> float:
        """Get service cost for country"""
        params = {
            'api_key': self.api_key,
            'action': 'getPrices',
            'service': service,
            'country': self.COUNTRY_CODES.get(country, 187)
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            import json
            data = json.loads(response.text)
            return float(data.get(str(self.COUNTRY_CODES.get(country, 187)), {}).get(service, 0))
        except:
            return 0.30  # Default cost


# ============================================================================
# TEXTVERIFIED.COM PROVIDER (HIGHEST SUCCESS RATE)
# ============================================================================

class TextVerifiedClient:
    """
    textverified.com API Client - Premium US/UK/CA numbers
    Features:
    - Real US mobile numbers (not VoIP)
    - Highest success rate (95%+)
    - Instant delivery
    - 30-day number rental available
    """
    
    BASE_URL = "https://api.textverified.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'GmailInfinityFactory/2026.∞'
        })
        
        self.balance = 0.0
        logger.info(f"TextVerifiedClient initialized with API key: {api_key[:8]}...")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_balance(self) -> float:
        """Get account balance"""
        try:
            response = self.session.get(f"{self.BASE_URL}/account")
            response.raise_for_status()
            data = response.json()
            self.balance = float(data.get('balance', 0))
            return self.balance
        except Exception as e:
            logger.error(f"Failed to get TextVerified balance: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def purchase_phone(self, service: str = "google", area_code: str = None) -> PhoneNumber:
        """Purchase a phone number for verification"""
        
        payload = {
            'service': service,
            'rental': False  # One-time verification
        }
        
        if area_code:
            payload['area_code'] = area_code
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/verifications",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            phone = PhoneNumber(
                id=str(data.get('id')),
                number=data.get('phone_number', ''),
                country=CountryCode.US,  # TextVerified is primarily US
                provider=ProviderType.TEXTVERIFIED,
                cost=float(data.get('price', 0)),
                currency="USD",
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                status="active"
            )
            
            logger.info(f"Purchased TextVerified phone: {phone.number} for ${phone.cost}")
            return phone
            
        except Exception as e:
            logger.error(f"Failed to purchase TextVerified phone: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def wait_for_sms(self, verification_id: str, timeout: int = 120) -> SMSMessage:
        """Wait for SMS verification code"""
        url = f"{self.BASE_URL}/verifications/{verification_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'completed':
                    code = data.get('code', '')
                    
                    # Create phone object
                    phone = PhoneNumber(
                        id=verification_id,
                        number=data.get('phone_number', ''),
                        country=CountryCode.US,
                        provider=ProviderType.TEXTVERIFIED,
                        cost=float(data.get('price', 0)),
                        status="completed"
                    )
                    
                    sms = SMSMessage(
                        id=verification_id,
                        phone_number=phone,
                        sender="Google",
                        text=data.get('message', ''),
                        code=code,
                        received_at=datetime.utcnow()
                    )
                    
                    logger.info(f"Received SMS code: {code}")
                    return sms
                
            except Exception as e:
                logger.debug(f"Waiting for SMS... {e}")
            
            time.sleep(2)
        
        raise TimeoutError(f"No SMS received within {timeout} seconds")


# ============================================================================
# ONLINESIM.IO PROVIDER (NO API KEY REQUIRED)
# ============================================================================

class OnlineSimClient:
    """
    onlinesim.io API Client - No API key required
    Features:
    - 30+ countries
    - No registration required
    - Pay-as-you-go
    - Free temporary numbers available
    """
    
    BASE_URL = "https://onlinesim.io/api"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GmailInfinityFactory/2026.∞'
        })
        
        self.balance = 0.0
        logger.info(f"OnlineSimClient initialized (API key: {'provided' if api_key else 'none'})")
    
    def get_balance(self) -> float:
        """Get account balance (if API key provided)"""
        if not self.api_key:
            return 0.0
        
        params = {'apikey': self.api_key} if self.api_key else {}
        
        try:
            response = self.session.get(f"{self.BASE_URL}/getBalance.php", params=params)
            response.raise_for_status()
            data = response.json()
            self.balance = float(data.get('balance', 0))
            return self.balance
        except:
            return 0.0
    
    def get_countries(self) -> List[Dict]:
        """Get available countries"""
        try:
            response = self.session.get(f"{self.BASE_URL}/getCountries.php")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get countries: {e}")
            return []
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_number(self, country_id: int = 7, service: str = "google") -> PhoneNumber:
        """Get a phone number"""
        params = {
            'country': country_id,
            'service': service
        }
        
        if self.api_key:
            params['apikey'] = self.api_key
        
        try:
            response = self.session.get(f"{self.BASE_URL}/getNum.php", params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'tzid' in data:
                phone = PhoneNumber(
                    id=str(data['tzid']),
                    number=data.get('number', ''),
                    country=CountryCode.US,  # Map properly in production
                    provider=ProviderType.ONLINESIM,
                    cost=0.10,  # Default cost
                    currency="USD",
                    expires_at=datetime.utcnow() + timedelta(minutes=20),
                    status="active"
                )
                
                logger.info(f"Purchased OnlineSim phone: {phone.number}")
                return phone
            else:
                raise Exception(f"Failed to get number: {data}")
                
        except Exception as e:
            logger.error(f"Failed to get OnlineSim number: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def wait_for_sms(self, tzid: str, timeout: int = 120) -> SMSMessage:
        """Wait for SMS verification code"""
        params = {'tzid': tzid}
        if self.api_key:
            params['apikey'] = self.api_key
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.BASE_URL}/getState.php", params=params)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and data:
                    state = data[0]
                    
                    if state.get('msg'):
                        code = self._extract_code(state['msg'])
                        
                        phone = PhoneNumber(
                            id=tzid,
                            number=state.get('number', ''),
                            country=CountryCode.US,
                            provider=ProviderType.ONLINESIM,
                            cost=0.10,
                            status="completed"
                        )
                        
                        sms = SMSMessage(
                            id=tzid,
                            phone_number=phone,
                            sender=state.get('service', 'Google'),
                            text=state.get('msg', ''),
                            code=code,
                            received_at=datetime.utcnow()
                        )
                        
                        logger.info(f"Received SMS code: {code}")
                        return sms
                
            except Exception as e:
                logger.debug(f"Waiting for SMS... {e}")
            
            time.sleep(3)
        
        raise TimeoutError(f"No SMS received within {timeout} seconds")
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extract verification code from message"""
        import re
        match = re.search(r'(\d{4,8})', text)
        return match.group(1) if match else None


# ============================================================================
# SMS PROVIDER FACTORY - UNIFIED INTERFACE
# ============================================================================

class SMSProviderFactory:
    """
    Factory class for unified SMS provider interface
    Automatically selects best provider based on country and success rate
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SMS providers with API keys from config
        
        config = {
            '5sim': {'api_key': '...'},
            'sms_activate': {'api_key': '...'},
            'textverified': {'api_key': '...'},
            'onlinesim': {'api_key': '...'},  # Optional
            'default_provider': '5sim',
            'preferred_countries': ['us', 'gb', 'ca', 'ye', 'sy']
        }
        """
        self.config = config
        self.providers = {}
        self.provider_stats = {}
        
        # Initialize providers with API keys
        if '5sim' in config:
            self.providers[ProviderType.FIVESIM] = FiveSimClient(config['5sim']['api_key'])
        
        if 'sms_activate' in config:
            self.providers[ProviderType.SMS_ACTIVATE] = SmsActivateClient(config['sms_activate']['api_key'])
        
        if 'textverified' in config:
            self.providers[ProviderType.TEXTVERIFIED] = TextVerifiedClient(config['textverified']['api_key'])
        
        if 'onlinesim' in config:
            self.providers[ProviderType.ONLINESIM] = OnlineSimClient(
                config['onlinesim'].get('api_key')
            )
        
        # Default provider
        self.default_provider = ProviderType(
            config.get('default_provider', '5sim')
        )
        
        # Preferred countries for bypass (regions with weak verification)
        self.preferred_countries = [
            CountryCode(c) for c in config.get('preferred_countries', 
                                               ['ye', 'sy', 'cu', 'kp', 'ng', 'eg'])
        ]
        
        logger.info(f"SMSProviderFactory initialized with {len(self.providers)} providers")
    
    async def get_phone_async(self, country: Optional[CountryCode] = None,
                             service: ServiceType = ServiceType.GOOGLE) -> PhoneNumber:
        """
        Get phone number asynchronously from best available provider
        """
        # If no country specified, try preferred bypass countries first
        if not country:
            for preferred in self.preferred_countries:
                try:
                    return await self._get_phone_from_provider(preferred, service)
                except:
                    continue
            
            # Fallback to US
            country = CountryCode.US
        
        return await self._get_phone_from_provider(country, service)
    
    def get_phone_sync(self, country: Optional[CountryCode] = None,
                      service: ServiceType = ServiceType.GOOGLE) -> PhoneNumber:
        """Synchronous version of get_phone"""
        import asyncio
        return asyncio.run(self.get_phone_async(country, service))
    
    async def _get_phone_from_provider(self, country: CountryCode,
                                      service: ServiceType) -> PhoneNumber:
        """
        Try to get phone number from providers in order of preference
        """
        # Provider preference order (by success rate)
        provider_order = [
            ProviderType.TEXTVERIFIED,  # Highest success rate, US only
            ProviderType.FIVESIM,       # Good coverage
            ProviderType.SMS_ACTIVATE,  # Cheap, good for bypass countries
            ProviderType.ONLINESIM      # No API key needed
        ]
        
        # Only use TextVerified for US/UK/CA
        if country not in [CountryCode.US, CountryCode.GB, CountryCode.CA]:
            provider_order.remove(ProviderType.TEXTVERIFIED)
        
        errors = []
        
        for provider_type in provider_order:
            if provider_type not in self.providers:
                continue
            
            try:
                provider = self.providers[provider_type]
                
                if provider_type == ProviderType.FIVESIM:
                    phone = provider.purchase_phone(country.value, "any", service.value)
                elif provider_type == ProviderType.SMS_ACTIVATE:
                    phone = provider.get_number(country.value, service.value)
                elif provider_type == ProviderType.TEXTVERIFIED:
                    phone = provider.purchase_phone(service.value)
                elif provider_type == ProviderType.ONLINESIM:
                    phone = provider.get_number(7, service.value)  # 7 = US
                else:
                    continue
                
                # Track success
                self._update_stats(provider_type, True)
                
                return phone
                
            except Exception as e:
                errors.append(f"{provider_type.value}: {str(e)}")
                self._update_stats(provider_type, False)
                continue
        
        raise Exception(f"All providers failed: {'; '.join(errors)}")
    
    async def wait_for_sms_async(self, phone: PhoneNumber, timeout: int = 120) -> SMSMessage:
        """Wait for SMS verification code"""
        provider = self.providers.get(phone.provider)
        if not provider:
            raise ValueError(f"Provider {phone.provider} not initialized")
        
        if phone.provider == ProviderType.FIVESIM:
            return provider.wait_for_sms(phone.id, timeout)
        elif phone.provider == ProviderType.SMS_ACTIVATE:
            return provider.wait_for_sms(phone.id, timeout)
        elif phone.provider == ProviderType.TEXTVERIFIED:
            return provider.wait_for_sms(phone.id, timeout)
        elif phone.provider == ProviderType.ONLINESIM:
            return provider.wait_for_sms(phone.id, timeout)
        else:
            raise ValueError(f"Unknown provider: {phone.provider}")
    
    def _update_stats(self, provider: ProviderType, success: bool):
        """Update provider success statistics"""
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'success_rate': 0.0
            }
        
        stats = self.provider_stats[provider]
        stats['attempts'] += 1
        
        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        stats['success_rate'] = (stats['successes'] / stats['attempts']) * 100
    
    def get_stats(self) -> Dict:
        """Get provider statistics"""
        return self.provider_stats


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_sms_provider(config_file: str = "config/sms_providers.json") -> SMSProviderFactory:
    """Create SMS provider factory from config file"""
    import os
    import json
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "5sim": {
                "api_key": os.environ.get("FIVESIM_API_KEY", "")
            },
            "sms_activate": {
                "api_key": os.environ.get("SMS_ACTIVATE_API_KEY", "")
            },
            "textverified": {
                "api_key": os.environ.get("TEXTVERIFIED_API_KEY", "")
            },
            "onlinesim": {
                "api_key": os.environ.get("ONLINESIM_API_KEY", "")
            },
            "default_provider": "5sim",
            "preferred_countries": ["ye", "sy", "cu", "kp", "ng", "eg"]
        }
        
        # Save default config
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    return SMSProviderFactory(config)


# ============================================================================
# UNIT TESTS
# ============================================================================

async def test_sms_providers():
    """Test SMS providers"""
    logger.info("Testing SMS providers...")
    
    # Create provider with environment variables
    factory = create_sms_provider()
    
    try:
        # Test getting phone from preferred bypass country
        phone = await factory.get_phone_async(CountryCode.YE)
        logger.success(f"Got phone: {phone.number}")
        
        # Wait for SMS (mock for testing)
        # sms = await factory.wait_for_sms_async(phone)
        # logger.success(f"Got SMS: {sms.code}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_sms_providers())