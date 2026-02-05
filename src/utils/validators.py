"""
Validators - Data Validation Utilities

Validates extracted data (emails, phones, URLs).
"""

import re
from typing import Optional
from urllib.parse import urlparse


class EmailValidator:
    """Validate email addresses"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Disposable email domains to filter
    DISPOSABLE_DOMAINS = {
        "mailinator.com", "tempmail.com", "throwaway.com",
        "guerrillamail.com", "10minutemail.com", "temp-mail.org"
    }
    
    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email is valid format"""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_REGEX.match(email.lower()))
    
    @classmethod
    def is_business(cls, email: str) -> bool:
        """Check if email is likely a business email"""
        if not cls.is_valid(email):
            return False
        
        domain = email.split("@")[1].lower()
        
        # Filter free email providers
        free_providers = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "icloud.com", "mail.com", "protonmail.com"
        }
        
        return domain not in free_providers and domain not in cls.DISPOSABLE_DOMAINS


class URLValidator:
    """Validate URLs"""
    
    @classmethod
    def is_valid(cls, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @classmethod
    def is_same_domain(cls, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False
    
    @classmethod
    def get_domain(cls, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc.lower()
        except:
            return None


class PhoneValidator:
    """Validate phone numbers"""
    
    @classmethod
    def is_valid(cls, phone: str) -> bool:
        """Check if phone number is valid"""
        # Remove formatting
        digits = re.sub(r'\D', '', phone)
        
        # Check length (7-15 digits)
        return 7 <= len(digits) <= 15
    
    @classmethod
    def normalize(cls, phone: str) -> str:
        """Normalize phone number"""
        # Remove all non-digit except +
        normalized = re.sub(r'[^\d+]', '', phone)
        return normalized


class DataCleaner:
    """Clean and normalize extracted data"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    @staticmethod
    def clean_url(url: str) -> str:
        """Clean and normalize URL"""
        if not url:
            return ""
        
        url = url.strip()
        
        # Remove tracking parameters
        tracking_params = [
            "utm_source", "utm_medium", "utm_campaign",
            "fbclid", "gclid", "ref", "source"
        ]
        
        parsed = urlparse(url)
        if parsed.query:
            # Remove tracking params (simplified)
            clean_query = "&".join([
                p for p in parsed.query.split("&")
                if not any(p.startswith(t + "=") for t in tracking_params)
            ])
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean_query:
                url += f"?{clean_query}"
        
        return url
    
    @staticmethod
    def deduplicate(items: list) -> list:
        """Remove duplicates while preserving order"""
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
