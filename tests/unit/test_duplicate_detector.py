"""Test duplicate detector for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from firefeed_rss_parser.services.duplicate_detector import DuplicateDetector
from firefeed_rss_parser.models import RSSItem


class TestDuplicateDetector:
    """Test cases for Duplicate Detector."""

    @pytest.fixture
    def duplicate_detector(self):
        """Create duplicate detector instance for testing."""
        return DuplicateDetector()

    @pytest.fixture
    def sample_item(self):
        """Create sample RSS item for testing."""
        return RSSItem(
            news_id="test-news-id",
            original_title="Test Article",
            original_content="Test content",
            original_language="en",
            rss_feed_id=1,
            source_url="https://example.com/article",
            pub_date=datetime.fromisoformat("2023-01-01T00:00:00Z").replace(tzinfo=timezone.utc),
            guid="test-guid-123"
        )

    @pytest.mark.asyncio
    async def test_is_duplicate_with_guid(self, duplicate_detector, sample_item):
        """Test duplicate detection using GUID."""
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid:
            mock_check_guid.return_value = True
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is True
            mock_check_guid.assert_called_once_with(sample_item.guid)

    @pytest.mark.asyncio
    async def test_is_duplicate_with_link(self, duplicate_detector, sample_item):
        """Test duplicate detection using link when GUID is not available."""
        sample_item.guid = None
        
        with patch.object(duplicate_detector, '_check_link_duplicate') as mock_check_link:
            mock_check_link.return_value = True
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is True
            mock_check_link.assert_called_once_with(sample_item.link)

    @pytest.mark.asyncio
    async def test_is_duplicate_with_title(self, duplicate_detector, sample_item):
        """Test duplicate detection using title when GUID and link are not available."""
        sample_item.guid = None
        sample_item.link = None
        
        with patch.object(duplicate_detector, '_check_title_duplicate') as mock_check_title:
            mock_check_title.return_value = True
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is True
            mock_check_title.assert_called_once_with(sample_item.title)

    @pytest.mark.asyncio
    async def test_is_duplicate_no_duplicates_found(self, duplicate_detector, sample_item):
        """Test when no duplicates are found."""
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid:
            mock_check_guid.return_value = False
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is False
            mock_check_guid.assert_called_once_with(sample_item.guid)

    @pytest.mark.asyncio
    async def test_check_guid_duplicate_found(self, duplicate_detector):
        """Test GUID duplicate detection when duplicate is found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {
                "data": [
                    {
                        "id": 1,
                        "title": "Test Article",
                        "link": "https://example.com/article",
                        "guid": "test-guid-123"
                    }
                ]
            }
            
            result = await duplicate_detector._check_guid_duplicate("test-guid-123")
            
            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_guid_duplicate_not_found(self, duplicate_detector):
        """Test GUID duplicate detection when duplicate is not found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {"data": []}
            
            result = await duplicate_detector._check_guid_duplicate("test-guid-123")
            
            assert result is False
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_link_duplicate_found(self, duplicate_detector):
        """Test link duplicate detection when duplicate is found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {
                "data": [
                    {
                        "id": 1,
                        "title": "Test Article",
                        "link": "https://example.com/article",
                        "guid": "test-guid-123"
                    }
                ]
            }
            
            result = await duplicate_detector._check_link_duplicate("https://example.com/article")
            
            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_link_duplicate_not_found(self, duplicate_detector):
        """Test link duplicate detection when duplicate is not found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {"data": []}
            
            result = await duplicate_detector._check_link_duplicate("https://example.com/article")
            
            assert result is False
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_title_duplicate_found(self, duplicate_detector):
        """Test title duplicate detection when duplicate is found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {
                "data": [
                    {
                        "id": 1,
                        "title": "Test Article",
                        "link": "https://example.com/article",
                        "guid": "test-guid-123"
                    }
                ]
            }
            
            result = await duplicate_detector._check_title_duplicate("Test Article")
            
            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_title_duplicate_not_found(self, duplicate_detector):
        """Test title duplicate detection when duplicate is not found."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.return_value = {"data": []}
            
            result = await duplicate_detector._check_title_duplicate("Test Article")
            
            assert result is False
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_guid_duplicate_api_error(self, duplicate_detector):
        """Test GUID duplicate detection with API error."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.side_effect = Exception("API Error")
            
            result = await duplicate_detector._check_guid_duplicate("test-guid-123")
            
            assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_check_link_duplicate_api_error(self, duplicate_detector):
        """Test link duplicate detection with API error."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.side_effect = Exception("API Error")
            
            result = await duplicate_detector._check_link_duplicate("https://example.com/article")
            
            assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_check_title_duplicate_api_error(self, duplicate_detector):
        """Test title duplicate detection with API error."""
        with patch('firefeed_core.api_client.client.APIClient') as mock_api_client:
            mock_client = AsyncMock()
            mock_api_client.return_value = mock_client
            
            mock_client.get.side_effect = Exception("API Error")
            
            result = await duplicate_detector._check_title_duplicate("Test Article")
            
            assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_is_duplicate_with_empty_guid(self, duplicate_detector, sample_item):
        """Test duplicate detection with empty GUID."""
        sample_item.guid = ""
        
        with patch.object(duplicate_detector, '_check_link_duplicate') as mock_check_link:
            mock_check_link.return_value = False
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is False
            mock_check_link.assert_called_once_with(sample_item.link)

    @pytest.mark.asyncio
    async def test_is_duplicate_with_empty_link(self, duplicate_detector, sample_item):
        """Test duplicate detection with empty link."""
        sample_item.link = ""
        
        with patch.object(duplicate_detector, '_check_title_duplicate') as mock_check_title:
            mock_check_title.return_value = False
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is False
            mock_check_title.assert_called_once_with(sample_item.title)

    @pytest.mark.asyncio
    async def test_is_duplicate_with_none_values(self, duplicate_detector, sample_item):
        """Test duplicate detection with None values."""
        sample_item.guid = None
        sample_item.link = None
        
        with patch.object(duplicate_detector, '_check_title_duplicate') as mock_check_title:
            mock_check_title.return_value = False
            
            result = await duplicate_detector.is_duplicate(sample_item)
            
            assert result is False
            mock_check_title.assert_called_once_with(sample_item.title)

    @pytest.mark.asyncio
    async def test_is_duplicate_with_special_characters(self, duplicate_detector):
        """Test duplicate detection with special characters."""
        item_with_special_chars = RSSItem(
            news_id="special-news-id",
            original_title="Test Article with ñáéíóú and 🚀",
            original_content="Test content",
            original_language="en",
            rss_feed_id=1,
            source_url="https://example.com/article-special",
            pub_date=datetime.fromisoformat("2023-01-01T00:00:00Z").replace(tzinfo=timezone.utc),
            guid="test-guid-special"
        )
        
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid:
            mock_check_guid.return_value = True
            
            result = await duplicate_detector.is_duplicate(item_with_special_chars)
            
            assert result is True
            mock_check_guid.assert_called_once_with("test-guid-special")

    @pytest.mark.asyncio
    async def test_is_duplicate_with_long_title(self, duplicate_detector):
        """Test duplicate detection with very long title."""
        long_title = "A" * 1000
        item_with_long_title = RSSItem(
            news_id="long-news-id",
            original_title=long_title,
            original_content="Test content",
            original_language="en",
            rss_feed_id=1,
            source_url="https://example.com/article-long",
            pub_date=datetime.fromisoformat("2023-01-01T00:00:00Z").replace(tzinfo=timezone.utc),
            guid="test-guid-long"
        )
        
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid:
            mock_check_guid.return_value = True
            
            result = await duplicate_detector.is_duplicate(item_with_long_title)
            
            assert result is True
            mock_check_guid.assert_called_once_with("test-guid-long")

    @pytest.mark.asyncio
    async def test_is_duplicate_concurrent_requests(self, duplicate_detector, sample_item):
        """Test concurrent duplicate detection requests."""
        import asyncio
        
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid:
            mock_check_guid.return_value = False
            
            # Create multiple concurrent requests
            tasks = [
                duplicate_detector.is_duplicate(sample_item),
                duplicate_detector.is_duplicate(sample_item),
                duplicate_detector.is_duplicate(sample_item)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert result is False
            
            # Verify that all requests were made
            assert mock_check_guid.call_count == 3

    @pytest.mark.asyncio
    async def test_is_duplicate_mixed_detection_methods(self, duplicate_detector):
        """Test duplicate detection with different detection methods."""
        items = [
            RSSItem(news_id="item1", original_title="Item 1", original_content="content1", original_language="en", rss_feed_id=1, source_url="https://example.com/item1", guid="guid1"),
            RSSItem(news_id="item2", original_title="Item 2", original_content="content2", original_language="en", rss_feed_id=1, source_url="https://example.com/item2", guid=None),
            RSSItem(news_id="item3", original_title="Item 3", original_content="content3", original_language="en", rss_feed_id=1, source_url=None, guid=None)
        ]
        
        with patch.object(duplicate_detector, '_check_guid_duplicate') as mock_check_guid, \
             patch.object(duplicate_detector, '_check_link_duplicate') as mock_check_link, \
             patch.object(duplicate_detector, '_check_title_duplicate') as mock_check_title:
            
            mock_check_guid.return_value = False
            mock_check_link.return_value = False
            mock_check_title.return_value = False
            
            results = await asyncio.gather(
                duplicate_detector.is_duplicate(items[0]),
                duplicate_detector.is_duplicate(items[1]),
                duplicate_detector.is_duplicate(items[2])
            )
            
            # All should return False (no duplicates)
            for result in results:
                assert result is False
            
            # Verify correct methods were called
            mock_check_guid.assert_called_once_with("guid1")
            mock_check_link.assert_called_once_with("https://example.com/item2")
            mock_check_title.assert_called_once_with("Item 3")