"""
Social Extractor - Extract Social Media Links

Extracts social media profile URLs from HTML content.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class SocialExtractor:
    """
    Extract social media links from HTML.
    
    Supports:
    - Twitter/X
    - Instagram
    - Facebook
    - LinkedIn
    - TikTok
    - YouTube
    - Pinterest
    """
    
    PATTERNS = {
        "twitter": re.compile(r'https?://(www\.)?(twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?', re.I),
        "instagram": re.compile(r'https?://(www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?', re.I),
        "facebook": re.compile(r'https?://(www\.)?facebook\.com/([a-zA-Z0-9.]+)/?', re.I),
        "linkedin": re.compile(r'https?://(www\.)?linkedin\.com/(in|company)/([a-zA-Z0-9_-]+)/?', re.I),
        "tiktok": re.compile(r'https?://(www\.)?tiktok\.com/@([a-zA-Z0-9_.]+)/?', re.I),
        "youtube": re.compile(r'https?://(www\.)?youtube\.com/(@?[a-zA-Z0-9_-]+)/?', re.I),
        "pinterest": re.compile(r'https?://(www\.)?pinterest\.com/([a-zA-Z0-9_]+)/?', re.I),
    }
    
    IGNORE_USERNAMES = {
        "share", "sharer", "intent", "home", "login", "signup",
        "help", "about", "contact", "privacy", "terms", "policies"
    }
    
    def extract(self, content: str) -> dict[str, list[str]]:
        """
        Extract social media links from content.
        
        Args:
            content: HTML content
        
        Returns:
            Dict mapping platform to list of profile URLs
        """
        results = {}
        
        for platform, pattern in self.PATTERNS.items():
            matches = pattern.findall(content)
            urls = set()
            
            for match in matches:
                # Get username from match groups
                username = match[-1] if match else None
                
                if username and username.lower() not in self.IGNORE_USERNAMES:
                    url = self._build_url(platform, username)
                    urls.add(url)
            
            if urls:
                results[platform] = sorted(list(urls))
        
        return results
    
    def _build_url(self, platform: str, username: str) -> str:
        """Build canonical URL for platform"""
        templates = {
            "twitter": f"https://twitter.com/{username}",
            "instagram": f"https://instagram.com/{username}",
            "facebook": f"https://facebook.com/{username}",
            "linkedin": f"https://linkedin.com/in/{username}",
            "tiktok": f"https://tiktok.com/@{username}",
            "youtube": f"https://youtube.com/{username}",
            "pinterest": f"https://pinterest.com/{username}",
        }
        return templates.get(platform, "")
