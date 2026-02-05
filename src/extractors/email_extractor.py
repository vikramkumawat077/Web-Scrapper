"""
Email Extractor - Extract Email Addresses

Extracts and validates email addresses from HTML content.
"""

import re
from typing import Optional


class EmailExtractor:
    """
    Extract email addresses from HTML/text.
    
    Features:
    - Regex-based extraction
    - Validation
    - Deduplication
    - Filtering of common false positives
    """
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    
    # False positive domains to filter
    IGNORE_DOMAINS = {
        "example.com",
        "email.com", 
        "domain.com",
        "yoursite.com",
        "yourdomain.com",
        "sentry.io",
        "wixpress.com",
        "placeholder.com",
    }
    
    # False positive patterns
    IGNORE_PATTERNS = [
        r".*\.png$",
        r".*\.jpg$",
        r".*\.gif$",
        r".*\.svg$",
        r".*\.css$",
        r".*\.js$",
    ]
    
    def extract(self, content: str) -> list[str]:
        """
        Extract email addresses from content.
        
        Args:
            content: HTML or text content
        
        Returns:
            List of unique, valid email addresses
        """
        # Find all email-like strings
        matches = self.EMAIL_PATTERN.findall(content)
        
        # Filter and deduplicate
        emails = set()
        for email in matches:
            email = email.lower().strip()
            
            if self._is_valid(email):
                emails.add(email)
        
        return sorted(list(emails))
    
    def _is_valid(self, email: str) -> bool:
        """Validate an email address"""
        # Check domain
        domain = email.split("@")[1] if "@" in email else ""
        
        if domain in self.IGNORE_DOMAINS:
            return False
        
        # Check patterns
        for pattern in self.IGNORE_PATTERNS:
            if re.match(pattern, email):
                return False
        
        # Basic validation
        if len(email) < 5 or len(email) > 254:
            return False
        
        if ".." in email:
            return False
        
        return True
