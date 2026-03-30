"""Dependency injection container for FireFeed RSS Parser."""

import logging
from typing import Callable, Any
from firefeed_rss_parser.config.firefeed_rss_parser_config import get_config

logger = logging.getLogger(__name__)

def get_service(key: str) -> Any:
    """Get config object for compatibility with image.py."""
    config = get_config()
    return config

# Existing functions can stay, but comment out core imports
# from firefeed_core... 

def setup_di_container() -> None:
    logger.info("DI container setup (image saving config ready)")
    pass

def shutdown_di_container() -> None:
    logger.info("DI container shutdown")
    pass

