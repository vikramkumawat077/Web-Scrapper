"""
curl_cffi Scraper - TLS Fingerprint Impersonation

Bypasses TLS-based bot detection by impersonating real browser fingerprints.
"""

import random
from typing import Optional


class CurlCffiScraper:
    """
    TLS fingerprint impersonation scraper.
    
    Uses curl_cffi to impersonate real browser TLS fingerprints,
    bypassing JA3-based detection used by Cloudflare, Akamai, etc.
    """
    
    BROWSER_PROFILES = [
        "chrome120",
        "chrome119", 
        "safari17_0",
        "edge120",
        "firefox120",
    ]
    
    def __init__(self):
        self.current_profile_idx = 0
    
    async def scrape(
        self, 
        url: str,
        impersonate: Optional[str] = None
    ) -> str:
        """
        Scrape with browser TLS impersonation.
        
        Args:
            url: URL to scrape
            impersonate: Browser to impersonate (e.g., "chrome120")
        
        Returns:
            HTML content
        """
        try:
            from curl_cffi.requests import AsyncSession
        except ImportError:
            raise ImportError("curl_cffi not installed. Run: pip install curl_cffi")
        
        profile = impersonate or self._get_next_profile()
        
        async with AsyncSession(impersonate=profile) as session:
            response = await session.get(
                url,
                headers=self._get_headers()
            )
            return response.text
    
    def _get_next_profile(self) -> str:
        """Rotate through browser profiles"""
        profile = self.BROWSER_PROFILES[self.current_profile_idx]
        self.current_profile_idx = (self.current_profile_idx + 1) % len(self.BROWSER_PROFILES)
        return profile
    
    def _get_headers(self) -> dict:
        """Get browser-like headers"""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
