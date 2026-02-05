"""
Media Extractor - Images, Videos, Documents

Extracts and downloads media files from web pages.
"""

import os
import re
import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Optional
import httpx
from src.config import config


class MediaExtractor:
    """
    Extract and download media files from HTML.
    
    Supports:
    - Images (jpg, png, gif, webp, svg)
    - Videos (mp4, webm)
    - Documents (pdf)
    - Audio (mp3)
    """
    
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"}
    VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov"}
    DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg"}
    
    IMAGE_PATTERN = re.compile(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    SRCSET_PATTERN = re.compile(
        r'<img[^>]+srcset=["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    VIDEO_PATTERN = re.compile(
        r'<(?:video|source)[^>]+src=["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or config.downloads_dir
        self.download_dir.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def extract_image_urls(self, html: str, base_url: str) -> list[str]:
        """
        Extract all image URLs from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for relative paths
        
        Returns:
            List of absolute image URLs
        """
        urls = set()
        
        # Extract from src
        for match in self.IMAGE_PATTERN.findall(html):
            url = self._normalize_url(match, base_url)
            if url:
                urls.add(url)
        
        # Extract from srcset (get highest resolution)
        for match in self.SRCSET_PATTERN.findall(html):
            srcset_urls = self._parse_srcset(match, base_url)
            if srcset_urls:
                urls.add(srcset_urls[-1])  # Highest resolution
        
        # Filter out data URLs and tracking pixels
        return [u for u in urls if self._is_valid_image_url(u)]
    
    def extract_video_urls(self, html: str, base_url: str) -> list[str]:
        """Extract all video URLs from HTML"""
        urls = set()
        
        for match in self.VIDEO_PATTERN.findall(html):
            url = self._normalize_url(match, base_url)
            if url and self._get_extension(url) in self.VIDEO_EXTENSIONS:
                urls.add(url)
        
        return list(urls)
    
    def extract_all_media(self, html: str, base_url: str) -> dict:
        """
        Extract all media from HTML.
        
        Returns:
            Dict with images, videos, documents lists
        """
        return {
            "images": self.extract_image_urls(html, base_url),
            "videos": self.extract_video_urls(html, base_url)
        }
    
    async def download_image(
        self, 
        url: str,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Download image to local storage.
        
        Args:
            url: Image URL
            filename: Optional filename (auto-generated if not provided)
        
        Returns:
            Path to downloaded file or None
        """
        try:
            response = await self.client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if response.status_code != 200:
                return None
            
            # Generate filename
            if not filename:
                ext = self._get_extension(url) or ".jpg"
                hash_name = hashlib.md5(url.encode()).hexdigest()[:12]
                filename = f"{hash_name}{ext}"
            
            # Save file
            filepath = self.download_dir / filename
            filepath.write_bytes(response.content)
            
            return filepath
        
        except Exception as e:
            print(f"Download failed: {url} - {e}")
            return None
    
    async def download_all_images(
        self, 
        urls: list[str],
        max_concurrent: int = 5
    ) -> list[Path]:
        """
        Download multiple images concurrently.
        
        Args:
            urls: List of image URLs
            max_concurrent: Max concurrent downloads
        
        Returns:
            List of downloaded file paths
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(url):
            async with semaphore:
                return await self.download_image(url)
        
        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if r is not None]
    
    def _normalize_url(self, url: str, base_url: str) -> Optional[str]:
        """Normalize relative URL to absolute"""
        if not url:
            return None
        
        # Skip data URLs
        if url.startswith("data:"):
            return None
        
        # Handle protocol-relative
        if url.startswith("//"):
            return f"https:{url}"
        
        # Handle relative
        if not url.startswith(("http://", "https://")):
            return urljoin(base_url, url)
        
        return url
    
    def _parse_srcset(self, srcset: str, base_url: str) -> list[str]:
        """Parse srcset attribute and return URLs sorted by size"""
        parts = srcset.split(",")
        urls = []
        
        for part in parts:
            items = part.strip().split()
            if items:
                url = self._normalize_url(items[0], base_url)
                if url:
                    urls.append(url)
        
        return urls
    
    def _get_extension(self, url: str) -> Optional[str]:
        """Get file extension from URL"""
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        return ext if ext else None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image"""
        # Skip tracking pixels and tiny images
        skip_patterns = [
            "pixel", "tracking", "beacon", "analytics",
            "1x1", "spacer", "blank", "clear.gif"
        ]
        
        url_lower = url.lower()
        return not any(p in url_lower for p in skip_patterns)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
