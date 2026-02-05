"""
Connection Pool Manager - HTTP Connection Reuse

Manages persistent HTTP connections for maximum speed.
"""

import asyncio
from typing import Optional
import httpx


class ConnectionPoolManager:
    """
    Manages HTTP connection pools for optimal performance.
    
    Features:
    - HTTP/2 multiplexing
    - Keep-alive connections
    - Connection reuse across requests
    - Per-host connection limits
    """
    
    _instance = None
    _client: Optional[httpx.AsyncClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get or create shared HTTP client"""
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                http2=True,
                follow_redirects=True,
                timeout=30.0,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=50,
                    keepalive_expiry=30.0
                )
            )
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close the shared client"""
        if cls._client:
            await cls._client.aclose()
            cls._client = None


class DNSCache:
    """
    DNS caching to avoid repeated lookups.
    
    Features:
    - In-memory DNS cache
    - TTL-based expiration
    - Pre-resolution for known domains
    """
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = ttl_seconds
    
    async def resolve(self, hostname: str) -> Optional[str]:
        """Resolve and cache hostname"""
        import socket
        import time
        
        # Check cache
        if hostname in self._cache:
            ip, timestamp = self._cache[hostname]
            if time.time() - timestamp < self._ttl:
                return ip
        
        # Resolve
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: socket.gethostbyname(hostname)
            )
            self._cache[hostname] = (result, time.time())
            return result
        except:
            return None
    
    async def preload(self, hostnames: list[str]):
        """Pre-resolve multiple hostnames"""
        tasks = [self.resolve(h) for h in hostnames]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def clear(self):
        """Clear the cache"""
        self._cache.clear()


class RequestBatcher:
    """
    Batch and optimize multiple requests.
    
    Features:
    - Request queuing
    - Batch execution
    - Result correlation
    """
    
    def __init__(
        self, 
        batch_size: int = 10,
        batch_delay: float = 0.1
    ):
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self._queue = []
        self._results = {}
    
    async def add(self, url: str) -> str:
        """Add URL to batch queue"""
        self._queue.append(url)
        
        # Process if batch full
        if len(self._queue) >= self.batch_size:
            await self._process_batch()
        
        return url
    
    async def _process_batch(self):
        """Process current batch"""
        if not self._queue:
            return
        
        # Get current batch
        batch = self._queue[:self.batch_size]
        self._queue = self._queue[self.batch_size:]
        
        # Execute in parallel
        client = await ConnectionPoolManager.get_client()
        tasks = [client.get(url) for url in batch]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Store results
        for url, response in zip(batch, responses):
            if isinstance(response, Exception):
                self._results[url] = None
            else:
                self._results[url] = response.text
    
    async def flush(self):
        """Process remaining items in queue"""
        while self._queue:
            await self._process_batch()
    
    def get_result(self, url: str) -> Optional[str]:
        """Get result for URL"""
        return self._results.get(url)
