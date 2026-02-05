"""
CAPTCHA Solver - 2Captcha Integration

Automatically solves reCAPTCHA, hCaptcha, and other CAPTCHAs.
"""

import asyncio
import httpx
from typing import Optional
from src.config import config


class CaptchaSolver:
    """
    CAPTCHA solving using 2Captcha API.
    
    Supports:
    - reCAPTCHA v2
    - reCAPTCHA v3
    - hCaptcha
    - Image CAPTCHA
    - Turnstile
    """
    
    API_URL = "https://2captcha.com"
    
    def __init__(self):
        self.api_key = config.captcha.twocaptcha_api_key
        self.client = httpx.AsyncClient(timeout=120.0)
    
    def is_configured(self) -> bool:
        """Check if 2Captcha is configured"""
        return bool(self.api_key)
    
    async def solve_recaptcha_v2(
        self, 
        sitekey: str,
        page_url: str,
        invisible: bool = False
    ) -> Optional[str]:
        """
        Solve reCAPTCHA v2.
        
        Args:
            sitekey: Site key from the page
            page_url: URL of the page with CAPTCHA
            invisible: Whether it's invisible reCAPTCHA
        
        Returns:
            CAPTCHA token or None
        """
        if not self.is_configured():
            return None
        
        # Submit task
        response = await self.client.post(
            f"{self.API_URL}/in.php",
            data={
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": page_url,
                "invisible": 1 if invisible else 0,
                "json": 1
            }
        )
        
        data = response.json()
        if data.get("status") != 1:
            print(f"2Captcha submission error: {data}")
            return None
        
        task_id = data.get("request")
        
        # Poll for result
        return await self._poll_result(task_id)
    
    async def solve_recaptcha_v3(
        self, 
        sitekey: str,
        page_url: str,
        action: str = "verify",
        min_score: float = 0.9
    ) -> Optional[str]:
        """
        Solve reCAPTCHA v3.
        
        Args:
            sitekey: Site key
            page_url: Page URL
            action: Action parameter
            min_score: Minimum required score
        
        Returns:
            CAPTCHA token or None
        """
        if not self.is_configured():
            return None
        
        response = await self.client.post(
            f"{self.API_URL}/in.php",
            data={
                "key": self.api_key,
                "method": "userrecaptcha",
                "version": "v3",
                "googlekey": sitekey,
                "pageurl": page_url,
                "action": action,
                "min_score": min_score,
                "json": 1
            }
        )
        
        data = response.json()
        if data.get("status") != 1:
            return None
        
        return await self._poll_result(data.get("request"))
    
    async def solve_hcaptcha(
        self, 
        sitekey: str,
        page_url: str
    ) -> Optional[str]:
        """
        Solve hCaptcha.
        
        Args:
            sitekey: Site key
            page_url: Page URL
        
        Returns:
            CAPTCHA token or None
        """
        if not self.is_configured():
            return None
        
        response = await self.client.post(
            f"{self.API_URL}/in.php",
            data={
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1
            }
        )
        
        data = response.json()
        if data.get("status") != 1:
            return None
        
        return await self._poll_result(data.get("request"))
    
    async def solve_turnstile(
        self, 
        sitekey: str,
        page_url: str
    ) -> Optional[str]:
        """
        Solve Cloudflare Turnstile.
        
        Args:
            sitekey: Site key
            page_url: Page URL
        
        Returns:
            CAPTCHA token or None
        """
        if not self.is_configured():
            return None
        
        response = await self.client.post(
            f"{self.API_URL}/in.php",
            data={
                "key": self.api_key,
                "method": "turnstile",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1
            }
        )
        
        data = response.json()
        if data.get("status") != 1:
            return None
        
        return await self._poll_result(data.get("request"))
    
    async def _poll_result(
        self, 
        task_id: str,
        max_attempts: int = 60,
        interval: float = 3.0
    ) -> Optional[str]:
        """Poll for CAPTCHA solution"""
        for _ in range(max_attempts):
            await asyncio.sleep(interval)
            
            response = await self.client.get(
                f"{self.API_URL}/res.php",
                params={
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1
                }
            )
            
            data = response.json()
            
            if data.get("status") == 1:
                return data.get("request")
            
            if data.get("request") != "CAPCHA_NOT_READY":
                print(f"2Captcha error: {data}")
                return None
        
        return None
    
    async def get_balance(self) -> float:
        """Get account balance"""
        if not self.is_configured():
            return 0.0
        
        response = await self.client.get(
            f"{self.API_URL}/res.php",
            params={
                "key": self.api_key,
                "action": "getbalance",
                "json": 1
            }
        )
        
        data = response.json()
        return float(data.get("request", 0))
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
