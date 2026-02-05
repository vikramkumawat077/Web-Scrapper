"""
Cloudflare Bypass - Multiple Strategies

Bypasses Cloudflare protection using various techniques.
"""

import asyncio
from typing import Optional


class CloudflareBypass:
    """
    Cloudflare bypass using multiple strategies.
    
    Strategies (in order of attempt):
    1. curl_cffi with TLS fingerprinting
    2. cloudscraper
    3. FlareSolverr (if running)
    4. Bright Data Web Unlocker
    """
    
    def __init__(self):
        self._flaresolverr_url = "http://localhost:8191/v1"
    
    async def bypass(self, url: str) -> str:
        """
        Attempt Cloudflare bypass with all strategies.
        
        Args:
            url: URL protected by Cloudflare
        
        Returns:
            HTML content
        """
        # Strategy 1: curl_cffi
        try:
            result = await self._try_curl_cffi(url)
            if result and not self._is_cf_challenge(result):
                return result
        except Exception as e:
            print(f"curl_cffi failed: {e}")
        
        # Strategy 2: cloudscraper
        try:
            result = await self._try_cloudscraper(url)
            if result and not self._is_cf_challenge(result):
                return result
        except Exception as e:
            print(f"cloudscraper failed: {e}")
        
        # Strategy 3: FlareSolverr
        try:
            result = await self._try_flaresolverr(url)
            if result:
                return result
        except Exception as e:
            print(f"FlareSolverr failed: {e}")
        
        # Strategy 4: Bright Data
        try:
            result = await self._try_bright_data(url)
            if result:
                return result
        except Exception as e:
            print(f"Bright Data failed: {e}")
        
        raise Exception("All Cloudflare bypass strategies failed")
    
    async def _try_curl_cffi(self, url: str) -> Optional[str]:
        """Try curl_cffi with Chrome impersonation"""
        try:
            from curl_cffi.requests import AsyncSession
            
            async with AsyncSession(impersonate="chrome120") as session:
                response = await session.get(url)
                return response.text
        except ImportError:
            return None
    
    async def _try_cloudscraper(self, url: str) -> Optional[str]:
        """Try cloudscraper library"""
        try:
            import cloudscraper
            
            # Run in thread pool since cloudscraper is sync
            loop = asyncio.get_event_loop()
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            
            response = await loop.run_in_executor(
                None, 
                lambda: scraper.get(url)
            )
            return response.text
        except ImportError:
            return None
    
    async def _try_flaresolverr(self, url: str) -> Optional[str]:
        """Try FlareSolverr API"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self._flaresolverr_url,
                    json={
                        "cmd": "request.get",
                        "url": url,
                        "maxTimeout": 60000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        return data["solution"]["response"]
        except:
            pass
        
        return None
    
    async def _try_bright_data(self, url: str) -> Optional[str]:
        """Try Bright Data Web Unlocker"""
        from src.scrapers.bright_data_scraper import BrightDataScraper
        
        scraper = BrightDataScraper()
        if scraper.is_configured():
            try:
                return await scraper.scrape(url)
            finally:
                await scraper.close()
        
        return None
    
    def _is_cf_challenge(self, html: str) -> bool:
        """Check if response is Cloudflare challenge page"""
        indicators = [
            "cf-browser-verification",
            "challenge-platform",
            "Just a moment...",
            "Checking your browser",
            "cf-spinner",
            "cf_captcha_container"
        ]
        return any(ind in html for ind in indicators)
