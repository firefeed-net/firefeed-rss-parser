"""FireFeed RSS Parser - Main Service"""

import asyncio
import logging
import os
from typing import Optional
import time

from config.firefeed_rss_parser_config import get_config, setup_logging
from services.rss_manager import RSSManager
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from services.rss_storage import RSSStorage
from firefeed_core.api_client.client import APIClient
from health_check import start_health_server


async def get_feeds_to_process(api_client: APIClient) -> list:
    """Get RSS feeds that need to be processed."""
    params = {"page": 1, "size": 100}
    response = await api_client.get("/api/v1/internal/rss/feeds", params=params)
    return response.get("data", []) if isinstance(response, dict) else []


async def main():
    """Main entry point for RSS Parser service."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting FireFeed RSS Parser service...")

    # Load configuration from central config
    config = get_config()
    api_base_url = config.base_url
    max_concurrent_feeds = config.max_concurrent_feeds
    fetch_timeout = config.fetch_timeout
    parser_timeout = config.parser_timeout
    max_retries = config.max_retries
    health_port = int(os.getenv("HEALTH_CHECK_PORT", "8081"))

    # Initialize API client once and reuse it
    api_token = os.getenv("FIREFEED_API_SERVICE_TOKEN", "")
    if not api_token:
        logger.error("FIREFEED_API_SERVICE_TOKEN missing - cannot connect to API")
        raise ValueError("FIREFEED_API_SERVICE_TOKEN required")

    api_client = APIClient(
        base_url=api_base_url,
        token=api_token,
        service_id="firefeed-rss-parser",
        timeout=fetch_timeout,
        max_retries=max_retries
    )

    # Initialize services
    rss_fetcher = RSSFetcher(timeout=fetch_timeout, max_retries=max_retries)
    rss_parser = RSSParser(timeout=parser_timeout, max_retries=max_retries)
    media_extractor = MediaExtractor(timeout=15.0, max_retries=max_retries)
    duplicate_detector = DuplicateDetector()
    rss_storage = RSSStorage(timeout=30.0, max_retries=max_retries)

    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        media_extractor=media_extractor,
        duplicate_detector=duplicate_detector,
        storage=rss_storage,
        max_concurrent_feeds=max_concurrent_feeds
    )

    restart_delay = config.retry_delay
    loop_interval = float(os.getenv("FETCH_INTERVAL", "600"))
    if loop_interval < 60:
        loop_interval = 60
    logger.info(f"Configuration: loop_interval={loop_interval}s")

    # Start health check server in the background
    health_runner = await start_health_server(port=health_port)

    try:
        while True:
            try:
                logger.info("RSS cycle started")

                feeds = await get_feeds_to_process(api_client)
                if not feeds:
                    logger.info("No feeds available, skipping cycle")
                    await asyncio.sleep(loop_interval)
                    continue

                logger.info(f"Processing {len(feeds)} feeds")
                await rss_manager.process_feeds(feeds)

                logger.info("RSS cycle completed")
                await asyncio.sleep(loop_interval)

            except asyncio.CancelledError:
                logger.info("Service cancelled gracefully")
                raise
            except Exception:
                logger.exception("Cycle failed")
                await asyncio.sleep(restart_delay)
    finally:
        await api_client.close()
        await rss_manager.cleanup()
        await health_runner.cleanup()


async def process_single_feed(feed_url: str, user_id: Optional[str] = None) -> dict:
    """Process a single RSS feed."""
    from config.firefeed_rss_parser_config import get_config
    setup_logging()
    logger = logging.getLogger(__name__)
    config = get_config()
    api_base_url = config.base_url
    api_token = config.api_key

    if not api_token:
        logger.error("FIREFEED_API_SERVICE_TOKEN missing - cannot connect to API")
        raise ValueError("FIREFEED_API_SERVICE_TOKEN required")
    
    api_client = APIClient(
        base_url=api_base_url,
        token=api_token,
        service_id="firefeed-rss-parser-single"
    )
    
    rss_fetcher = RSSFetcher()
    rss_parser = RSSParser()
    media_extractor = MediaExtractor()
    duplicate_detector = DuplicateDetector()
    rss_storage = RSSStorage()
    
    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        media_extractor=media_extractor,
        duplicate_detector=duplicate_detector,
        storage=rss_storage
    )
    
    feed = {'url': feed_url, 'user_id': user_id}
    
    try:
        result = await rss_manager.process_feeds([feed])
        logger.info(f"Processed feed: {feed_url}")
        return result
    finally:
        await api_client.close()
        await rss_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

