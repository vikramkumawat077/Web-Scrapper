"""
Cache - Redis Caching Layer

Caches scraped content to avoid duplicate requests.
"""

from typing import Optional
import json
import hashlib


class Cache:
    """
    Redis-based caching.
    
    Features:
    - URL-based cache keys
    - Configurable TTL
    - JSON serialization
    """
    
    def __init__(self, ttl_hours: int = 24):
        self.ttl = ttl_hours * 3600
        self._redis = None
    
    async def _get_redis(self):
        """Lazy Redis connection"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                from src.config import config
                self._redis = await redis.from_url(config.database.redis_url)
            except Exception as e:
                print(f"Redis connection failed: {e}")
                return None
        return self._redis
    
    def _url_to_key(self, url: str) -> str:
        """Convert URL to cache key"""
        return f"cache:{hashlib.md5(url.encode()).hexdigest()}"
    
    async def get(self, url: str) -> Optional[str]:
        """Get cached content for URL"""
        redis = await self._get_redis()
        if not redis:
            return None
        
        key = self._url_to_key(url)
        try:
            data = await redis.get(key)
            return data.decode() if data else None
        except:
            return None
    
    async def set(self, url: str, content: str) -> bool:
        """Cache content for URL"""
        redis = await self._get_redis()
        if not redis:
            return False
        
        key = self._url_to_key(url)
        try:
            await redis.setex(key, self.ttl, content)
            return True
        except:
            return False
    
    async def exists(self, url: str) -> bool:
        """Check if URL is cached"""
        redis = await self._get_redis()
        if not redis:
            return False
        
        key = self._url_to_key(url)
        try:
            return await redis.exists(key) > 0
        except:
            return False
    
    async def delete(self, url: str) -> bool:
        """Delete cached content"""
        redis = await self._get_redis()
        if not redis:
            return False
        
        key = self._url_to_key(url)
        try:
            await redis.delete(key)
            return True
        except:
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
