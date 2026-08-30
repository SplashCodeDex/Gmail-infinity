import os
import time
import random
import logging
from collections import defaultdict, deque
from typing import Dict, Optional
import requests
from config.settings import Config

logger = logging.getLogger('gmail_creator_proxy')


class ProxyManager:
    def __init__(self):
        self._proxies = []
        self._current_index = 0
        self._health = {}
        self._scores = {}
        self.proxy_history = defaultdict(lambda: {'successes': 0, 'failures': 0, 'last_used': 0.0, 'latency_ms': deque(maxlen=10)})
        self._load_proxies()

    def _load_proxies(self):
        proxy_file = Config.PROXY_FILE
        if not os.path.exists(proxy_file):
            logger.warning(f"Proxy file not found: {proxy_file}")
            return
        with open(proxy_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self._proxies.append(line)
                    self._health[line] = True
                    self._scores[line] = 50
        if self._proxies:
            logger.info(f"Loaded {len(self._proxies)} proxies")

    @property
    def count(self):
        return len(self._proxies)

    @property
    def healthy_count(self):
        return sum(1 for p in self._proxies if self._health.get(p, True))

    def get_all_proxies(self):
        return list(self._proxies)

    def add_proxies(self, proxies_list, replace=False):
        """Add new proxies to the manager with validation."""
        if replace:
            self._proxies = []
            self._health = {}
            self._scores = {}

        added_count = 0
        for p in proxies_list:
            if not p:
                continue
            p = p.strip()
            if not p or p.startswith('#'):
                continue
            if self.parse(p) and p not in self._proxies:
                self._proxies.append(p)
                self._health[p] = True
                self._scores[p] = 50
                added_count += 1

        self.save_to_disk()
        return added_count

    def clear_proxies(self):
        """Clear all proxies from memory and disk."""
        self._proxies = []
        self._health = {}
        self._scores = {}
        self.save_to_disk()

    def save_to_disk(self):
        """Save current proxy list to Config.PROXY_FILE."""
        try:
            proxy_file = Config.PROXY_FILE
            os.makedirs(os.path.dirname(proxy_file), exist_ok=True)
            with open(proxy_file, "w", encoding="utf-8") as f:
                for p in self._proxies:
                    f.write(f"{p}\n")
            logger.info(f"Saved {len(self._proxies)} proxies to {proxy_file}")
        except Exception as e:
            logger.error(f"Failed to save proxies to disk: {e}")

    def get_random(self):
        healthy = [p for p in self._proxies if self._health.get(p, True)]
        if not healthy:
            healthy = self._proxies
        if not healthy:
            return None
        return random.choice(healthy)

    def get_next(self):
        if not self._proxies:
            return None
        healthy = [p for p in self._proxies if self._health.get(p, True)]
        if not healthy:
            healthy = self._proxies
        proxy = healthy[self._current_index % len(healthy)]
        self._current_index += 1
        return proxy

    def get_best(self):
        if not self._proxies:
            return None
        healthy = [p for p in self._proxies if self._health.get(p, True)]
        if not healthy:
            healthy = self._proxies
        return max(healthy, key=lambda p: self._scores.get(p, 50))

    def mark_success(self, proxy):
        if proxy in self._scores:
            self._scores[proxy] = min(100, self._scores[proxy] + 10)
            self._health[proxy] = True
        self.proxy_history[proxy]['successes'] += 1
        self.proxy_history[proxy]['last_used'] = time.time()

    def mark_failure(self, proxy, fatal=False):
        if proxy in self._scores:
            self._scores[proxy] = max(0, self._scores[proxy] - (30 if fatal else 10))
            if self._scores[proxy] <= 10:
                self._health[proxy] = False
                logger.warning(f"Proxy marked unhealthy: {proxy}")
        self.proxy_history[proxy]['failures'] += 1
        self.proxy_history[proxy]['last_used'] = time.time()

    def record_result(self, proxy: str, success: bool, latency_ms: Optional[float] = None):
        """Single bookkeeping entry point for creation outcomes."""
        if not proxy:
            return

        history = self.proxy_history[proxy]
        if success:
            history['successes'] += 1
            if proxy in self._scores:
                self._scores[proxy] = min(100, self._scores[proxy] + 10)
                self._health[proxy] = True
        else:
            history['failures'] += 1
            if proxy in self._scores:
                self._scores[proxy] = max(0, self._scores[proxy] - 10)
                if self._scores[proxy] <= 10:
                    self._health[proxy] = False

        history['last_used'] = time.time()
        if latency_ms is not None and latency_ms > 0:
            history['latency_ms'].append(latency_ms)

    def calculate_proxy_score(self, proxy: str) -> float:
        """Calculate proxy reliability score using composite metric (success 60%, speed 20%, freshness 20%)."""
        if not proxy:
            return 0.5

        history = self.proxy_history[proxy]
        total = history['successes'] + history['failures']

        if total == 0:
            return 0.5  # Neutral for untested proxies

        # Success rate component (60%)
        success_rate = history['successes'] / total

        # Speed component (20%) - normalized in milliseconds (neutral 0.5 if unknown)
        if history['latency_ms']:
            avg_ms = sum(history['latency_ms']) / len(history['latency_ms'])
            speed_score = max(0.0, 1.0 - (avg_ms / 3000.0))
        else:
            speed_score = 0.5

        # Freshness component (20%) - penalize old proxies
        time_since_use = time.time() - history['last_used'] if history['last_used'] > 0 else 0
        freshness_score = max(0.0, 1.0 - (time_since_use / 3600.0))

        return (success_rate * 0.6) + (speed_score * 0.2) + (freshness_score * 0.2)

    def select_smart(self) -> Optional[str]:
        """Select best proxy using epsilon-greedy ML scoring (85% exploitation, 15% exploration)."""
        if not self._proxies:
            return None

        # Calculate scores
        scored = [(p, self.calculate_proxy_score(p)) for p in self._proxies]
        scored.sort(key=lambda x: x[1], reverse=True)

        if random.random() < 0.85 and scored:
            return scored[0][0]
        return random.choice(self._proxies)

    def get_intelligence_stats(self) -> Dict:
        """Get comprehensive proxy statistics for export / insights."""
        stats = {}
        for proxy, history in self.proxy_history.items():
            total = history['successes'] + history['failures']
            avg_lat = sum(history['latency_ms']) / len(history['latency_ms']) if history['latency_ms'] else 0.0
            stats[proxy] = {
                'score': self.calculate_proxy_score(proxy),
                'success_rate': (history['successes'] / total * 100) if total > 0 else 0.0,
                'total_uses': total,
                'avg_response_time': avg_lat / 1000.0 if avg_lat else 0.0,
                'avg_latency_ms': avg_lat,
            }
        return stats

    def check_health(self, proxy, timeout=10):
        parsed = self.parse(proxy)
        if not parsed:
            return False
        try:
            proxies_dict = {}
            if parsed["user"]:
                proxy_url = f"http://{parsed['user']}:{parsed['pass']}@{parsed['host']}:{parsed['port']}"
            else:
                proxy_url = f"http://{parsed['host']}:{parsed['port']}"
            proxies_dict = {"http": proxy_url, "https": proxy_url}
            start_t = time.time()
            resp = requests.get("https://httpbin.org/ip", proxies=proxies_dict, timeout=timeout)
            if resp.status_code == 200:
                elapsed_ms = (time.time() - start_t) * 1000
                self._health[proxy] = True
                self.proxy_history[proxy]['latency_ms'].append(elapsed_ms)
                return True
        except Exception as e:
            logger.debug(f"Proxy health check failed for {proxy}: {e}")
        self._health[proxy] = False
        return False

    def check_all_health(self):
        return self.check_all_health_detailed()

    def check_all_health_detailed(self, max_workers=10, timeout=6):
        import concurrent.futures
        results = {"total": len(self._proxies), "healthy": 0, "unhealthy": 0, "proxies": []}
        if not self._proxies:
            return results

        def _test_single(proxy):
            start = time.time()
            healthy = self.check_health(proxy, timeout=timeout)
            latency = round((time.time() - start) * 1000, 1) if healthy else None
            return {
                "proxy": proxy,
                "healthy": healthy,
                "latency_ms": latency,
                "score": self._scores.get(proxy, 50)
            }

        worker_count = min(len(self._proxies), max_workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(worker_count, 1)) as ex:
            futures = [ex.submit(_test_single, p) for p in self._proxies]
            for f in concurrent.futures.as_completed(futures):
                try:
                    res = f.result()
                    results["proxies"].append(res)
                    if res["healthy"]:
                        results["healthy"] += 1
                    else:
                        results["unhealthy"] += 1
                except Exception:
                    pass

        # Sort proxies with healthy/lowest latency first
        results["proxies"].sort(key=lambda x: (not x["healthy"], x["latency_ms"] or 99999))
        return results

    def get_ip_info(self, proxy=None):
        try:
            proxies_dict = {}
            if proxy:
                parsed = self.parse(proxy)
                if parsed:
                    if parsed["user"]:
                        url = f"http://{parsed['user']}:{parsed['pass']}@{parsed['host']}:{parsed['port']}"
                    else:
                        url = f"http://{parsed['host']}:{parsed['port']}"
                    proxies_dict = {"http": url, "https": url}

            ip_resp = requests.get("https://api.ipify.org?format=json", proxies=proxies_dict, timeout=10)
            ip = ip_resp.json().get("ip", "Unknown")

            info_resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            info = info_resp.json()

            is_datacenter = "hosting" in str(info.get("org", "")).lower()
            return {
                "ip": ip,
                "city": info.get("city", "N/A"),
                "country": info.get("country", "N/A"),
                "org": info.get("org", "N/A"),
                "is_datacenter": is_datacenter,
            }
        except Exception as e:
            logger.warning(f"IP info check failed: {e}")
            return None

    def rotate_mobile_ip(self):
        url = getattr(Config, 'MOBILE_PROXY_IP_CHANGE_URL', '')
        if not url:
            return False
        try:
            logger.info("Rotating mobile proxy IP...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                wait_time = getattr(Config, 'PROXY_CHANGE_WAIT_TIME', 10)
                logger.info(f"IP changed. Waiting {wait_time}s for propagation...")
                time.sleep(wait_time)
                return True
            logger.warning(f"IP rotation returned status {resp.status_code}")
        except Exception as e:
            logger.error(f"Mobile IP rotation failed: {e}")
        return False

    @staticmethod
    def parse(proxy_string):
        """Parse a proxy string into its components.

        Supported formats:
            host:port
            host:port:user:pass            (legacy)
            user:pass@host:port
            protocol://host:port
            protocol://user:pass@host:port

        Returns {"host", "port", "user", "pass", "protocol"} or None.
        """
        if not proxy_string:
            return None

        s = proxy_string.strip()

        # Split off an optional scheme (http, https, socks5, ...)
        protocol = "http"
        if "://" in s:
            scheme, s = s.split("://", 1)
            scheme = scheme.lower()
            if scheme in ("http", "https", "socks4", "socks5", "socks5h"):
                protocol = scheme
            else:
                return None

        # Split off optional user:pass@ credentials
        user = pwd = None
        if "@" in s:
            creds, s = s.rsplit("@", 1)
            if ":" in creds:
                user, pwd = creds.split(":", 1)
            else:
                user, pwd = creds, None

        # Remaining part must be host:port (or legacy host:port:user:pass)
        parts = s.split(":")
        if len(parts) == 2:
            host, port = parts
        elif len(parts) == 4 and user is None:
            host, port, user, pwd = parts
        else:
            return None

        try:
            port = int(port)
        except (TypeError, ValueError):
            return None
        if not (0 < port < 65536) or not host:
            return None

        return {"host": host, "port": port, "user": user, "pass": pwd, "protocol": protocol}

    @staticmethod
    def format_for_playwright(proxy_string):
        parsed = ProxyManager.parse(proxy_string)
        if not parsed:
            return None
        result = {"server": f"{parsed['protocol']}://{parsed['host']}:{parsed['port']}"}
        if parsed["user"]:
            result["username"] = parsed["user"]
            result["password"] = parsed["pass"]
        return result

    def get_stats(self):
        return {
            "total": len(self._proxies),
            "healthy": self.healthy_count,
            "unhealthy": len(self._proxies) - self.healthy_count,
            "scores": {p: self._scores.get(p, 0) for p in self._proxies[:10]},
        }


proxy_manager = ProxyManager()
