"""Integration tests for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from firefeed_rss_parser.main import main, process_feed, process_all_feeds
from firefeed_rss_parser.services.rss_manager import RSSManager
from firefeed_rss_parser.services.rss_fetcher import RSSFetcher
from firefeed_rss_parser.services.rss_parser import RSSParser
from firefeed_rss_parser.services.rss_storage import RSSStorage
from firefeed_rss_parser.services.media_extractor import MediaExtractor
from firefeed_rss_parser.services.duplicate_detector import DuplicateDetector
from firefeed_rss_parser.models import RSSFeed, RSSItem, Category


class TestIntegration:
    """Integration test cases for RSS Parser service."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for integration testing."""
        return {
            'fetcher': AsyncMock(spec=RSSFetcher),
            'parser': AsyncMock(spec=RSSParser),
            'storage': AsyncMock(spec=RSSStorage),
            'media_extractor': AsyncMock(spec=MediaExtractor),
            'duplicate_detector': AsyncMock(spec=DuplicateDetector)
        }

    @pytest.fixture
    def rss_manager(self, mock_services):
        """Create RSS manager with mock services."""
        return RSSManager(
            fetcher=mock_services['fetcher'],
            parser=mock_services['parser'],
            storage=mock_services['storage'],
            media_extractor=mock_services['media_extractor'],
            duplicate_detector=mock_services['duplicate_detector']
        )

    @pytest.fixture
    def sample_feed(self):
        """Create sample RSS feed for testing."""
        return RSSFeed(
            id=1,
            name="Test Feed",
            url="https://example.com/rss",
            category_id=1,
            is_active=True,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )

    @pytest.fixture
    def sample_parsed_data(self):
        """Create sample parsed RSS data."""
        return {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": {
                "url": "https://example.com/image.jpg",
                "type": "image",
                "title": "Test Image",
                "description": "Test image description"
            }
        }

    @pytest.mark.asyncio
    async def test_full_feed_processing_pipeline(self, mock_services, rss_manager, sample_feed, sample_parsed_data):
        """Test the complete feed processing pipeline."""
        # Setup mocks
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = sample_parsed_data
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['media_extractor'].extract_media.return_value = sample_parsed_data["media"]
        mock_services['storage'].save_rss_item.return_value = 1

        # Process feed
        result = await process_feed(sample_feed, rss_manager)

        # Verify complete pipeline execution
        assert result is True
        mock_services['fetcher'].fetch_rss.assert_called_once_with(sample_feed.url)
        mock_services['parser'].parse_rss.assert_called_once_with("<rss>...</rss>")
        mock_services['duplicate_detector'].is_duplicate.assert_called_once_with(sample_parsed_data["guid"])
        mock_services['media_extractor'].extract_media.assert_called_once_with(sample_parsed_data["link"])
        mock_services['storage'].save_rss_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_feeds_processing(self, mock_services, rss_manager):
        """Test processing multiple feeds concurrently."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        # Setup mocks for all feeds
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": None
        }
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['media_extractor'].extract_media.return_value = None
        mock_services['storage'].save_rss_item.return_value = 1

        # Process all feeds
        results = await process_all_feeds(feeds, rss_manager)

        # Verify all feeds were processed successfully
        assert len(results) == 3
        assert all(result is True for result in results)
        
        # Verify service calls
        assert mock_services['fetcher'].fetch_rss.call_count == 3
        assert mock_services['parser'].parse_rss.call_count == 3
        assert mock_services['duplicate_detector'].is_duplicate.call_count == 3
        assert mock_services['storage'].save_rss_item.call_count == 3

    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self, mock_services, rss_manager, sample_feed):
        """Test error handling throughout the processing pipeline."""
        # Test fetch error
        mock_services['fetcher'].fetch_rss.side_effect = Exception("Network error")
        
        result = await process_feed(sample_feed, rss_manager)
        assert result is False
        
        # Test parse error
        mock_services['fetcher'].fetch_rss.side_effect = None
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.side_effect = Exception("Parse error")
        
        result = await process_feed(sample_feed, rss_manager)
        assert result is False
        
        # Test storage error
        mock_services['parser'].parse_rss.side_effect = None
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": None
        }
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['storage'].save_rss_item.side_effect = Exception("Database error")
        
        result = await process_feed(sample_feed, rss_manager)
        assert result is False

    @pytest.mark.asyncio
    async def test_duplicate_detection_integration(self, mock_services, rss_manager, sample_feed, sample_parsed_data):
        """Test duplicate detection integration."""
        # Setup mocks
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = sample_parsed_data
        mock_services['duplicate_detector'].is_duplicate.return_value = True  # Duplicate found

        # Process feed
        result = await process_feed(sample_feed, rss_manager)

        # Verify duplicate was detected and processing stopped
        assert result is True  # Processing considered successful even with duplicate
        mock_services['fetcher'].fetch_rss.assert_called_once_with(sample_feed.url)
        mock_services['parser'].parse_rss.assert_called_once_with("<rss>...</rss>")
        mock_services['duplicate_detector'].is_duplicate.assert_called_once_with(sample_parsed_data["guid"])
        
        # Media extraction and storage should not be called for duplicates
        mock_services['media_extractor'].extract_media.assert_not_called()
        mock_services['storage'].save_rss_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_extraction_integration(self, mock_services, rss_manager, sample_feed, sample_parsed_data):
        """Test media extraction integration."""
        # Setup mocks with media
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = sample_parsed_data
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['media_extractor'].extract_media.return_value = sample_parsed_data["media"]
        mock_services['storage'].save_rss_item.return_value = 1

        # Process feed
        result = await process_feed(sample_feed, rss_manager)

        # Verify media extraction was called
        assert result is True
        mock_services['media_extractor'].extract_media.assert_called_once_with(sample_parsed_data["link"])
        mock_services['storage'].save_rss_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_media_extraction_integration(self, mock_services, rss_manager, sample_feed):
        """Test processing without media extraction."""
        # Setup mocks without media
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": None
        }
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['media_extractor'].extract_media.return_value = None
        mock_services['storage'].save_rss_item.return_value = 1

        # Process feed
        result = await process_feed(sample_feed, rss_manager)

        # Verify processing completed without media
        assert result is True
        mock_services['storage'].save_rss_item.assert_called_once()
        saved_item = mock_services['storage'].save_rss_item.call_args[0][0]
        assert saved_item.media_url is None
        assert saved_item.media_type is None

    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, mock_services, rss_manager):
        """Test concurrent processing performance with many feeds."""
        import time
        
        # Create many feeds
        feeds = [
            RSSFeed(id=i, name=f"Feed {i}", url=f"https://example.com/rss{i}", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
            for i in range(50)
        ]
        
        # Setup mocks
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": None
        }
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['storage'].save_rss_item.return_value = 1

        # Measure processing time
        start_time = time.time()
        results = await process_all_feeds(feeds, rss_manager)
        end_time = time.time()

        # Verify all feeds were processed
        assert len(results) == 50
        assert all(result is True for result in results)
        
        # Verify service call counts
        assert mock_services['fetcher'].fetch_rss.call_count == 50
        assert mock_services['parser'].parse_rss.call_count == 50
        assert mock_services['duplicate_detector'].is_duplicate.call_count == 50
        assert mock_services['storage'].save_rss_item.call_count == 50
        
        # Should complete relatively quickly due to concurrency
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete in under 5 seconds

    @pytest.mark.asyncio
    async def test_mixed_feed_types_processing(self, mock_services, rss_manager):
        """Test processing different types of feeds (RSS, Atom, etc.)."""
        feeds = [
            RSSFeed(id=1, name="RSS Feed", url="https://example.com/rss", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Atom Feed", url="https://example.com/atom", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="JSON Feed", url="https://example.com/json", category_id=3, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        # Setup mocks to return different parsed data for each feed type
        def mock_parse_rss(rss_content):
            if "rss" in rss_content:
                return {
                    "title": "RSS Article",
                    "link": "https://example.com/rss-article",
                    "description": "RSS description",
                    "pub_date": "2023-01-01T00:00:00Z",
                    "content": "RSS content",
                    "author": "RSS Author",
                    "guid": "rss-guid-123",
                    "media": None
                }
            elif "atom" in rss_content:
                return {
                    "title": "Atom Article",
                    "link": "https://example.com/atom-article",
                    "description": "Atom description",
                    "pub_date": "2023-01-01T00:00:00Z",
                    "content": "Atom content",
                    "author": "Atom Author",
                    "guid": "atom-guid-123",
                    "media": None
                }
            else:
                return {
                    "title": "JSON Article",
                    "link": "https://example.com/json-article",
                    "description": "JSON description",
                    "pub_date": "2023-01-01T00:00:00Z",
                    "content": "JSON content",
                    "author": "JSON Author",
                    "guid": "json-guid-123",
                    "media": None
                }
        
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.side_effect = mock_parse_rss
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['storage'].save_rss_item.return_value = 1

        # Process all feeds
        results = await process_all_feeds(feeds, rss_manager)

        # Verify all feeds were processed successfully
        assert len(results) == 3
        assert all(result is True for result in results)
        
        # Verify each feed type was processed
        assert mock_services['parser'].parse_rss.call_count == 3
        assert mock_services['storage'].save_rss_item.call_count == 3

    @pytest.mark.asyncio
    async def test_error_recovery_in_concurrent_processing(self, mock_services, rss_manager):
        """Test error recovery when some feeds fail in concurrent processing."""
        feeds = [
            RSSFeed(id=1, name="Good Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Bad Feed", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Good Feed 2", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        # Setup mocks with one failing feed
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
            "author": "Test Author",
            "guid": "test-guid-123",
            "media": None
        }
        mock_services['duplicate_detector'].is_duplicate.return_value = False
        mock_services['storage'].save_rss_item.return_value = 1
        
        # Make the second feed fail
        async def mock_process_feed(feed):
            if feed.id == 2:
                raise Exception("Feed processing failed")
            return await process_feed(feed, rss_manager)
        
        # Process feeds with custom error handling
        tasks = [mock_process_feed(feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        assert len(results) == 3
        assert results[0] is True  # First feed succeeded
        assert isinstance(results[1], Exception)  # Second feed failed
        assert results[2] is True  # Third feed succeeded