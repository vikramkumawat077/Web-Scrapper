"""
Bright Data Scraper - Premium Proxy Integration

Uses Bright Data Web Unlocker for heavily protected sites.
"""

import httpx
from typing import Optional
from src.config import config


class BrightDataScraper:
    """
    Bright Data integration for heavily protected sites.
    
    Features:
    - Web Unlocker API
    - Residential/datacenter proxies
    - SERP API for search results
    - Scraping Browser for complex sites
    """
    
    def __init__(self):
        proxy_url = config.proxy.bright_data_url
        self.proxy = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
        self.client = httpx.AsyncClient(
            timeout=60.0,
            proxy=proxy_url if proxy_url else None
        )
    
    def is_configured(self) -> bool:
        """Check if Bright Data is configured"""
        return bool(config.proxy.bright_data_username)
    
    async def scrape(
        self, 
        url: str,
        country: str = "us",
        session_id: Optional[str] = None
    ) -> str:
        """
        Scrape URL using Bright Data proxy.
        
        Args:
            url: URL to scrape
            country: Target country for proxy
            session_id: Session ID for sticky sessions
        
        Returns:
            HTML content
        """
        if not self.is_configured():
            raise ValueError("Bright Data not configured. Set BRIGHT_DATA_USERNAME and BRIGHT_DATA_PASSWORD")
        
        # Build proxy URL with country targeting
        proxy_url = self._build_proxy_url(country, session_id)
        
        async with httpx.AsyncClient(
            timeout=60.0,
            proxy=proxy_url
        ) as client:
            response = await client.get(
                url,
                headers=self._get_headers()
            )
            return response.text
    
    async def scrape_serp(
        self, 
        query: str,
        engine: str = "google",
        country: str = "us",
        num_results: int = 10
    ) -> list[dict]:
        """
        Get search results using Bright Data SERP API.
        
        Args:
            query: Search query
            engine: Search engine (google, bing)
            country: Target country
            num_results: Number of results
        
        Returns:
            List of search results
        """
        if not self.is_configured():
            return []
        
        # Bright Data SERP API endpoint
        serp_url = f"https://brightdata.com/api/serp/search?q={query}&engine={engine}&country={country}&num={num_results}"
        
        try:
            response = await self.client.get(
                serp_url,
                headers={
                    "Authorization": f"Bearer {config.proxy.bright_data_password}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            print(f"SERP API error: {e}")
        
        return []
    
    def _build_proxy_url(
        self, 
        country: str = "us",
        session_id: Optional[str] = None
    ) -> str:
        """Build Bright Data proxy URL with options"""
        username = config.proxy.bright_data_username
        password = config.proxy.bright_data_password
        host = config.proxy.bright_data_host
        port = config.proxy.bright_data_port
        
        # Add country and session to username
        if country:
            username = f"{username}-country-{country}"
        if session_id:
            username = f"{username}-session-{session_id}"
        
        return f"http://{username}:{password}@{host}:{port}"
    
    def _get_headers(self) -> dict:
        """Get request headers"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
