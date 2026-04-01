#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROXY_MANAGER.PY - v2026.∞                                ║
║                  Residential & Mobile Proxy Mesh Engine                      ║
║                                                                              ║
║  "You are not where you appear to be. You are everywhere and nowhere."      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import json
import aiohttp
import aiofiles
import ipaddress
from typing import List, Dict, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from collections import deque
import hashlib

from loguru import logger
import redis.asyncio as redis


class ProxyType(Enum):
    """Types of proxies with different trust levels"""
    RESIDENTIAL = "residential"  # ISP-assigned, highest trust
    MOBILE = "mobile"  # 4G/5G carrier IP, highest trust
    DATACENTER = "datacenter"  # DC IP, low trust
    RESIDENTIAL_STATIC = "residential_static"  # Static residential ISP
    MOBILE_ROTATING = "mobile_rotating"  # Rotating mobile carrier


class ProxyProtocol(Enum):
    """Supported proxy protocols"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class Proxy:
    """Represents a proxy with health and metadata"""
    
    # Core connection info
    ip: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Proxy type
    proxy_type: ProxyType = ProxyType.RESIDENTIAL
    
    # Geolocation
    country: str = "US"
    city: Optional[str] = None
    isp: Optional[str] = None
    
    # Health metrics
    is_alive: bool = True
    last_checked: datetime = field(default_factory=datetime.utcnow)
    response_time: float = 0.0  # ms
    success_count: int = 0
    fail_count: int = 0
    consecutive_fails: int = 0
    
    # Google-specific
    google_blocked: bool = False
    google_captcha_count: int = 0
    
    # Usage tracking
    last_used: Optional[datetime] = None
    use_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def url(self) -> str:
        """Get proxy URL for Playwright/Selenium"""
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{self.protocol.value}://{auth}{self.ip}:{self.port}"
    
    @property
    def health_score(self) -> float:
        """Calculate health score (0-100)"""
        if not self.is_alive:
            return 0
        
        total_requests = self.success_count + self.fail_count
        if total_requests == 0:
            return 50
        
        success_rate = self.success_count / total_requests
        
        # Response time score (lower is better)
        if self.response_time == 0:
            rt_score = 50
        elif self.response_time < 500:
            rt_score = 100
        elif self.response_time < 1000:
            rt_score = 80
        elif self.response_time < 2000:
            rt_score = 60
        elif self.response_time < 3000:
            rt_score = 40
        elif self.response_time < 5000:
            rt_score = 20
        else:
            rt_score = 10
        
        # Google block penalty
        google_penalty = 0
        if self.google_blocked:
            google_penalty = 100
        elif self.google_captcha_count > 0:
            google_penalty = min(50, self.google_captcha_count * 10)
        
        # Consecutive fails penalty
        fail_penalty = min(50, self.consecutive_fails * 10)
        
        score = (success_rate * 60) + (rt_score * 0.3) - google_penalty - fail_penalty
        return max(0, min(100, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ip': self.ip,
            'port': self.port,
            'protocol': self.protocol.value,
            'username': self.username,
            'password': self.password,
            'proxy_type': self.proxy_type.value,
            'country': self.country,
            'city': self.city,
            'isp': self.isp,
            'is_alive': self.is_alive,
            'last_checked': self.last_checked.isoformat(),
            'response_time': self.response_time,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'consecutive_fails': self.consecutive_fails,
            'google_blocked': self.google_blocked,
            'google_captcha_count': self.google_captcha_count,
            'use_count': self.use_count,
            'health_score': self.health_score,
        }


class ProxyHealthChecker:
    """Advanced proxy health checking with geolocation validation"""
    
    TEST_URLS = [
        'http://httpbin.org/ip',
        'http://ip-api.com/json',
        'http://ipinfo.io/json',
        'https://api.ipify.org?format=json',
    ]
    
    GOOGLE_TEST_URL = 'https://accounts.google.com'
    
    @classmethod
    async def check_proxy(cls, proxy: Proxy, timeout: int = 10) -> Tuple[bool, float, Dict]:
        """Check if proxy is alive and get geolocation data"""
        
        start_time = datetime.utcnow()
        
        try:
            # Test with multiple URLs for reliability
            for test_url in cls.TEST_URLS:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            test_url,
                            proxy=proxy.url,
                            timeout=aiohttp.ClientTimeout(total=timeout),
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Extract IP and geolocation
                                if 'ip' in data:
                                    detected_ip = data['ip']
                                    
                                    # Check if proxy is leaking our real IP
                                    if detected_ip == proxy.ip:
                                        # Get geolocation if available
                                        geo_data = {}
                                        if 'country' in data:
                                            geo_data['country'] = data['country']
                                        if 'city' in data:
                                            geo_data['city'] = data['city']
                                        if 'isp' in data:
                                            geo_data['isp'] = data['isp']
                                        
                                        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                                        return True, response_time, geo_data
                
                except Exception:
                    continue
            
            return False, 0, {}
            
        except Exception as e:
            logger.debug(f"Proxy check failed for {proxy.ip}: {e}")
            return False, 0, {}
    
    @classmethod
    async def check_google_access(cls, proxy: Proxy) -> Tuple[bool, bool]:
        """Check if proxy can access Google without blocking/captcha"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    cls.GOOGLE_TEST_URL,
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=15),
                    allow_redirects=True
                ) as response:
                    
                    html = await response.text()
                    
                    # Check for Google block
                    if 'unusual traffic' in html.lower():
                        return True, True  # Blocked
                    
                    # Check for captcha
                    if 'recaptcha' in html.lower() or 'captcha' in html.lower():
                        return True, False  # Captcha
                    
                    return False, False  # Access OK
                    
        except Exception:
            return False, False  # Assume not blocked, just failed


