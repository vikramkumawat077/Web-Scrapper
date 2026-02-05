"""
Platform Harvester - Marketplace Website Discovery

Harvests seller/shop URLs from major platforms:
- Amazon
- eBay
- Etsy
- Google Maps
"""

import asyncio
import re
import httpx
from typing import Optional


class PlatformHarvester:
    """
    Harvest websites from e-commerce platforms.
    
    Many businesses are found through their marketplace presence.
    This module extracts their direct websites from platform profiles.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def harvest(self, query: str, max_per_platform: int = 20) -> list[dict]:
        """
        Harvest websites from all platforms.
        
        Args:
            query: Search query
            max_per_platform: Maximum results per platform
        
        Returns:
            List of discovered websites
        """
        tasks = [
            self._harvest_amazon(query, max_per_platform),
            self._harvest_ebay(query, max_per_platform),
            self._harvest_etsy(query, max_per_platform),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
        
        return all_results
    
    async def _harvest_amazon(self, query: str, max_results: int) -> list[dict]:
        """Extract seller website URLs from Amazon search"""
        results = []
        
        try:
            # Search Amazon (requires scraping or API)
            # This is a simplified version - full implementation needs
            # proper Amazon scraping with protection bypass
            search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
            
            # Note: Amazon heavily blocks scrapers
            # In production, use Bright Data or similar
            response = await self.client.get(search_url)
            
            if response.status_code == 200:
                # Extract seller links (simplified regex)
                seller_links = re.findall(
                    r'href="(/sp\?seller=[A-Z0-9]+)"', 
                    response.text
                )
                
                for link in seller_links[:max_results]:
                    results.append({
                        "url": f"https://www.amazon.com{link}",
                        "title": "Amazon Seller",
                        "snippet": f"Found via Amazon search: {query}",
                        "source": "amazon"
                    })
        except Exception as e:
            print(f"Amazon harvest error: {e}")
        
        return results
    
    async def _harvest_ebay(self, query: str, max_results: int) -> list[dict]:
        """Extract seller website URLs from eBay search"""
        results = []
        
        try:
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}"
            response = await self.client.get(search_url)
            
            if response.status_code == 200:
                # Extract seller profile links
                seller_links = re.findall(
                    r'href="(https://www\.ebay\.com/usr/[^"]+)"',
                    response.text
                )
                
                for link in list(set(seller_links))[:max_results]:
                    results.append({
                        "url": link,
                        "title": "eBay Seller",
                        "snippet": f"Found via eBay search: {query}",
                        "source": "ebay"
                    })
        except Exception as e:
            print(f"eBay harvest error: {e}")
        
        return results
    
    async def _harvest_etsy(self, query: str, max_results: int) -> list[dict]:
        """Extract shop URLs from Etsy search"""
        results = []
        
        try:
            search_url = f"https://www.etsy.com/search?q={query.replace(' ', '+')}"
            response = await self.client.get(search_url)
            
            if response.status_code == 200:
                # Extract shop links
                shop_links = re.findall(
                    r'href="(https://www\.etsy\.com/shop/[^"?]+)"',
                    response.text
                )
                
                for link in list(set(shop_links))[:max_results]:
                    results.append({
                        "url": link,
                        "title": "Etsy Shop",
                        "snippet": f"Found via Etsy search: {query}",
                        "source": "etsy"
                    })
        except Exception as e:
            print(f"Etsy harvest error: {e}")
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
