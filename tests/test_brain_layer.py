"""
Tests for Brain Layer
"""

import pytest
import asyncio
from src.brain.brain_layer import BrainLayer
from src.brain.search_aggregator import SearchAggregator
from src.extractors.email_extractor import EmailExtractor
from src.extractors.social_extractor import SocialExtractor


class TestEmailExtractor:
    """Test email extraction"""
    
    def test_extract_valid_emails(self):
        extractor = EmailExtractor()
        content = """
        Contact us at info@example.org or sales@company.com
        Support: help@website.net
        """
        emails = extractor.extract(content)
        
        assert "info@example.org" in emails
        assert "sales@company.com" in emails
        assert "help@website.net" in emails
    
    def test_filter_invalid_emails(self):
        extractor = EmailExtractor()
        content = """
        Invalid: test@example.com (filtered domain)
        Image: logo.png@style.css (not an email)
        """
        emails = extractor.extract(content)
        
        # example.com is in ignore list
        assert "test@example.com" not in emails
    
    def test_deduplicate_emails(self):
        extractor = EmailExtractor()
        content = """
        info@company.com
        INFO@COMPANY.COM
        info@company.com
        """
        emails = extractor.extract(content)
        
        assert len(emails) == 1
        assert "info@company.com" in emails


class TestSocialExtractor:
    """Test social media extraction"""
    
    def test_extract_twitter(self):
        extractor = SocialExtractor()
        content = '''
        <a href="https://twitter.com/username">Twitter</a>
        <a href="https://x.com/anotheruser">X</a>
        '''
        social = extractor.extract(content)
        
        assert "twitter" in social
        assert len(social["twitter"]) >= 1
    
    def test_extract_instagram(self):
        extractor = SocialExtractor()
        content = '''
        <a href="https://instagram.com/brand">Instagram</a>
        '''
        social = extractor.extract(content)
        
        assert "instagram" in social
    
    def test_filter_generic_links(self):
        extractor = SocialExtractor()
        content = '''
        <a href="https://twitter.com/share">Share</a>
        <a href="https://twitter.com/intent">Intent</a>
        '''
        social = extractor.extract(content)
        
        # share and intent should be filtered
        if "twitter" in social:
            assert "https://twitter.com/share" not in social["twitter"]


class TestBrainLayer:
    """Test brain layer discovery"""
    
    @pytest.mark.asyncio
    async def test_deduplicate(self):
        brain = BrainLayer()
        
        results = [
            {"url": "https://example.com/page"},
            {"url": "https://example.com/page/"},
            {"url": "https://example.com/page?ref=1"},
        ]
        
        unique = brain._deduplicate(results)
        assert len(unique) == 1
    
    @pytest.mark.asyncio
    async def test_keyword_filter(self):
        brain = BrainLayer()
        
        results = [
            {"url": "https://cameras.com", "title": "Vintage Camera Shop", "snippet": "Buy vintage cameras"},
            {"url": "https://random.com", "title": "Random Site", "snippet": "Nothing related"},
        ]
        
        filtered = brain._keyword_filter("vintage cameras", results)
        
        # Camera site should score higher
        assert len(filtered) >= 1
        assert filtered[0]["url"] == "https://cameras.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
