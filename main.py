"""FireFeed RSS Parser - Main Service"""

import asyncio
import logging
import os
from typing import Optional
from pathlib import Path

from config import setup_logging, get_config
from services.rss_manager import RSSManager
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from services.rss_storage import RSSStorage
from firefeed_core.api_client.client import APIClient
from utils.validation import validate_url
from firefeed_core.exceptions.rss_exceptions import RSSException as RSSParserError


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
    
    try:
        config = get_config()
        api_base_url = os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001")
        logger.info(f"Configuration loaded. Base URL: {api_base_url}")
        
        # Initialize FireFeed API client
        rss_parser_token = os.getenv("RSS_PARSER_TOKEN", "")
        if not rss_parser_token:
            logger.warning("RSS_PARSER_TOKEN environment variable not set")
        
        api_client = APIClient(
            base_url=api_base_url,
            token=rss_parser_token,
            service_id="firefeed-rss-parser",
            timeout=float(os.getenv("FIREFEED_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        # Initialize services
        rss_fetcher = RSSFetcher(
            timeout=float(os.getenv("FIREFEED_FETCH_TIMEOUT", "15.0")),
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        rss_parser = RSSParser(
            timeout=10.0,
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        media_extractor = MediaExtractor(
            timeout=15.0,
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        duplicate_detector = DuplicateDetector(
            timeout=5.0,
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        rss_storage = RSSStorage(
            timeout=30.0,
            max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
        )
        
        rss_manager = RSSManager(
            fetcher=rss_fetcher,
            parser=rss_parser,
            media_extractor=media_extractor,
            duplicate_detector=duplicate_detector,
            storage=rss_storage,
            max_concurrent_feeds=int(os.getenv("RSS_MAX_CONCURRENT_FEEDS", "10"))
        )
        
        # Get RSS feeds to process
        logger.info("Fetching RSS feeds to process...")
        
        try:
            feeds = await get_feeds_to_process(api_client)
            if not feeds:
                logger.info("No feeds returned from API, using fallback sample feeds")
                # Fallback to sample feeds for testing - using more reliable feeds
                feeds = [
                    {
                        'id': 1,
                        'url': 'https://feeds.bbci.co.uk/news/rss.xml',
                        'name': 'BBC News',
                        'language': 'en',
                        'is_active': True
                    },
                    {
                        'id': 2,
                        'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
                        'name': 'NYT Home Page',
                        'language': 'en',
                        'is_active': True
                    },
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch feeds from API: {e}, using fallback sample feeds")
            # Fallback to sample feeds for testing
            feeds = [
                {
                    'id': 1,
                    'url': 'https://feeds.bbci.co.uk/news/rss.xml',
                    'name': 'BBC News',
                    'language': 'en',
                    'is_active': True
                },
                {
                    'id': 2,
                    'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
                    'name': 'NYT Home Page',
                    'language': 'en',
                    'is_active': True
                },
            ]
        
        if not feeds:
            logger.info("No feeds to process")
            return
            
        logger.info(f"Found {len(feeds)} feeds to process")
        
        # Process feeds
        await rss_manager.process_feeds(feeds)
        
        logger.info("RSS Parser service completed successfully")
        
    except Exception as e:
        logger.error(f"RSS Parser service failed: {str(e)}")
        raise


async def process_single_feed(feed_url: str, user_id: Optional[str] = None) -> dict:
    """Process a single RSS feed."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = get_config()
    
    # Validate URL
    if not validate_url(feed_url):
        raise RSSParserError(f"Invalid RSS feed URL: {feed_url}")
    
    # Initialize services
    rss_parser_token = os.getenv("RSS_PARSER_TOKEN", "")
    if not rss_parser_token:
        logger.warning("RSS_PARSER_TOKEN environment variable not set")
    
    api_client = APIClient(
        base_url=os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001"),
        token=rss_parser_token,
        service_id="firefeed-rss-parser-single",
        timeout=float(os.getenv("FIREFEED_TIMEOUT", "30.0")),
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    rss_fetcher = RSSFetcher(
        timeout=float(os.getenv("FIREFEED_FETCH_TIMEOUT", "15.0")),
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    rss_parser = RSSParser(
        timeout=10.0,
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    media_extractor = MediaExtractor(
        timeout=15.0,
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    duplicate_detector = DuplicateDetector(
        timeout=5.0,
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    rss_storage = RSSStorage(
        timeout=30.0,
        max_retries=int(os.getenv("FIREFEED_MAX_RETRIES", "3"))
    )
    
    rss_manager = RSSManager(
        fetcher=rss_fetcher,
        parser=rss_parser,
        media_extractor=media_extractor,
        duplicate_detector=duplicate_detector,
        storage=rss_storage,
        max_concurrent_feeds=1
    )
    
    # Create feed object
    feed = {
        'url': feed_url,
        'user_id': user_id
    }
    
    # Process the feed
    result = await rss_manager.process_feeds([feed])
    
    logger.info(f"Successfully processed feed: {feed_url}")
    return result


if __name__ == "__main__":
    asyncio.run(main())