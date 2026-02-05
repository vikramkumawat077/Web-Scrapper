"""
Proxy Pool - Proxy Rotation and Management

Manages multiple proxy sources for reliable scraping.
"""

import random
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx


@dataclass
class Proxy:
    """Proxy server configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    country: Optional[str] = None
    last_used: Optional[datetime] = None
    fail_count: int = 0
    success_count: int = 0
    
    @property
    def url(self) -> str:
        """Get proxy URL"""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.protocol}://{auth}{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.5


class ProxyPool:
    """
    Proxy pool with rotation and health checking.
    
    Features:
    - Multiple proxy sources
    - Automatic rotation
    - Health checking
    - Country targeting
    """
    
    def __init__(self):
        self._proxies: list[Proxy] = []
        self._banned: set[str] = set()
        self._lock = asyncio.Lock()
    
    def add_proxy(self, proxy: Proxy):
        """Add proxy to pool"""
        self._proxies.append(proxy)
    
    def add_proxies(self, proxies: list[Proxy]):
        """Add multiple proxies"""
        self._proxies.extend(proxies)
    
    async def get_proxy(
        self, 
        country: Optional[str] = None,
        protocol: str = "http"
    ) -> Optional[Proxy]:
        """
        Get next available proxy.
        
        Args:
            country: Target country code (optional)
            protocol: Proxy protocol (http, socks5)
        
        Returns:
            Proxy or None if pool is empty
        """
        async with self._lock:
            # Filter available proxies
            available = [
                p for p in self._proxies
                if p.url not in self._banned
                and p.protocol == protocol
                and (country is None or p.country == country)
                and p.fail_count < 5
            ]
            
            if not available:
                return None
            
            # Sort by success rate and pick best
            available.sort(key=lambda p: p.success_rate, reverse=True)
            
            # Use weighted random (favor better proxies)
            if len(available) > 3:
                proxy = random.choice(available[:3])
            else:
                proxy = available[0]
            
            proxy.last_used = datetime.now()
            return proxy
    
    async def mark_success(self, proxy: Proxy):
        """Mark proxy request as successful"""
        async with self._lock:
            proxy.success_count += 1
    
    async def mark_failure(self, proxy: Proxy):
        """Mark proxy request as failed"""
        async with self._lock:
            proxy.fail_count += 1
            
            # Ban if too many failures
            if proxy.fail_count >= 5:
                self._banned.add(proxy.url)
    
    async def check_proxy(self, proxy: Proxy) -> bool:
        """
        Check if proxy is working.
        
        Args:
            proxy: Proxy to check
        
        Returns:
            True if working
        """
        try:
            async with httpx.AsyncClient(
                proxy=proxy.url,
                timeout=10.0
            ) as client:
                response = await client.get("https://httpbin.org/ip")
                return response.status_code == 200
        except:
            return False
    
    async def check_all(self) -> dict:
        """
        Check all proxies and return health report.
        
        Returns:
            Dict with working, failed, banned counts
        """
        working = 0
        failed = 0
        
        for proxy in self._proxies:
            if await self.check_proxy(proxy):
                working += 1
            else:
                failed += 1
        
        return {
            "total": len(self._proxies),
            "working": working,
            "failed": failed,
            "banned": len(self._banned)
        }
    
    def clear_bans(self):
        """Clear ban list"""
        self._banned.clear()
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "total": len(self._proxies),
            "available": len([p for p in self._proxies if p.url not in self._banned]),
            "banned": len(self._banned),
            "avg_success_rate": sum(p.success_rate for p in self._proxies) / len(self._proxies) if self._proxies else 0
        }


class FreeProxyFetcher:
    """Fetch free proxies from public sources"""
    
    SOURCES = [
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    ]
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch(self) -> list[Proxy]:
        """Fetch proxies from all sources"""
        proxies = []
        
        for source in self.SOURCES:
            try:
                response = await self.client.get(source)
                if response.status_code == 200:
                    lines = response.text.strip().split("\n")
                    for line in lines:
                        if ":" in line:
                            parts = line.strip().split(":")
                            if len(parts) == 2:
                                proxies.append(Proxy(
                                    host=parts[0],
                                    port=int(parts[1])
                                ))
            except Exception as e:
                print(f"Failed to fetch from {source}: {e}")
        
        return proxies
    
    async def close(self):
        """Close client"""
        await self.client.aclose()