class ResidentialProxyFetcher:
    """Fetch residential proxies from various providers"""
    
    PROVIDERS = {
        '5socks': {
            'api_url': 'https://api.5socks.net/proxy/list',
            'api_key_required': True,
        },
        'proxyscrape': {
            'api_url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'api_key_required': False,
        },
        'geonode': {
            'api_url': 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps',
            'api_key_required': False,
        },
        'proxybonanza': {
            'api_url': 'https://api.proxybonanza.com/v1/proxylist',
            'api_key_required': True,
        }
    }
    
    @classmethod
    async def fetch_from_proxyscrape(cls) -> List[Proxy]:
        """Fetch proxies from proxyscrape.com"""
        proxies = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                    timeout=10
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        
                        for line in text.strip().split('\n'):
                            try:
                                ip, port = line.strip().split(':')
                                proxy = Proxy(
                                    ip=ip,
                                    port=int(port),
                                    protocol=ProxyProtocol.HTTP,
                                    proxy_type=ProxyType.DATACENTER,
                                    country='US',  # Default
                                )
                                proxies.append(proxy)
                            except:
                                continue
        except Exception as e:
            logger.error(f"Failed to fetch from proxyscrape: {e}")
        
        return proxies
    
    @classmethod
    async def fetch_from_geonode(cls) -> List[Proxy]:
        """Fetch proxies from geonode.com"""
        proxies = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps',
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('data', []):
                            try:
                                proxy = Proxy(
                                    ip=item['ip'],
                                    port=int(item['port']),
                                    protocol=ProxyProtocol.HTTP if 'http' in item.get('protocols', []) else ProxyProtocol.HTTPS,
                                    proxy_type=ProxyType.DATACENTER,
                                    country=item.get('country', 'US'),
                                    city=item.get('city', ''),
                                    isp=item.get('isp', ''),
                                )
                                proxies.append(proxy)
                            except:
                                continue
        except Exception as e:
            logger.error(f"Failed to fetch from geonode: {e}")
        
        return proxies


class MobileProxyFetcher:
    """Fetch mobile (4G/5G) proxies from premium providers"""
    
    @classmethod
    async def fetch_from_5sim(cls, api_key: str) -> List[Proxy]:
        """Fetch mobile proxies from 5sim.net"""
        proxies = []
        
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    'https://5sim.net/v1/user/proxy',
                    timeout=15
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data:
                            try:
                                proxy = Proxy(
                                    ip=item['ip'],
                                    port=int(item['port']),
                                    protocol=ProxyProtocol.HTTP,
                                    username=item.get('username'),
                                    password=item.get('password'),
                                    proxy_type=ProxyType.MOBILE,
                                    country=item.get('country', 'US'),
                                    isp='Mobile Carrier',
                                )
                                proxies.append(proxy)
                            except:
                                continue
        except Exception as e:
            logger.error(f"Failed to fetch from 5sim: {e}")
        
        return proxies
    
    @classmethod
    async def fetch_from_sms_activate(cls, api_key: str) -> List[Proxy]:
        """Fetch proxies from sms-activate.ru"""
        # Similar implementation for sms-activate
        return []


