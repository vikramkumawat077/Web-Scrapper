"""
Browser Scraper - Multiple Browser Automation Options

Supports multiple browser engines:
1. DrissionPage (lightweight, no browser install)
2. Selenium (popular, stable)
3. Playwright (powerful, but heavy)
"""

import asyncio
from typing import Optional


class DrissionPageScraper:
    """
    DrissionPage scraper - lightweight browser automation.
    
    Advantages over Playwright:
    - No browser download required (uses installed Chrome)
    - Smaller memory footprint
    - Simpler API
    - Built-in stealth mode
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._page = None
    
    def _get_page(self):
        """Get or create browser page"""
        if self._page is None:
            try:
                from DrissionPage import ChromiumPage, ChromiumOptions
                
                options = ChromiumOptions()
                if self.headless:
                    options.headless()
                options.set_argument('--disable-blink-features=AutomationControlled')
                options.set_argument('--no-sandbox')
                
                self._page = ChromiumPage(options)
            except ImportError:
                raise ImportError("DrissionPage not installed. Run: pip install DrissionPage")
        return self._page
    
    async def scrape(self, url: str, wait_time: float = 2.0) -> str:
        """
        Scrape URL with browser automation.
        
        Args:
            url: URL to scrape
            wait_time: Time to wait for JS execution
        
        Returns:
            HTML content
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, url, wait_time)
    
    def _scrape_sync(self, url: str, wait_time: float) -> str:
        """Sync scraping method"""
        page = self._get_page()
        page.get(url)
        
        # Wait for JS
        import time
        time.sleep(wait_time)
        
        return page.html
    
    async def scrape_with_action(
        self, 
        url: str,
        click_selector: Optional[str] = None,
        scroll: bool = False
    ) -> str:
        """Scrape with custom actions"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._scrape_with_action_sync, 
            url, click_selector, scroll
        )
    
    def _scrape_with_action_sync(
        self, 
        url: str, 
        click_selector: Optional[str],
        scroll: bool
    ) -> str:
        """Sync scraping with actions"""
        page = self._get_page()
        page.get(url)
        
        import time
        time.sleep(1)
        
        if click_selector:
            try:
                page.ele(click_selector).click()
                time.sleep(1)
            except:
                pass
        
        if scroll:
            for _ in range(3):
                page.scroll.down(300)
                time.sleep(0.5)
        
        return page.html
    
    def close(self):
        """Close browser"""
        if self._page:
            self._page.quit()
            self._page = None


class SeleniumScraper:
    """
    Selenium-based scraper.
    
    Advantages:
    - Most stable and widely used
    - Great community support
    - Works with Chrome, Firefox, Edge
    """
    
    def __init__(self, headless: bool = True, browser: str = "chrome"):
        self.headless = headless
        self.browser = browser
        self._driver = None
    
    def _get_driver(self):
        """Get or create WebDriver"""
        if self._driver is None:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                
                options = Options()
                if self.headless:
                    options.add_argument("--headless=new")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                self._driver = webdriver.Chrome(options=options)
            except ImportError:
                raise ImportError("Selenium not installed. Run: pip install selenium webdriver-manager")
        return self._driver
    
    async def scrape(self, url: str, wait_time: float = 2.0) -> str:
        """
        Scrape URL with Selenium.
        
        Args:
            url: URL to scrape
            wait_time: Time to wait for JS
        
        Returns:
            HTML content
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, url, wait_time)
    
    def _scrape_sync(self, url: str, wait_time: float) -> str:
        """Sync scraping"""
        driver = self._get_driver()
        driver.get(url)
        
        import time
        time.sleep(wait_time)
        
        return driver.page_source
    
    def close(self):
        """Close browser"""
        if self._driver:
            self._driver.quit()
            self._driver = None


class UndetectedChromeScraper:
    """
    Undetected Chrome - best for anti-bot bypass.
    
    Uses undetected-chromedriver to bypass:
    - Cloudflare
    - PerimeterX
    - DataDome
    - Imperva
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._driver = None
    
    def _get_driver(self):
        """Get undetected Chrome driver"""
        if self._driver is None:
            try:
                import undetected_chromedriver as uc
                
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                
                self._driver = uc.Chrome(options=options)
            except ImportError:
                raise ImportError("undetected-chromedriver not installed. Run: pip install undetected-chromedriver")
        return self._driver
    
    async def scrape(self, url: str, wait_time: float = 3.0) -> str:
        """Scrape with undetected Chrome"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, url, wait_time)
    
    def _scrape_sync(self, url: str, wait_time: float) -> str:
        """Sync scraping"""
        driver = self._get_driver()
        driver.get(url)
        
        import time
        time.sleep(wait_time)
        
        return driver.page_source
    
    def close(self):
        """Close driver"""
        if self._driver:
            self._driver.quit()
            self._driver = None


def get_best_browser_scraper(
    prefer_lightweight: bool = True,
    headless: bool = True
):
    """
    Get the best available browser scraper.
    
    Priority (if prefer_lightweight):
    1. DrissionPage (lightest)
    2. Selenium
    3. undetected-chromedriver
    4. Playwright
    
    Args:
        prefer_lightweight: Prefer lighter options
        headless: Run headless
    
    Returns:
        Browser scraper instance
    """
    if prefer_lightweight:
        # Try DrissionPage first
        try:
            from DrissionPage import ChromiumPage
            return DrissionPageScraper(headless=headless)
        except ImportError:
            pass
        
        # Try Selenium
        try:
            from selenium import webdriver
            return SeleniumScraper(headless=headless)
        except ImportError:
            pass
        
        # Try undetected-chromedriver
        try:
            import undetected_chromedriver
            return UndetectedChromeScraper(headless=headless)
        except ImportError:
            pass
    
    # Fall back to Playwright
    try:
        from src.scrapers.playwright_scraper import PlaywrightScraper
        return PlaywrightScraper(headless=headless)
    except ImportError:
        pass
    
    raise ImportError(
        "No browser automation library found. Install one of:\n"
        "  pip install DrissionPage        # Lightweight, recommended\n"
        "  pip install selenium            # Stable, widely used\n"
        "  pip install undetected-chromedriver  # Best for anti-bot\n"
        "  pip install playwright && playwright install chromium  # Most powerful"
    )
