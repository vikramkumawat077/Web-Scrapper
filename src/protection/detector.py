"""
Protection Detector - Identify Website Protection

Detects the type of protection a website uses:
- Cloudflare
- Akamai
- PerimeterX
- DataDome
- CAPTCHA
"""

from enum import Enum
from typing import Optional
import httpx


class ProtectionType(Enum):
    """Types of website protection"""
    NONE = "none"
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    PERIMETERX = "perimeterx"
    DATADOME = "datadome"
    RECAPTCHA = "recaptcha"
    HCAPTCHA = "hcaptcha"
    UNKNOWN = "unknown"


async def detect_protection(url: str) -> ProtectionType:
    """
    Detect what protection a website uses.
    
    Args:
        url: URL to check
    
    Returns:
        ProtectionType enum
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            headers = dict(response.headers)
            html = response.text.lower()
            
            # Check headers
            if "cf-ray" in headers or "cf-cache-status" in headers:
                return ProtectionType.CLOUDFLARE
            
            if "x-akamai" in str(headers).lower():
                return ProtectionType.AKAMAI
            
            if "x-px" in headers or "_pxhd" in str(response.cookies):
                return ProtectionType.PERIMETERX
            
            if "datadome" in str(headers).lower():
                return ProtectionType.DATADOME
            
            # Check HTML content
            if "challenges.cloudflare.com" in html or "cf-browser-verification" in html:
                return ProtectionType.CLOUDFLARE
            
            if "recaptcha" in html or "g-recaptcha" in html:
                return ProtectionType.RECAPTCHA
            
            if "hcaptcha" in html or "h-captcha" in html:
                return ProtectionType.HCAPTCHA
            
            if "perimeterx" in html:
                return ProtectionType.PERIMETERX
            
            # Check for generic blocking
            if any(x in html for x in ["access denied", "bot detected", "please verify"]):
                return ProtectionType.UNKNOWN
            
            return ProtectionType.NONE
    
    except Exception:
        return ProtectionType.UNKNOWN


def get_recommended_engine(protection: ProtectionType) -> str:
    """
    Get recommended scraping engine for protection type.
    
    Returns:
        Engine name: "httpx", "curl", "playwright", "bright_data"
    """
    recommendations = {
        ProtectionType.NONE: "httpx",
        ProtectionType.CLOUDFLARE: "curl",
        ProtectionType.AKAMAI: "curl",
        ProtectionType.PERIMETERX: "playwright",
        ProtectionType.DATADOME: "bright_data",
        ProtectionType.RECAPTCHA: "playwright",
        ProtectionType.HCAPTCHA: "playwright",
        ProtectionType.UNKNOWN: "curl",
    }
    return recommendations.get(protection, "curl")
