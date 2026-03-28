#!/usr/bin/env python3
"""Test script to verify the fixes for firefeed-rss-parser."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import setup_logging, get_config
from services.rss_manager import RSSManager
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from services.rss_storage import RSSStorage
from firefeed_core.api_client.client import APIClient
from utils.validation import validate_url


async def test_rss_fetcher():
    """Test RSS fetcher with timeout handling."""
    print("Testing RSS Fetcher...")
    
    fetcher = RSSFetcher(timeout=30.0, max_retries=2)
    
    # Test with a valid URL
    test_url = "http://lenta.ru/rss/news"
    
    try:
        content = await fetcher.fetch_rss(test_url)
        print(f"✓ Successfully fetched RSS content from {test_url}")
        print(f"  Content length: {len(content)} characters")
        return True
    except Exception as e:
        print(f"✗ Failed to fetch RSS content: {e}")
        return False


async def test_rss_parser():
    """Test RSS parser with sample content."""
    print("\nTesting RSS Parser...")
    
    parser = RSSParser(timeout=10.0, max_retries=2)
    
    # Sample RSS content
    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <description>Test RSS feed</description>
            <link>https://example.com</link>
            <item>
                <title>Test Item</title>
                <description>This is a test item</description>
                <link>https://example.com/item1</link>
                <pubDate>Mon, 28 Dec 2025 10:00:00 GMT</pubDate>
                <guid>test-item-1</guid>
            </item>
        </channel>
    </rss>"""
    
    try:
        parsed = await parser.parse_rss(sample_rss)
        if parsed and 'items' in parsed:
            print(f"✓ Successfully parsed RSS content")
            print(f"  Items found: {len(parsed['items'])}")
            return True
        else:
            print("✗ Failed to parse RSS content - no items found")
            return False
    except Exception as e:
        print(f"✗ Failed to parse RSS content: {e}")
        return False


async def test_url_validation():
    """Test URL validation."""
    print("\nTesting URL Validation...")
    
    test_urls = [
        ("http://lenta.ru/rss/news", True),
        ("http://example.com/feed", True),
        ("invalid-url", False),
        ("", False),
        ("ftp://example.com", False)
    ]
    
    all_passed = True
    for url, expected in test_urls:
        result = validate_url(url)
        if result == expected:
            print(f"✓ URL validation for '{url}': {result}")
        else:
            print(f"✗ URL validation for '{url}': expected {expected}, got {result}")
            all_passed = False
    
    return all_passed


async def test_api_client():
    """Test API client initialization."""
    print("\nTesting API Client...")
    
    try:
        config = get_config()
        rss_parser_token = os.getenv("RSS_PARSER_TOKEN", "")
        
        api_client = APIClient(
            base_url=config.api_base_url,
            token=rss_parser_token,
            service_id="test-client",
            timeout=30.0,
            max_retries=3
        )
        
        print(f"✓ API client initialized successfully")
        print(f"  Base URL: {config.api_base_url}")
        print(f"  Token provided: {'Yes' if rss_parser_token else 'No'}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize API client: {e}")
        return False


async def test_rss_manager():
    """Test RSS manager with sample feeds."""
    print("\nTesting RSS Manager...")
    
    try:
        # Initialize services
        rss_fetcher = RSSFetcher(timeout=30.0, max_retries=3)
        rss_parser = RSSParser(timeout=10.0, max_retries=3)
        media_extractor = MediaExtractor(timeout=15.0, max_retries=3)
        duplicate_detector = DuplicateDetector(max_retries=3)
        rss_storage = RSSStorage(max_retries=3)
        
        rss_manager = RSSManager(
            fetcher=rss_fetcher,
            parser=rss_parser,
            media_extractor=media_extractor,
            duplicate_detector=duplicate_detector,
            storage=rss_storage,
            max_concurrent_feeds=2
        )
        
        # Test with sample feeds
        sample_feeds = [
            {
                'id': 1,
                'url': 'http://lenta.ru/rss/news',
                'name': 'Lenta news',
                'language': 'ru',
                'is_active': True
            }
        ]
        
        results = await rss_manager.process_feeds(sample_feeds)
        print(f"✓ RSS Manager processed feeds successfully")
        print(f"  Total feeds: {results['total_feeds']}")
        print(f"  Processed feeds: {results['processed_feeds']}")
        print(f"  Failed feeds: {results['failed_feeds']}")
        
        if results['errors']:
            print(f"  Errors: {results['errors']}")
        
        return True
    except Exception as e:
        print(f"✗ RSS Manager test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("FireFeed RSS Parser - Fix Verification Tests")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Run tests
    tests = [
        test_url_validation(),
        test_api_client(),
        test_rss_fetcher(),
        test_rss_parser(),
        test_rss_manager()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    
    passed = 0
    total = len(results)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Test {i+1}: FAILED - {result}")
        elif result:
            print(f"Test {i+1}: PASSED")
            passed += 1
        else:
            print(f"Test {i+1}: FAILED")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The fixes appear to be working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please review the issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)