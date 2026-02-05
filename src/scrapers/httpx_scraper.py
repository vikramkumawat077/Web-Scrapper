"""
HTTPX Scraper - Fast Async HTTP Scraping

The fastest scraping engine, uses HTTP/2 multiplexing.
Best for unprotected or lightly protected sites.
"""

import asyncio
import httpx
from typing import Optional
import random


class HttpxScraper:
    """
    High-performance async HTTP scraper.
    
    Features:
    - HTTP/2 multiplexing
    - Connection pooling
    - User agent rotation
    - Automatic retries
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    
    def __init__(self, max_connections: int = 100):
        self.client = httpx.AsyncClient(
            http2=True,
            follow_redirects=True,
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=50
            )
        )
    
    async def scrape(
        self, 
        url: str, 
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None
    ) -> str:
        """
        Scrape a URL and return HTML content.
        
        Args:
            url: URL to scrape
            headers: Optional custom headers
            cookies: Optional cookies
        
        Returns:
            HTML content
        """
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        response = await self.client.get(
            url,
            headers=request_headers,
            cookies=cookies
        )
        response.raise_for_status()
        
        return response.text
    
    async def scrape_many(self, urls: list[str]) -> list[dict]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
        
        Returns:
            List of results with url, content, and error
        """
        tasks = [self.scrape(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for url, response in zip(urls, responses):
            if isinstance(response, Exception):
                results.append({"url": url, "error": str(response)})
            else:
                results.append({"url": url, "content": response})
        
        return results
    
    def _get_headers(self) -> dict:
        """Get request headers with random user agent"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
