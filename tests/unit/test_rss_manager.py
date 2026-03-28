"""Test RSS manager for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from firefeed_rss_parser.services.rss_manager import RSSManager
from firefeed_rss_parser.services.rss_fetcher import RSSFetcher
from firefeed_rss_parser.services.rss_parser import RSSParser
from firefeed_rss_parser.services.rss_storage import RSSStorage
from firefeed_rss_parser.services.media_extractor import MediaExtractor
from firefeed_rss_parser.services.duplicate_detector import DuplicateDetector
from firefeed_rss_parser.models import RSSFeed, RSSItem, Category


class TestRSSManager:
    """Test cases for RSS Manager."""

    @pytest.fixture
    def mock_fetcher(self):
        """Create mock RSS fetcher."""
        return AsyncMock(spec=RSSFetcher)

    @pytest.fixture
    def mock_parser(self):
        """Create mock RSS parser."""
        return AsyncMock(spec=RSSParser)

    @pytest.fixture
    def mock_storage(self):
        """Create mock RSS storage."""
        return AsyncMock(spec=RSSStorage)

    @pytest.fixture
    def mock_media_extractor(self):
        """Create mock media extractor."""
        return AsyncMock(spec=MediaExtractor)

    @pytest.fixture
    def mock_duplicate_detector(self):
        """Create mock duplicate detector."""
        return AsyncMock(spec=DuplicateDetector)

    @pytest.fixture
    def rss_manager(self, mock_fetcher, mock_parser, mock_storage, mock_media_extractor, mock_duplicate_detector):
        """Create RSS manager instance for testing."""
        return RSSManager(
            fetcher=mock_fetcher,
            parser=mock_parser,
            storage=mock_storage,
            media_extractor=mock_media_extractor,
            duplicate_detector=mock_duplicate_detector
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_parsed_data(self):
        """Create sample parsed RSS data."""
        return {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": datetime.now(timezone.utc),
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
    async def test_process_feed_success(self, rss_manager, sample_feed, sample_parsed_data):
        """Test successful feed processing."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.fetcher.fetch_rss.assert_called_once_with(sample_feed.url)
        rss_manager.parser.parse_rss.assert_called_once_with("<rss>...</rss>")
        rss_manager.duplicate_detector.is_duplicate.assert_called_once_with(sample_parsed_data["guid"])
        rss_manager.media_extractor.extract_media.assert_called_once_with(sample_parsed_data["link"])
        rss_manager.storage.save_rss_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_feed_duplicate_item(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with duplicate item."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = True

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.fetcher.fetch_rss.assert_called_once_with(sample_feed.url)
        rss_manager.parser.parse_rss.assert_called_once_with("<rss>...</rss>")
        rss_manager.duplicate_detector.is_duplicate.assert_called_once_with(sample_parsed_data["guid"])
        # Media extraction and storage should not be called for duplicates
        rss_manager.media_extractor.extract_media.assert_not_called()
        rss_manager.storage.save_rss_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_feed_fetch_error(self, rss_manager, sample_feed):
        """Test feed processing with fetch error."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.side_effect = Exception("Network error")

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is False
        rss_manager.fetcher.fetch_rss.assert_called_once_with(sample_feed.url)
        # Parser should not be called if fetch fails
        rss_manager.parser.parse_rss.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_feed_parse_error(self, rss_manager, sample_feed):
        """Test feed processing with parse error."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.side_effect = Exception("Parse error")

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is False
        rss_manager.fetcher.fetch_rss.assert_called_once_with(sample_feed.url)
        rss_manager.parser.parse_rss.assert_called_once_with("<rss>...</rss>")

    @pytest.mark.asyncio
    async def test_process_feed_storage_error(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with storage error."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.side_effect = Exception("Database error")

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is False
        rss_manager.storage.save_rss_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_feed_with_no_media(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with no media content."""
        # Remove media from sample data
        sample_parsed_data.pop("media", None)
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = None
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert saved_item.media_url is None
        assert saved_item.media_type is None

    @pytest.mark.asyncio
    async def test_process_feed_with_invalid_pub_date(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with invalid publication date."""
        # Set invalid pub_date
        sample_parsed_data["pub_date"] = None
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert saved_item.pub_date is not None  # Should use current time as fallback

    @pytest.mark.asyncio
    async def test_process_feed_with_empty_content(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with empty content."""
        # Set empty content
        sample_parsed_data["content"] = ""
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert saved_item.content == ""  # Empty content should be preserved

    @pytest.mark.asyncio
    async def test_process_feed_with_long_title(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with very long title."""
        # Set very long title
        sample_parsed_data["title"] = "A" * 1000
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert len(saved_item.title) == 1000  # Full title should be preserved

    @pytest.mark.asyncio
    async def test_process_feed_with_special_characters(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with special characters in content."""
        # Set special characters
        sample_parsed_data["title"] = "Test with special chars: ñáéíóú"
        sample_parsed_data["description"] = "Test with HTML: <b>bold</b> & <i>italic</i>"
        sample_parsed_data["content"] = "Test with Unicode: 🚀🔥✨"
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert "ñáéíóú" in saved_item.title
        assert "<b>bold</b>" in saved_item.description
        assert "🚀" in saved_item.content

    @pytest.mark.asyncio
    async def test_process_feed_with_missing_optional_fields(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with missing optional fields."""
        # Remove optional fields
        sample_parsed_data.pop("author", None)
        sample_parsed_data.pop("guid", None)
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process feed
        result = await rss_manager.process_feed(sample_feed)

        # Verify results
        assert result is True
        rss_manager.storage.save_rss_item.assert_called_once()
        saved_item = rss_manager.storage.save_rss_item.call_args[0][0]
        assert saved_item.author is None
        assert saved_item.guid is None

    @pytest.mark.asyncio
    async def test_process_feed_concurrent(self, rss_manager, sample_feed, sample_parsed_data):
        """Test concurrent processing of multiple feeds."""
        import asyncio
        
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Create multiple feeds
        feeds = [sample_feed for _ in range(3)]
        
        # Process feeds concurrently
        tasks = [rss_manager.process_feed(feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        for result in results:
            assert result is True
        
        # Verify that all feeds were processed
        assert rss_manager.fetcher.fetch_rss.call_count == 3
        assert rss_manager.parser.parse_rss.call_count == 3
        assert rss_manager.storage.save_rss_item.call_count == 3

    @pytest.mark.asyncio
    async def test_process_feed_with_rate_limiting(self, rss_manager, sample_feed, sample_parsed_data):
        """Test feed processing with rate limiting considerations."""
        # Setup mocks
        rss_manager.fetcher.fetch_rss.return_value = "<rss>...</rss>"
        rss_manager.parser.parse_rss.return_value = sample_parsed_data
        rss_manager.duplicate_detector.is_duplicate.return_value = False
        rss_manager.media_extractor.extract_media.return_value = sample_parsed_data["media"]
        rss_manager.storage.save_rss_item.return_value = 1

        # Process same feed multiple times
        for _ in range(3):
            result = await rss_manager.process_feed(sample_feed)
            assert result is True

        # Verify that fetcher was called multiple times (no internal rate limiting)
        assert rss_manager.fetcher.fetch_rss.call_count == 3
        assert rss_manager.parser.parse_rss.call_count == 3