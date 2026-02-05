"""
Playwright Scraper - Full Browser Automation

Uses headless Chrome for JavaScript-heavy sites and protection bypass.
"""

import asyncio
from typing import Optional


class PlaywrightScraper:
    """
    Browser automation scraper using Playwright.
    
    Features:
    - JavaScript execution
    - Resource blocking (images/fonts for speed)
    - Stealth mode integration
    - Screenshot capability
    """
    
    def __init__(self, headless: bool = True, block_resources: bool = True):
        self.headless = headless
        self.block_resources = block_resources
        self._browser = None
        self._context = None
    
    async def _get_browser(self):
        """Lazy browser initialization"""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )
                self._context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            except ImportError:
                raise ImportError("playwright not installed. Run: pip install playwright && playwright install chromium")
        return self._browser
    
    async def scrape(
        self, 
        url: str,
        wait_for: Optional[str] = None,
        timeout: int = 30000
    ) -> str:
        """
        Scrape URL with full browser automation.
        
        Args:
            url: URL to scrape
            wait_for: CSS selector to wait for
            timeout: Timeout in milliseconds
        
        Returns:
            HTML content
        """
        await self._get_browser()
        
        page = await self._context.new_page()
        
        try:
            # Block resources for speed
            if self.block_resources:
                await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", 
                                lambda route: route.abort())
            
            # Navigate
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # Wait for specific element if provided
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=5000)
                except:
                    pass
            
            # Wait a bit for JS to execute
            await asyncio.sleep(1)
            
            # Get content
            content = await page.content()
            return content
        
        finally:
            await page.close()
    
    async def scrape_with_scroll(
        self, 
        url: str,
        scroll_count: int = 3,
        delay: float = 1.0
    ) -> str:
        """
        Scrape with infinite scroll handling.
        
        Args:
            url: URL to scrape
            scroll_count: Number of times to scroll
            delay: Delay between scrolls
        
        Returns:
            HTML content
        """
        await self._get_browser()
        
        page = await self._context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            
            for _ in range(scroll_count):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(delay)
            
            return await page.content()
        
        finally:
            await page.close()
    
    async def screenshot(
        self, 
        url: str,
        path: str = "screenshot.png",
        full_page: bool = True
    ) -> str:
        """Take screenshot of page"""
        await self._get_browser()
        
        page = await self._context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle")
            await page.screenshot(path=path, full_page=full_page)
            return path
        
        finally:
            await page.close()
    
    async def close(self):
        """Close browser"""
        if self._browser:
            await self._browser.close()
            await self._playwright.stop()
            self._browser = None
