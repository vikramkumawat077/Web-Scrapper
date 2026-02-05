"""
Engine Selector - Auto-Select Best Scraping Engine

Automatically selects the fastest/most appropriate scraping engine
based on the target site's protection level.
"""

import asyncio
from typing import Optional
from src.scrapers.httpx_scraper import HttpxScraper
from src.scrapers.curl_cffi_scraper import CurlCffiScraper
from src.protection.detector import detect_protection, ProtectionType


# Engine instances
_httpx_scraper = None
_curl_scraper = None


def get_httpx_scraper() -> HttpxScraper:
    global _httpx_scraper
    if _httpx_scraper is None:
        _httpx_scraper = HttpxScraper()
    return _httpx_scraper


def get_curl_scraper() -> CurlCffiScraper:
    global _curl_scraper
    if _curl_scraper is None:
        _curl_scraper = CurlCffiScraper()
    return _curl_scraper


async def smart_scrape(
    url: str,
    force_engine: Optional[str] = None,
    retry_on_block: bool = True
) -> str:
    """
    Intelligently scrape a URL using the best engine.
    
    Pipeline:
    1. Detect protection type
    2. Select appropriate engine
    3. Scrape with escalation on failure
    
    Args:
        url: URL to scrape
        force_engine: Force specific engine ("httpx", "curl", "playwright")
        retry_on_block: Retry with different engine if blocked
    
    Returns:
        HTML content of the page
    """
    # If engine forced, use directly
    if force_engine == "httpx":
        return await get_httpx_scraper().scrape(url)
    elif force_engine == "curl":
        return await get_curl_scraper().scrape(url)
    
    # Try fastest engine first (httpx)
    try:
        html = await get_httpx_scraper().scrape(url)
        
        # Check if blocked
        if _is_blocked(html):
            if retry_on_block:
                # Escalate to curl_cffi (TLS fingerprinting)
                return await get_curl_scraper().scrape(url)
            else:
                raise Exception("Blocked by protection")
        
        return html
    
    except Exception as e:
        if retry_on_block:
            # Try curl_cffi
            try:
                return await get_curl_scraper().scrape(url)
            except:
                pass
        raise e


def _is_blocked(html: str) -> bool:
    """Check if response indicates blocking"""
    block_indicators = [
        "cf-browser-verification",
        "challenge-platform",
        "captcha",
        "access denied",
        "please wait while we verify",
        "checking your browser",
        "just a moment",
        "ddos protection",
        "bot detection",
    ]
    
    html_lower = html.lower()
    return any(indicator in html_lower for indicator in block_indicators)
