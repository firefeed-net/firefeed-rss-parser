"""FireFeed RSS Parser - Main Service"""

import asyncio
import logging
import os
from typing import Optional
import time

from config import setup_logging
from services.rss_manager import RSSManager
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from services.rss_storage import RSSStorage
from firefeed_core.api_client.client import APIClient


async def get_feeds_to_process(api_client: APIClient) -> list:
    """Get RSS feeds that need to be processed."""
    params = {"page": 1, "size": 100}
    response = await api_client.get("/api/v1/internal/rss/feeds", params=params)
    return response.get("data", [])


async def main():
    """Main entry point for RSS Parser service."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting FireFeed RSS Parser service...")
    
    # Load configuration values directly from canonical .env vars
    api_base_url = os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001")
    max_concurrent_feeds = int(os.getenv("MAX_CONCURRENT_FEEDS", "10"))
    fetch_timeout = float(os.getenv("FETCH_TIMEOUT", "15.0"))
    parser_timeout = float(os.getenv("PARSER_TIMEOUT", "10.0"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    
    # Initialize services that can be reused across cycles
    rss_parser_token = os.getenv("RSS_PARSER_TOKEN", "")
    
    if not rss_parser_token:
        logger.warning("RSS_PARSER_TOKEN environment variable not set")

    # Initialize API client once and reuse it
    api_client = APIClient(
        base_url=api_base_url,
        token=rss_parser_token,
        service_id="firefeed-rss-parser",
        timeout=fetch_timeout,
        max_retries=max_retries
    )
    
    # Initialize other services that can be reused
    rss_fetcher = RSSFetcher(
        timeout=fetch_timeout,
        max_retries=max_retries
    )
    
    rss_parser = RSSParser(
        timeout=parser_timeout,
        max_retries=max_retries
    )
    
    media_extractor = MediaExtractor(
        timeout=15.0,
        max_retries=max_retries
    )
    
    duplicate_detector = DuplicateDetector(
        timeout=5.0,
        max_retries=max_retries
    )
    
    rss_storage = RSSStorage(
        timeout=30.0,
        max_retries=max_retries
    )
    
    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        media_extractor=media_extractor,
        duplicate_detector=duplicate_detector,
        storage=rss_storage,
        max_concurrent_feeds=max_concurrent_feeds
    )
    
    restart_delay = float(os.getenv("RETRY_DELAY", "60.0"))
    
    loop_interval = float(os.getenv("FETCH_INTERVAL", "300"))
    if loop_interval < 60:
        loop_interval = 60
    logger.info(f"Configuration loaded: loop_interval={loop_interval}s, base_url={api_base_url}")
    
    try:
        while True:
            try:
                cycle_id = int(time.time())
                cycle_start_time = time.time()
                logger.info("RSS cycle started", extra={
                    "event": "rss_cycle_start",
                    "cycle_id": cycle_id
                })
                
                # Get RSS feeds with error handling
                logger.info("Fetching RSS feeds...")
                try:
                    feeds = await get_feeds_to_process(api_client)
                except Exception as api_err:
                    logger.exception("API feeds fetch failed, backoff")
                    await asyncio.sleep(restart_delay)
                    continue
                
                if not feeds:
                    enable_fallback = os.getenv("ENABLE_FALLBACK_FEEDS", "false").lower() == "true"
                    if enable_fallback:
                        logger.info("Using fallback feeds (BBC)")
                        feeds = [{"id": 1, "url": "https://feeds.bbci.co.uk/news/rss.xml", "name": "BBC News", "language": "en", "is_active": True}]
                    else:
                        logger.info("No feeds available, skipping cycle")
                        await asyncio.sleep(loop_interval)
                        continue
                
                logger.info(f"Processing {len(feeds)} feeds")
                await rss_manager.process_feeds(feeds)
                
                cycle_end_time = time.time()
                elapsed = cycle_end_time - cycle_start_time
                logger.info("RSS cycle completed", extra={
                    "event": "rss_cycle_complete",
                    "cycle_id": cycle_id,
                    "feed_count": len(feeds),
                    "elapsed_seconds": elapsed
                })
                
                await asyncio.sleep(loop_interval)
                
            except asyncio.CancelledError:
                logger.info("Service cancelled gracefully")
                raise
            except Exception:
                logger.exception("Cycle failed")
                await asyncio.sleep(restart_delay)
    finally:
        await api_client.close()


async def process_single_feed(feed_url: str, user_id: Optional[str] = None) -> dict:
    """Process a single RSS feed."""
    setup_logging()

    logger = logging.getLogger(__name__)
    
    # Load configuration values directly from canonical .env vars
    api_base_url = os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001")
    max_concurrent_feeds = int(os.getenv("MAX_CONCURRENT_FEEDS", "10"))
    fetch_timeout = float(os.getenv("FETCH_TIMEOUT", "15.0"))
    parser_timeout = float(os.getenv("PARSER_TIMEOUT", "10.0"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    
    # Initialize services
    rss_parser_token = os.getenv("RSS_PARSER_TOKEN", "")
    if not rss_parser_token:
        logger.warning("RSS_PARSER_TOKEN environment variable not set")
    
    api_client = APIClient(
        base_url=api_base_url,
        token=rss_parser_token,
        service_id="firefeed-rss-parser-single",
        timeout=fetch_timeout,
        max_retries=max_retries
    )
    
    rss_fetcher = RSSFetcher(
        timeout=fetch_timeout,
        max_retries=max_retries
    )
    
    rss_parser = RSSParser(
        timeout=parser_timeout,
        max_retries=max_retries
    )
    
    media_extractor = MediaExtractor(
        timeout=15.0,
        max_retries=max_retries
    )
    
    duplicate_detector = DuplicateDetector(
        timeout=5.0,
        max_retries=max_retries
    )
    
    rss_storage = RSSStorage(
        timeout=30.0,
        max_retries=max_retries
    )
    
    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        media_extractor=media_extractor,
        duplicate_detector=duplicate_detector,
        storage=rss_storage,
        max_concurrent_feeds=max_concurrent_feeds
    )
    
    # Create feed object
    feed = {
        'url': feed_url,
        'user_id': user_id
    }
    
    try:
        # Process the feed
        result = await rss_manager.process_feeds([feed])
        
        logger.info(f"Successfully processed feed: {feed_url}")
        return result
    finally:
        await api_client.close()


if __name__ == "__main__":
    asyncio.run(main())