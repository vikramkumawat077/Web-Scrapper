"""
Logging - Structured Logging

Provides structured logging for the scraper.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.config import config


def setup_logger(
    name: str = "scraper",
    level: str = "INFO",
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Set up structured logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Default logger
logger = setup_logger(
    level="INFO",
    log_file=config.logs_dir / "scraper.log"
)


class ScrapeLogger:
    """Specialized logger for scraping operations"""
    
    def __init__(self):
        self.logger = logger
        self._stats = {
            "scraped": 0,
            "failed": 0,
            "blocked": 0,
            "start_time": None
        }
    
    def start_session(self):
        """Start a new scraping session"""
        self._stats = {
            "scraped": 0,
            "failed": 0,
            "blocked": 0,
            "start_time": datetime.now()
        }
        self.logger.info("=" * 50)
        self.logger.info("Scraping session started")
    
    def log_scrape(self, url: str, success: bool, details: str = ""):
        """Log a scrape attempt"""
        if success:
            self._stats["scraped"] += 1
            self.logger.info(f"✅ Scraped: {url[:60]} {details}")
        else:
            self._stats["failed"] += 1
            self.logger.warning(f"❌ Failed: {url[:60]} {details}")
    
    def log_blocked(self, url: str, protection: str = "unknown"):
        """Log blocked request"""
        self._stats["blocked"] += 1
        self.logger.warning(f"🚫 Blocked: {url[:60]} ({protection})")
    
    def log_extract(self, url: str, data_type: str, count: int):
        """Log extraction"""
        self.logger.info(f"📦 Extracted {count} {data_type} from {url[:50]}")
    
    def log_error(self, message: str, exc: Optional[Exception] = None):
        """Log error"""
        if exc:
            self.logger.error(f"💥 Error: {message} - {exc}")
        else:
            self.logger.error(f"💥 Error: {message}")
    
    def end_session(self) -> dict:
        """End session and return stats"""
        duration = datetime.now() - self._stats["start_time"] if self._stats["start_time"] else None
        
        stats = {
            **self._stats,
            "duration": str(duration) if duration else "N/A"
        }
        
        self.logger.info("-" * 50)
        self.logger.info(f"Session complete: {stats['scraped']} scraped, {stats['failed']} failed, {stats['blocked']} blocked")
        self.logger.info(f"Duration: {stats['duration']}")
        self.logger.info("=" * 50)
        
        return stats


# Global scrape logger
scrape_logger = ScrapeLogger()
