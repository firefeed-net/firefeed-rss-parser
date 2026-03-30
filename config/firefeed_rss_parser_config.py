"""Configuration module for FireFeed RSS Parser."""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from firefeed_core.config.services_config import get_service_config
from firefeed_core.config.settings import FireFeedSettings

# Global configuration instance
config = get_service_config()


def get_config():
    """Get global configuration instance."""
    return config


# Compatibility properties for existing code
@property
def base_url(self) -> str:
    """Get FireFeed API base URL."""
    return self.api_base_url

@property
def api_key(self) -> Optional[str]:
    """Get FireFeed API key."""
    return os.getenv("FIREFEED_API_RSS_PARSER_TOKEN")

@property
def timeout(self) -> float:
    """Get FireFeed API timeout."""
    return float(os.getenv("FETCH_TIMEOUT", "30"))

@property
def max_retries(self) -> int:
    """Get FireFeed API max retries."""
    return int(os.getenv("MAX_RETRIES", "3"))

@property
def retry_delay(self) -> float:
    """Get FireFeed API retry delay."""
    return float(os.getenv("RETRY_DELAY", "1.0"))

@property
def max_concurrent_feeds(self) -> int:
    """Get max concurrent feeds."""
    return self.rss.max_concurrent_feeds

@property
def fetch_timeout(self) -> float:
    """Get fetch timeout."""
    return self.rss.request_timeout

@property
def parser_timeout(self) -> float:
    """Get parser timeout."""
    return 10.0

@property
def storage_timeout(self) -> float:
    """Get storage timeout."""
    return 30.0

@property
def media_timeout(self) -> float:
    """Get media timeout."""
    return 15.0

@property
def duplicate_check_timeout(self) -> float:
    """Get duplicate check timeout."""
    return 5.0

@property
def images_root_dir(self) -> str:
    """Get images root directory."""
    return os.getenv("IMAGES_ROOT_DIR", "/app/media")

@property
def image_file_extensions(self) -> list:
    """Get supported image file extensions."""
    return [
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"
    ]

@property
def log_level(self) -> str:
    """Get log level."""
    return os.getenv("LOG_LEVEL", "INFO")

def setup_logging():
    """Setup logging configuration using firefeed_core."""
    from firefeed_core.config.logging_config import setup_logging as core_setup_logging
    core_setup_logging()