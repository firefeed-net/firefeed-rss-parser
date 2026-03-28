"""Configuration module for FireFeed RSS Parser."""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# No global config instance - using environment variables directly


def get_config():
    """Return a simple config object with environment variables."""
    return type('Config', (), {
        'api_base_url': os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001"),
        'rss': type('RSSConfig', (), {
            'max_concurrent_feeds': int(os.getenv("RSS_MAX_CONCURRENT_FEEDS", "10")),
            'request_timeout': float(os.getenv("RSS_REQUEST_TIMEOUT", "15"))
        })()
    })()


# API Configuration Properties
def get_base_url() -> str:
    """Get FireFeed API base URL."""
    return os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001")

def get_api_key() -> Optional[str]:
    """Get FireFeed API key."""
    return os.getenv("RSS_PARSER_TOKEN")

def get_timeout() -> float:
    """Get FireFeed API timeout."""
    return float(os.getenv("FIREFEED_TIMEOUT", "30.0"))

def get_max_retries() -> int:
    """Get FireFeed API max retries."""
    return int(os.getenv("FIREFEED_MAX_RETRIES", "3"))

def get_retry_delay() -> float:
    """Get FireFeed API retry delay."""
    return float(os.getenv("FIREFEED_RETRY_DELAY", "1.0"))

def get_max_concurrent_feeds() -> int:
    """Get max concurrent feeds."""
    return int(os.getenv("RSS_MAX_CONCURRENT_FEEDS", "10"))

def get_fetch_timeout() -> float:
    """Get fetch timeout."""
    return float(os.getenv("RSS_REQUEST_TIMEOUT", "15"))

def get_parser_timeout() -> float:
    """Get parser timeout."""
    return 10.0

def get_storage_timeout() -> float:
    """Get storage timeout."""
    return 30.0

def get_media_timeout() -> float:
    """Get media timeout."""
    return 15.0

def get_duplicate_check_timeout() -> float:
    """Get duplicate check timeout."""
    return 5.0

def get_log_level() -> str:
    """Get log level."""
    return os.getenv("LOG_LEVEL", "INFO")


def setup_logging():
    """Setup logging configuration using firefeed_core."""
    from firefeed_core.config.logging_config import setup_logging as core_setup_logging
    core_setup_logging()