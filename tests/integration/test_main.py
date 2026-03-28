"""Test main module for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from firefeed_rss_parser.main import main, process_feed, process_all_feeds
from firefeed_rss_parser.services.rss_manager import RSSManager
from firefeed_rss_parser.models import RSSFeed, Category


class TestMain:
    """Test cases for main module."""

    @pytest.fixture
    def mock_rss_manager(self):
        """Create mock RSS manager."""
        return AsyncMock(spec=RSSManager)

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
    def sample_category(self):
        """Create sample category for testing."""
        return Category(
            id=1,
            name="Technology",
            description="Technology news",
            is_active=True,
            created_at="2023-01-01T00:00:00Z"
        )

    @pytest.mark.asyncio
    async def test_process_feed_success(self, mock_rss_manager, sample_feed):
        """Test successful feed processing."""
        mock_rss_manager.process_feed.return_value = True
        
        result = await process_feed(sample_feed, mock_rss_manager)
        
        assert result is True
        mock_rss_manager.process_feed.assert_called_once_with(sample_feed)

    @pytest.mark.asyncio
    async def test_process_feed_failure(self, mock_rss_manager, sample_feed):
        """Test feed processing failure."""
        mock_rss_manager.process_feed.return_value = False
        
        result = await process_feed(sample_feed, mock_rss_manager)
        
        assert result is False
        mock_rss_manager.process_feed.assert_called_once_with(sample_feed)

    @pytest.mark.asyncio
    async def test_process_feed_exception(self, mock_rss_manager, sample_feed):
        """Test feed processing with exception."""
        mock_rss_manager.process_feed.side_effect = Exception("Processing error")
        
        result = await process_feed(sample_feed, mock_rss_manager)
        
        assert result is False
        mock_rss_manager.process_feed.assert_called_once_with(sample_feed)

    @pytest.mark.asyncio
    async def test_process_all_feeds_success(self, mock_rss_manager):
        """Test successful processing of all feeds."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_mixed_results(self, mock_rss_manager):
        """Test processing of all feeds with mixed results."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        # Mock different results for each feed
        mock_rss_manager.process_feed.side_effect = [True, False, True]
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert results == [True, False, True]
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_with_exceptions(self, mock_rss_manager):
        """Test processing of all feeds with some exceptions."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        # Mock exceptions for some feeds
        mock_rss_manager.process_feed.side_effect = [
            True,
            Exception("Processing error"),
            True
        ]
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert results[0] is True
        assert results[1] is False  # Exception should result in False
        assert results[2] is True
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_empty_list(self, mock_rss_manager):
        """Test processing of empty feeds list."""
        results = await process_all_feeds([], mock_rss_manager)
        
        assert len(results) == 0
        mock_rss_manager.process_feed.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_all_feeds_single_feed(self, mock_rss_manager):
        """Test processing of single feed."""
        feeds = [RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")]
        
        mock_rss_manager.process_feed.return_value = True
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 1
        assert results[0] is True
        mock_rss_manager.process_feed.assert_called_once_with(feeds[0])

    @pytest.mark.asyncio
    async def test_process_all_feeds_concurrent_processing(self, mock_rss_manager):
        """Test concurrent processing of multiple feeds."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        # Process feeds concurrently
        tasks = [process_feed(feed, mock_rss_manager) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert result is True
        
        # Verify that all feeds were processed
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_with_inactive_feeds(self, mock_rss_manager):
        """Test processing of feeds with some inactive feeds."""
        feeds = [
            RSSFeed(id=1, name="Active Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Inactive Feed", url="https://example.com/rss2", category_id=1, is_active=False, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="Active Feed 2", url="https://example.com/rss3", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        # Note: The current implementation processes all feeds regardless of is_active status
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_with_duplicate_feeds(self, mock_rss_manager):
        """Test processing of feeds with duplicate entries."""
        feeds = [
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),  # Duplicate
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_rss_manager.process_feed.call_count == 3

    @pytest.mark.asyncio
    async def test_process_all_feeds_with_invalid_feeds(self, mock_rss_manager):
        """Test processing of feeds with invalid feed objects."""
        # Create feeds with missing required fields
        feeds = [
            RSSFeed(id=1, name="Valid Feed", url="https://example.com/rss1", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            None,  # Invalid feed
            RSSFeed(id=2, name="Another Valid Feed", url="https://example.com/rss2", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        # This should handle the None feed gracefully
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        # The None feed should result in an exception being caught and False returned
        assert results[0] is True
        assert results[1] is False  # None feed should fail
        assert results[2] is True
        assert mock_rss_manager.process_feed.call_count == 2  # Only valid feeds should be processed

    @pytest.mark.asyncio
    async def test_process_all_feeds_performance(self, mock_rss_manager):
        """Test performance of processing many feeds."""
        import time
        
        # Create many feeds
        feeds = [
            RSSFeed(id=i, name=f"Feed {i}", url=f"https://example.com/rss{i}", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
            for i in range(100)
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        start_time = time.time()
        results = await process_all_feeds(feeds, mock_rss_manager)
        end_time = time.time()
        
        assert len(results) == 100
        assert all(result is True for result in results)
        assert mock_rss_manager.process_feed.call_count == 100
        
        # Should complete relatively quickly since it's concurrent
        processing_time = end_time - start_time
        assert processing_time < 10.0  # Should complete in under 10 seconds

    @pytest.mark.asyncio
    async def test_process_all_feeds_with_mixed_feed_types(self, mock_rss_manager):
        """Test processing of feeds with different types and configurations."""
        feeds = [
            RSSFeed(id=1, name="RSS Feed", url="https://example.com/rss", category_id=1, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=2, name="Atom Feed", url="https://example.com/atom", category_id=2, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            RSSFeed(id=3, name="JSON Feed", url="https://example.com/json", category_id=3, is_active=True, created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        
        mock_rss_manager.process_feed.return_value = True
        
        results = await process_all_feeds(feeds, mock_rss_manager)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_rss_manager.process_feed.call_count == 3