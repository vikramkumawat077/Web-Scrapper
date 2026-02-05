"""
Stealth Module - Human-Like Behavior

Adds human-like behavior to avoid bot detection.
"""

import asyncio
import random
from typing import Optional


class StealthBehavior:
    """
    Human-like behavior patterns for bot detection evasion.
    
    Features:
    - Random delays
    - Mouse movement simulation
    - Scroll patterns
    - Click variation
    """
    
    @staticmethod
    async def random_delay(
        min_seconds: float = 0.5,
        max_seconds: float = 2.0
    ):
        """Add random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    @staticmethod
    def get_random_viewport() -> dict:
        """Get random realistic viewport size"""
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1280, "height": 720},
        ]
        return random.choice(viewports)
    
    @staticmethod
    def get_random_user_agent(device: str = "desktop") -> str:
        """Get random user agent string"""
        desktop_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        
        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
        ]
        
        if device == "mobile":
            return random.choice(mobile_agents)
        return random.choice(desktop_agents)
    
    @staticmethod
    async def simulate_human_scroll(page, scroll_count: int = 3):
        """Simulate human-like scrolling in Playwright page"""
        for _ in range(scroll_count):
            scroll_amount = random.randint(200, 500)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.3, 1.0))
    
    @staticmethod
    async def simulate_mouse_movement(page, duration: float = 1.0):
        """Simulate random mouse movement in Playwright page"""
        steps = int(duration * 10)
        x, y = random.randint(100, 500), random.randint(100, 400)
        
        for _ in range(steps):
            x += random.randint(-50, 50)
            y += random.randint(-30, 30)
            x = max(0, min(x, 1920))
            y = max(0, min(y, 1080))
            await page.mouse.move(x, y)
            await asyncio.sleep(0.1)
    
    @staticmethod
    def get_request_headers(referer: Optional[str] = None) -> dict:
        """Get realistic request headers"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
        }
        
        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "cross-site"
        
        return headers
    
    @staticmethod
    def get_cookie_consent_payload() -> dict:
        """Get typical cookie consent values"""
        return {
            "cookieConsent": "accepted",
            "gdprConsent": "true",
            "analyticsConsent": "false"
        }


class RateLimiter:
    """Rate limiting with exponential backoff"""
    
    def __init__(
        self, 
        requests_per_minute: int = 30,
        burst_limit: int = 5
    ):
        self.rpm = requests_per_minute
        self.burst = burst_limit
        self._tokens = burst_limit
        self._last_refill = asyncio.get_event_loop().time()
    
    async def acquire(self):
        """Acquire rate limit token"""
        now = asyncio.get_event_loop().time()
        
        # Refill tokens
        elapsed = now - self._last_refill
        refill = elapsed * (self.rpm / 60)
        self._tokens = min(self.burst, self._tokens + refill)
        self._last_refill = now
        
        # Wait if no tokens
        if self._tokens < 1:
            wait_time = (1 - self._tokens) / (self.rpm / 60)
            await asyncio.sleep(wait_time)
            self._tokens = 1
        
        self._tokens -= 1
    
    async def backoff(self, attempt: int):
        """Exponential backoff with jitter"""
        base_delay = 2 ** attempt
        jitter = random.uniform(0, 1)
        delay = min(base_delay + jitter, 60)  # Max 60 seconds
        await asyncio.sleep(delay)
