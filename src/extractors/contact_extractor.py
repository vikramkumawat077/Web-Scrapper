"""
Contact Extractor - Phones, Addresses

Extracts contact information (phones, addresses) from web pages.
"""

import re
from typing import Optional


class ContactExtractor:
    """
    Extract contact information from HTML.
    
    Supports:
    - Phone numbers (international formats)
    - Physical addresses
    - Postal codes
    """
    
    # Phone number patterns
    PHONE_PATTERNS = [
        # International format: +1-234-567-8900
        re.compile(r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
        # UK format: +44 7911 123456
        re.compile(r'\+44\s?\d{4}\s?\d{6}'),
        # Generic international
        re.compile(r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
    ]
    
    # Address patterns
    ADDRESS_PATTERNS = [
        # US ZIP codes
        re.compile(r'\d{1,5}\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Place|Pl)[\s,]+[\w\s]+,?\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?', re.IGNORECASE),
        # UK postcodes
        re.compile(r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}', re.IGNORECASE),
    ]
    
    # Ignore patterns (false positives)
    IGNORE_PHONE_PATTERNS = [
        r'^\d{3,4}$',  # Too short
        r'^1[2-9]\d{2}$',  # Year-like
        r'^\d{10,}$',  # No formatting
    ]
    
    def extract_phones(self, content: str) -> list[str]:
        """
        Extract phone numbers from content.
        
        Args:
            content: HTML or text content
        
        Returns:
            List of phone numbers
        """
        phones = set()
        
        # Clean HTML tags
        text = re.sub(r'<[^>]+>', ' ', content)
        
        for pattern in self.PHONE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                phone = self._clean_phone(match)
                if phone and self._is_valid_phone(phone):
                    phones.add(phone)
        
        return list(phones)
    
    def extract_addresses(self, content: str) -> list[str]:
        """
        Extract physical addresses from content.
        
        Args:
            content: HTML or text content
        
        Returns:
            List of addresses
        """
        addresses = set()
        
        # Clean HTML tags
        text = re.sub(r'<[^>]+>', ' ', content)
        
        for pattern in self.ADDRESS_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                address = self._clean_address(match)
                if address:
                    addresses.add(address)
        
        return list(addresses)
    
    def extract_all(self, content: str) -> dict:
        """
        Extract all contact information.
        
        Returns:
            Dict with phones, addresses, postal_codes
        """
        return {
            "phones": self.extract_phones(content),
            "addresses": self.extract_addresses(content)
        }
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and normalize phone number"""
        # Remove extra whitespace
        phone = " ".join(phone.split())
        return phone.strip()
    
    def _clean_address(self, address: str) -> str:
        """Clean address string"""
        # Remove extra whitespace
        address = " ".join(address.split())
        return address.strip()
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number"""
        # Remove formatting
        digits = re.sub(r'\D', '', phone)
        
        # Check length (7-15 digits)
        if len(digits) < 7 or len(digits) > 15:
            return False
        
        # Check for obvious invalid patterns
        for pattern in self.IGNORE_PHONE_PATTERNS:
            if re.match(pattern, digits):
                return False
        
        return True


class PhoneNumberParser:
    """Parse and format phone numbers"""
    
    @staticmethod
    def format_e164(phone: str, default_country: str = "US") -> Optional[str]:
        """Format phone number in E.164 format"""
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone, default_country)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.E164
                )
        except:
            pass
        return None
    
    @staticmethod
    def get_country(phone: str, default_country: str = "US") -> Optional[str]:
        """Get country code from phone number"""
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone, default_country)
            return phonenumbers.region_code_for_number(parsed)
        except:
            pass
        return None