class IPv6Rotator:
    """Generate and rotate IPv6 addresses from /64 subnet"""
    
    def __init__(self, subnet: str):
        """
        Initialize with IPv6 subnet (e.g., '2001:db8::/64')
        """
        self.subnet = ipaddress.IPv6Network(subnet)
        self.generated_ips: Set[str] = set()
    
    def generate_ip(self) -> str:
        """Generate a unique IPv6 address from subnet"""
        max_attempts = 1000
        
        for _ in range(max_attempts):
            # Generate random host part
            host = random.randint(0, 2**64 - 1)
            ip = self.subnet[host]
            ip_str = str(ip)
            
            if ip_str not in self.generated_ips:
                self.generated_ips.add(ip_str)
                return ip_str
        
        # If we've used many IPs, start reusing
        return str(random.choice(list(self.generated_ips)))
    
    def create_proxy(self, base_proxy: Proxy, ipv6: str) -> Proxy:
        """Create a new proxy with IPv6 address"""
        return Proxy(
            ip=ipv6,
            port=base_proxy.port,
            protocol=base_proxy.protocol,
            username=base_proxy.username,
            password=base_proxy.password,
            proxy_type=ProxyType.RESIDENTIAL,
            country=base_proxy.country,
            isp=base_proxy.isp,
        )


class ProxyAnonymizer:
    """Anonymize proxy usage to prevent fingerprinting"""
    
    @staticmethod
    def randomize_user_agent() -> str:
        """Generate random realistic user agent"""
        browsers = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:122.0) Gecko/20100101 Firefox/122.0',
        ]
        return random.choice(browsers)
    
    @staticmethod
    def randomize_headers() -> Dict[str, str]:
        """Generate random HTTP headers"""
        return {
            'User-Agent': ProxyAnonymizer.randomize_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'en-CA,en;q=0.7']),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': str(random.choice(['1', '0'])),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }


