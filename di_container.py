"""Dependency injection container for FireFeed RSS Parser."""

import logging
from typing import Dict, Any

from firefeed_core.di_container import register_singleton, register_instance, get_container
from firefeed_core.config.settings import Settings
from firefeed_core.api_client.client import APIClient
from services.duplicate_detector import DuplicateDetector
from services.health_checker import HealthChecker
from services.media_extractor import MediaExtractor
from services.rss_fetcher import RSSFetcher
from services.rss_manager import RSSManager
from services.rss_parser import RSSParser
from services.rss_storage import RSSStorage
from services.translation_service import TranslationService


logger = logging.getLogger(__name__)


def setup_di_container() -> None:
    """Setup dependency injection container for RSS Parser."""
    container = get_container()
    
    # Get settings
    settings = Settings()
    register_instance("settings", settings)
    
    # 1. HTTP client services
    # API client for FireFeed API using firefeed-core
    api_client = APIClient(
        base_url=settings.api_base_url,
        token=settings.jwt_secret_key,  # Using jwt_secret_key as API key for now
        service_id="firefeed-rss-parser",
        timeout=settings.api_timeout
    )
    register_singleton("api_client", lambda: api_client)
    
    # 2. Core RSS services
    # RSS fetcher
    rss_fetcher = RSSFetcher(timeout=15)
    register_singleton("rss_fetcher", lambda: rss_fetcher)
    
    # RSS parser
    rss_parser = RSSParser(
        fetcher=rss_fetcher,
        timeout=10
    )
    register_singleton("rss_parser", lambda: rss_parser)
    
    # Media extractor
    media_extractor = MediaExtractor(
        timeout=15,
        max_size=10485760,  # 10MB
        allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"]
    )
    register_singleton("media_extractor", lambda: media_extractor)
    
    # Duplicate detector
    duplicate_detector = DuplicateDetector(api_client=api_client)
    register_singleton("duplicate_detector", lambda: duplicate_detector)
    
    # RSS storage
    rss_storage = RSSStorage(api_client=api_client)
    register_singleton("rss_storage", lambda: rss_storage)
    
    # Translation service
    translation_service = TranslationService(
        api_client=api_client,
        timeout=30
    )
    register_singleton("translation_service", lambda: translation_service)
    
    # 3. Manager services
    # RSS manager
    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        storage=rss_storage,
        duplicate_detector=duplicate_detector,
        media_extractor=media_extractor,
        translation_service=translation_service,
        timeout=60
    )
    register_singleton("rss_manager", lambda: rss_manager)
    
    # 4. Health and monitoring
    # Health checker
    health_checker = HealthChecker(
        api_client=api_client,
        rss_fetcher=rss_fetcher,
        rss_parser=rss_parser,
        rss_storage=rss_storage,
        duplicate_detector=duplicate_detector,
        media_extractor=media_extractor,
        translation_service=translation_service
    )
    register_singleton("health_checker", lambda: health_checker)
    
    logger.info("RSS Parser DI container setup completed successfully")


def shutdown_di_container() -> None:
    """Shutdown dependency injection container."""
    container = get_container()
    
    # Close API client
    api_client = container.resolve_optional("api_client")
    if api_client:
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(api_client.close())
    
    # Clear container
    container.clear()
    
    logger.info("RSS Parser DI container shutdown completed successfully")