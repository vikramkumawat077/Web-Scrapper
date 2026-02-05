"""
Max Speed Web Scraper - Configuration
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class SearchConfig:
    """Search API Configuration"""
    serper_api_key: Optional[str] = field(default_factory=lambda: os.getenv("SERPER_API_KEY"))
    bing_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BING_API_KEY"))
    brave_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BRAVE_API_KEY"))


@dataclass
class ProxyConfig:
    """Proxy Configuration"""
    bright_data_username: Optional[str] = field(default_factory=lambda: os.getenv("BRIGHT_DATA_USERNAME"))
    bright_data_password: Optional[str] = field(default_factory=lambda: os.getenv("BRIGHT_DATA_PASSWORD"))
    bright_data_host: str = field(default_factory=lambda: os.getenv("BRIGHT_DATA_HOST", "brd.superproxy.io"))
    bright_data_port: int = field(default_factory=lambda: int(os.getenv("BRIGHT_DATA_PORT", "22225")))
    scraperapi_key: Optional[str] = field(default_factory=lambda: os.getenv("SCRAPERAPI_KEY"))
    
    @property
    def bright_data_url(self) -> Optional[str]:
        if self.bright_data_username and self.bright_data_password:
            return f"http://{self.bright_data_username}:{self.bright_data_password}@{self.bright_data_host}:{self.bright_data_port}"
        return None


@dataclass
class CaptchaConfig:
    """CAPTCHA Solver Configuration"""
    twocaptcha_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TWOCAPTCHA_API_KEY"))


@dataclass
class DatabaseConfig:
    """Database Configuration"""
    supabase_url: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    supabase_key: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_KEY"))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))


@dataclass 
class LLMConfig:
    """LLM Configuration"""
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model_name: str = "llama3.2"


@dataclass
class ScraperConfig:
    """Scraper Behavior Configuration"""
    max_concurrency: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENCY", "20")))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))
    request_delay: float = field(default_factory=lambda: float(os.getenv("REQUEST_DELAY", "1.0")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    rotate_user_agent: bool = field(default_factory=lambda: os.getenv("ROTATE_USER_AGENT", "true").lower() == "true")


@dataclass
class Config:
    """Main Configuration Container"""
    search: SearchConfig = field(default_factory=SearchConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    
    # Project paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    cache_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / ".cache")
    downloads_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "downloads")
    
    def __post_init__(self):
        # Create directories if they don't exist
        self.logs_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)


# Global config instance
config = Config()