class ProxyManager:
    """
    Advanced proxy manager with health checking, rotation, and scoring
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis: Optional[redis.Redis] = None
        if redis_url:
            self.redis = redis.from_url(redis_url, decode_responses=True)
        
        self.proxies: List[Proxy] = []
        self.blacklist: Set[str] = set()
        self.active_proxies: Dict[str, Proxy] = {}
        
        self.health_checker = ProxyHealthChecker()
        self.anonymizer = ProxyAnonymizer()
        self.ipv6_rotator: Optional[IPv6Rotator] = None
        
        # Proxy pools by type
        self.residential_pool: List[Proxy] = []
        self.mobile_pool: List[Proxy] = []
        self.datacenter_pool: List[Proxy] = []
        
        # Configuration
        self.max_consecutive_fails = 3
        self.min_health_score = 60
        self.proxy_refresh_interval = 300  # 5 minutes
        self.google_block_penalty = 100
        
        # Stats
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def initialize(self):
        """Initialize proxy manager"""
        logger.info("🚀 Initializing Proxy Manager")
        
        # Try to load from Redis cache
        if self.redis:
            await self._load_from_cache()
        
        # Initial proxy fetch
        await self.refresh_proxies()
        
        logger.success(f"✅ Proxy Manager initialized with {len(self.proxies)} proxies")
    
    async def _load_from_cache(self):
        """Load proxies from Redis cache"""
        try:
            cached_proxies = await self.redis.get('proxies:all')
            if cached_proxies:
                proxy_data = json.loads(cached_proxies)
                self.proxies = [self._dict_to_proxy(p) for p in proxy_data]
                logger.info(f"📦 Loaded {len(self.proxies)} proxies from cache")
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
    
    async def _save_to_cache(self):
        """Save proxies to Redis cache"""
        if not self.redis:
            return
        
        try:
            proxy_data = [p.to_dict() for p in self.proxies]
            await self.redis.setex('proxies:all', 3600, json.dumps(proxy_data))
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")
    
    def _dict_to_proxy(self, data: Dict) -> Proxy:
        """Convert dictionary to Proxy object"""
        return Proxy(
            ip=data['ip'],
            port=data['port'],
            protocol=ProxyProtocol(data.get('protocol', 'http')),
            username=data.get('username'),
            password=data.get('password'),
            proxy_type=ProxyType(data.get('proxy_type', 'residential')),
            country=data.get('country', 'US'),
            city=data.get('city'),
            isp=data.get('isp'),
            is_alive=data.get('is_alive', True),
            last_checked=datetime.fromisoformat(data['last_checked']) if 'last_checked' in data else datetime.utcnow(),
            response_time=data.get('response_time', 0),
            success_count=data.get('success_count', 0),
            fail_count=data.get('fail_count', 0),
            consecutive_fails=data.get('consecutive_fails', 0),
            google_blocked=data.get('google_blocked', False),
            google_captcha_count=data.get('google_captcha_count', 0),
            use_count=data.get('use_count', 0),
        )
    
    async def refresh_proxies(self):
        """Refresh proxy lists from all providers"""
        logger.info("🔄 Refreshing proxy lists")
        
        new_proxies = []
        
        # Fetch from free providers
        new_proxies.extend(await ResidentialProxyFetcher.fetch_from_proxyscrape())
        new_proxies.extend(await ResidentialProxyFetcher.fetch_from_geonode())
        
        # Filter and deduplicate
        seen_ips = {p.ip for p in self.proxies}
        unique_proxies = []
        
        for proxy in new_proxies:
            if proxy.ip not in seen_ips:
                unique_proxies.append(proxy)
                seen_ips.add(proxy.ip)
        
        # Add to proxy list
        self.proxies.extend(unique_proxies)
        
        # Check health of new proxies
        await self.check_all_proxies(unique_proxies)
        
        # Sort into pools
        await self._sort_into_pools()
        
        # Save to cache
        await self._save_to_cache()
        
        logger.info(f"✅ Added {len(unique_proxies)} new proxies, total: {len(self.proxies)}")
    
    async def _sort_into_pools(self):
        """Sort proxies into type-specific pools"""
        self.residential_pool = []
        self.mobile_pool = []
        self.datacenter_pool = []
        
        for proxy in self.proxies:
            if not proxy.is_alive or proxy.google_blocked:
                continue
            
            if proxy.health_score < self.min_health_score:
                continue
            
            if proxy.proxy_type == ProxyType.RESIDENTIAL:
                self.residential_pool.append(proxy)
            elif proxy.proxy_type == ProxyType.MOBILE:
                self.mobile_pool.append(proxy)
            else:
                self.datacenter_pool.append(proxy)
        
        # Sort by health score
        self.residential_pool.sort(key=lambda x: x.health_score, reverse=True)
        self.mobile_pool.sort(key=lambda x: x.health_score, reverse=True)
        self.datacenter_pool.sort(key=lambda x: x.health_score, reverse=True)
        
        logger.info(f"📊 Proxy pools - Residential: {len(self.residential_pool)}, Mobile: {len(self.mobile_pool)}, Datacenter: {len(self.datacenter_pool)}")
    
    async def check_all_proxies(self, proxies: Optional[List[Proxy]] = None, concurrency: int = 20):
        """Check health of all or specified proxies"""
        to_check = proxies or self.proxies
        
        if not to_check:
            return
        
        logger.info(f"🔍 Checking health of {len(to_check)} proxies")
        
        # Limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def check_with_semaphore(proxy: Proxy):
            async with semaphore:
                is_alive, response_time, geo_data = await self.health_checker.check_proxy(proxy)
                
                if is_alive:
                    proxy.is_alive = True
                    proxy.response_time = response_time
                    proxy.last_checked = datetime.utcnow()
                    proxy.consecutive_fails = 0
                    
                    # Update geolocation
                    if geo_data:
                        proxy.country = geo_data.get('country', proxy.country)
                        proxy.city = geo_data.get('city', proxy.city)
                        proxy.isp = geo_data.get('isp', proxy.isp)
                    
                    # Check Google access
                    is_blocked, has_captcha = await self.health_checker.check_google_access(proxy)
                    proxy.google_blocked = is_blocked
                    
                    if has_captcha:
                        proxy.google_captcha_count += 1
                    else:
                        proxy.google_captcha_count = max(0, proxy.google_captcha_count - 1)
                else:
                    proxy.consecutive_fails += 1
                    
                    if proxy.consecutive_fails >= self.max_consecutive_fails:
                        proxy.is_alive = False
        
        # Run checks concurrently
        await asyncio.gather(*[check_with_semaphore(p) for p in to_check])
        
        # Count alive proxies
        alive_count = sum(1 for p in self.proxies if p.is_alive and not p.google_blocked)
        logger.info(f"✅ Health check complete: {alive_count}/{len(self.proxies)} proxies alive")
    
    async def get_proxy(
        self,
        preferred_type: Optional[ProxyType] = None,
        country: Optional[str] = None,
        min_score: int = 70
    ) -> Optional[Proxy]:
        """Get the best available proxy based on criteria"""
        
        # Select appropriate pool
        if preferred_type == ProxyType.RESIDENTIAL:
            pool = self.residential_pool
        elif preferred_type == ProxyType.MOBILE:
            pool = self.mobile_pool
        elif preferred_type == ProxyType.DATACENTER:
            pool = self.datacenter_pool
        else:
            # Combine all pools, prioritize residential > mobile > datacenter
            pool = self.residential_pool + self.mobile_pool + self.datacenter_pool
        
        # Filter by country
        if country:
            pool = [p for p in pool if p.country == country]
        
        # Filter by minimum health score
        pool = [p for p in pool if p.health_score >= min_score]
        
        if not pool:
            return None
        
        # Weighted random selection based on health score
        scores = [p.health_score for p in pool]
        total_score = sum(scores)
        
        if total_score == 0:
            selected = random.choice(pool)
        else:
            weights = [s / total_score for s in scores]
            selected = random.choices(pool, weights=weights, k=1)[0]
        
        # Update usage stats
        selected.last_used = datetime.utcnow()
        selected.use_count += 1
        
        return selected
    
    async def get_proxy_for_google(self) -> Optional[Proxy]:
        """Get the best proxy specifically for Google accounts"""
        
        # Try residential first (highest trust)
        proxy = await self.get_proxy(
            preferred_type=ProxyType.RESIDENTIAL,
            min_score=80
        )
        
        if not proxy:
            # Try mobile
            proxy = await self.get_proxy(
                preferred_type=ProxyType.MOBILE,
                min_score=75
            )
        
        if not proxy:
            # Try any residential
            proxy = await self.get_proxy(
                preferred_type=ProxyType.RESIDENTIAL,
                min_score=60
            )
        
        return proxy
    
    async def report_success(self, proxy: Proxy):
        """Report successful proxy usage"""
        proxy.success_count += 1
        proxy.consecutive_fails = 0
        self.successful_requests += 1
        self.total_requests += 1
        
        # Update health score in pool
        await self._sort_into_pools()
    
    async def report_failure(self, proxy: Proxy, reason: str = ""):
        """Report failed proxy usage"""
        proxy.fail_count += 1
        proxy.consecutive_fails += 1
        self.failed_requests += 1
        self.total_requests += 1
        
        # Check for Google blocks
        if 'captcha' in reason.lower() or 'block' in reason.lower():
            proxy.google_captcha_count += 1
            
            if 'block' in reason.lower() and proxy.google_captcha_count >= 3:
                proxy.google_blocked = True
        
        # Mark as dead if too many failures
        if proxy.consecutive_fails >= self.max_consecutive_fails:
            proxy.is_alive = False
            logger.warning(f"⚠️ Proxy {proxy.ip} marked as dead after {proxy.consecutive_fails} failures")
        
        # Update pools
        await self._sort_into_pools()
    
    async def blacklist_proxy(self, proxy: Proxy, reason: str = ""):
        """Permanently blacklist a proxy"""
        self.blacklist.add(proxy.ip)
        
        if proxy in self.proxies:
            self.proxies.remove(proxy)
        
        if proxy in self.residential_pool:
            self.residential_pool.remove(proxy)
        
        if proxy in self.mobile_pool:
            self.mobile_pool.remove(proxy)
        
        if proxy in self.datacenter_pool:
            self.datacenter_pool.remove(proxy)
        
        logger.warning(f"⛔ Proxy {proxy.ip} blacklisted: {reason}")
    
    def enable_ipv6_rotation(self, subnet: str):
        """Enable IPv6 rotation for infinite IPs"""
        self.ipv6_rotator = IPv6Rotator(subnet)
        logger.info(f"🌐 IPv6 rotation enabled with subnet {subnet}")
    
    async def get_ipv6_proxy(self, base_proxy: Proxy) -> Proxy:
        """Get a proxy with rotated IPv6 address"""
        if not self.ipv6_rotator:
            return base_proxy
        
        ipv6 = self.ipv6_rotator.generate_ip()
        return self.ipv6_rotator.create_proxy(base_proxy, ipv6)
    
    async def rotate_proxies(self, interval_minutes: int = 5):
        """Background task to rotate and refresh proxies"""
        while True:
            await asyncio.sleep(interval_minutes * 60)
            
            # Refresh proxy list
            await self.refresh_proxies()
            
            # Recheck health of all proxies
            await self.check_all_proxies()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy manager statistics"""
        return {
            'total_proxies': len(self.proxies),
            'alive_proxies': sum(1 for p in self.proxies if p.is_alive),
            'residential_proxies': len(self.residential_pool),
            'mobile_proxies': len(self.mobile_pool),
            'datacenter_proxies': len(self.datacenter_pool),
            'blacklisted': len(self.blacklist),
            'total_requests': self.total_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            'average_response_time': sum(p.response_time for p in self.proxies if p.response_time > 0) / max(1, len([p for p in self.proxies if p.response_time > 0])),
        }