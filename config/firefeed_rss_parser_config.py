"""Configuration module for FireFeed RSS Parser."""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path
from firefeed_core.config.services_config import get_service_config, ServiceConfig


@dataclass
class RSSParserConfig:
    config: ServiceConfig = field(default_factory=get_service_config)
    
    @property
    def base_url(self) -> str:
        """Get FireFeed API base URL."""
        return self.config.api_base_url
    
    @property
    def api_key(self) -> Optional[str]:
        """Get FireFeed API key."""
        return os.getenv("FIREFEED_API_SERVICE_TOKEN")
    
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
        # Read directly from env to match documented variable
        return int(os.getenv("MAX_CONCURRENT_FEEDS", "10"))
    
    @property
    def fetch_timeout(self) -> float:
        """Get fetch timeout."""
        return float(os.getenv("FETCH_TIMEOUT", "15.0"))
    
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
    def redis_host(self) -> str:
        """Get Redis host."""
        return os.getenv("REDIS_HOST", "localhost")
    
    @property
    def redis_port(self) -> int:
        """Get Redis port."""
        return int(os.getenv("REDIS_PORT", "6379"))
    
    @property
    def redis_password(self) -> Optional[str]:
        """Get Redis password."""
        pwd = os.getenv("REDIS_PASSWORD", "")
        return pwd if pwd else None
    
    @property
    def redis_db(self) -> int:
        """Get Redis database number."""
        return int(os.getenv("REDIS_DB", "0"))
    
    def get_redis_connection_params(self) -> dict:
        """Get Redis connection parameters (password not included in URL for security)."""
        return {
            "host": self.redis_host,
            "port": self.redis_port,
            "password": self.redis_password,
            "db": self.redis_db,
            "encoding": "utf-8",
            "decode_responses": True
        }
    
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

    @property
    def duplicate_detection_enabled(self) -> bool:
        """Check if duplicate detection is enabled."""
        return os.getenv("DUPLICATE_DETECTION_ENABLED", "true").lower() in ("true", "1", "yes")


# Global configuration instance
config = RSSParserConfig()


def get_config():
    """Get global configuration instance."""
    return config


def setup_logging():
    """Setup logging configuration using firefeed_core."""
    from firefeed_core.config.logging_config import setup_logging as core_setup_logging
    core_setup_logging()

