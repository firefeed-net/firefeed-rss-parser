"""Test RSS storage for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from firefeed_rss_parser.services.rss_storage import RSSStorage
from firefeed_rss_parser.models import RSSItem


class TestRSSStorage:
    """Test cases for RSS Storage."""

    @pytest.fixture
    def rss_storage(self):
        """Create RSS storage instance for testing."""
        return RSSStorage()

    @pytest.fixture
    def sample_item(self):
        """Create sample RSS item for testing."""
        return RSSItem(
            title="Test Article",
            link="https://example.com/article",
            description="Test description",
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content="Test content",
            guid="test-guid-123",
            media_url="https://example.com/image.jpg",
            media_type="image",
            media_title="Test Image",
            media_description="Test image description"
        )

    @pytest.mark.asyncio
    async def test_save_rss_item_success(self, rss_storage, sample_item):
        """Test successful RSS item saving."""
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Test Article"}
            
            result = await rss_storage.save_rss_item(sample_item)
            
            assert result == 1
            mock_api_request.assert_called_once_with(
                "POST",
                "/api/v1/rss/items",
                json={
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "description": "Test description",
                    "pub_date": "2023-01-01T00:00:00Z",
                    "rss_feed_id": 1,
                    "content": "Test content",
                    "guid": "test-guid-123",
                    "media_url": "https://example.com/image.jpg",
                    "media_type": "image",
                    "media_title": "Test Image",
                    "media_description": "Test image description"
                }
            )

    @pytest.mark.asyncio
    async def test_save_rss_item_with_minimal_data(self, rss_storage):
        """Test RSS item saving with minimal required data."""
        minimal_item = RSSItem(
            title="Minimal Article",
            link="https://example.com/minimal",
            description="Minimal description",
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content="Minimal content"
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Minimal Article"}
            
            result = await rss_storage.save_rss_item(minimal_item)
            
            assert result == 1
            mock_api_request.assert_called_once_with(
                "POST",
                "/api/v1/rss/items",
                json={
                    "title": "Minimal Article",
                    "link": "https://example.com/minimal",
                    "description": "Minimal description",
                    "pub_date": "2023-01-01T00:00:00Z",
                    "rss_feed_id": 1,
                    "content": "Minimal content",
                    "guid": None,
                    "media_url": None,
                    "media_type": None,
                    "media_title": None,
                    "media_description": None
                }
            )

    @pytest.mark.asyncio
    async def test_save_rss_item_with_none_values(self, rss_storage):
        """Test RSS item saving with None values."""
        item_with_none = RSSItem(
            title=None,
            link=None,
            description=None,
            pub_date=None,
            rss_feed_id=None,
            content=None,
            guid=None,
            media_url=None,
            media_type=None,
            media_title=None,
            media_description=None
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": None}
            
            result = await rss_storage.save_rss_item(item_with_none)
            
            assert result == 1
            mock_api_request.assert_called_once_with(
                "POST",
                "/api/v1/rss/items",
                json={
                    "title": None,
                    "link": None,
                    "description": None,
                    "pub_date": None,
                    "rss_feed_id": None,
                    "content": None,
                    "guid": None,
                    "media_url": None,
                    "media_type": None,
                    "media_title": None,
                    "media_description": None
                }
            )

    @pytest.mark.asyncio
    async def test_save_rss_item_validation_error(self, rss_storage, sample_item):
        """Test RSS item saving with validation error."""
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.side_effect = Exception("Validation Error")
            
            with pytest.raises(Exception):
                await rss_storage.save_rss_item(sample_item)

    @pytest.mark.asyncio
    async def test_save_rss_item_duplicate_error(self, rss_storage, sample_item):
        """Test RSS item saving with duplicate error."""
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.side_effect = Exception("Duplicate Item")
            
            with pytest.raises(Exception):
                await rss_storage.save_rss_item(sample_item)

    @pytest.mark.asyncio
    async def test_save_rss_item_with_special_characters(self, rss_storage):
        """Test RSS item saving with special characters."""
        special_item = RSSItem(
            title="Test with ñáéíóú and 🚀",
            link="https://example.com/special",
            description="Test with HTML: <b>bold</b> & <i>italic</i>",
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content="Test with Unicode: 🚀🔥✨",
            guid="test-guid-special",
            media_url="https://example.com/special-image.jpg",
            media_type="image",
            media_title="Special Image",
            media_description="Special image description"
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Test with ñáéíóú and 🚀"}
            
            result = await rss_storage.save_rss_item(special_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert "ñáéíóú" in json_data["title"]
            assert "🚀" in json_data["title"]
            assert "<b>bold</b>" in json_data["description"]
            assert "🔥" in json_data["content"]

    @pytest.mark.asyncio
    async def test_save_rss_item_with_long_content(self, rss_storage):
        """Test RSS item saving with very long content."""
        long_content = "x" * 10000
        long_item = RSSItem(
            title="Long Article",
            link="https://example.com/long",
            description=long_content,
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content=long_content,
            guid="test-guid-long"
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Long Article"}
            
            result = await rss_storage.save_rss_item(long_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert json_data["description"] == long_content
            assert json_data["content"] == long_content

    @pytest.mark.asyncio
    async def test_save_rss_item_concurrent_requests(self, rss_storage, sample_item):
        """Test concurrent RSS item saving requests."""
        import asyncio
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Test Article"}
            
            # Create multiple concurrent requests
            tasks = [
                rss_storage.save_rss_item(sample_item),
                rss_storage.save_rss_item(sample_item),
                rss_storage.save_rss_item(sample_item)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert result == 1
            
            # Verify that all requests were made
            assert mock_api_request.call_count == 3

    @pytest.mark.asyncio
    async def test_save_rss_item_with_different_media_types(self, rss_storage):
        """Test RSS item saving with different media types."""
        media_types = ["image", "video", "audio", "document"]
        
        for media_type in media_types:
            item_with_media = RSSItem(
                title=f"Article with {media_type}",
                link=f"https://example.com/{media_type}",
                description=f"Article with {media_type} content",
                pub_date="2023-01-01T00:00:00Z",
                rss_feed_id=1,
                content=f"Article content with {media_type}",
                guid=f"test-guid-{media_type}",
                media_url=f"https://example.com/{media_type}.jpg",
                media_type=media_type,
                media_title=f"{media_type.title()} Title",
                media_description=f"{media_type.title()} description"
            )
            
            with patch.object(rss_storage, '_make_api_request') as mock_api_request:
                mock_api_request.return_value = {"id": 1, "title": f"Article with {media_type}"}
                
                result = await rss_storage.save_rss_item(item_with_media)
                
                assert result == 1
                mock_api_request.assert_called_once()
                call_args = mock_api_request.call_args
                json_data = call_args[1]['json']
                
                assert json_data["media_type"] == media_type
                assert json_data["media_url"] == f"https://example.com/{media_type}.jpg"

    @pytest.mark.asyncio
    async def test_save_rss_item_with_empty_strings(self, rss_storage):
        """Test RSS item saving with empty strings."""
        empty_item = RSSItem(
            title="",
            link="",
            description="",
            pub_date="",
            rss_feed_id=1,
            content="",
            guid="",
            media_url="",
            media_type="",
            media_title="",
            media_description=""
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": ""}
            
            result = await rss_storage.save_rss_item(empty_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert json_data["title"] == ""
            assert json_data["link"] == ""
            assert json_data["description"] == ""

    @pytest.mark.asyncio
    async def test_save_rss_item_with_unicode_content(self, rss_storage):
        """Test RSS item saving with Unicode content."""
        unicode_content = "测试内容 - Test content - Contenu de test - Testinhoud"
        unicode_item = RSSItem(
            title=unicode_content,
            link="https://example.com/unicode",
            description=unicode_content,
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content=unicode_content,
            guid="test-guid-unicode"
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": unicode_content}
            
            result = await rss_storage.save_rss_item(unicode_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert json_data["title"] == unicode_content
            assert json_data["description"] == unicode_content
            assert json_data["content"] == unicode_content

    @pytest.mark.asyncio
    async def test_save_rss_item_api_error_handling(self, rss_storage, sample_item):
        """Test RSS item saving with various API errors."""
        error_cases = [
            ("Connection Error", "Connection failed"),
            ("Timeout Error", "Request timeout"),
            ("Server Error", "Internal server error"),
            ("Network Error", "Network unavailable")
        ]
        
        for error_name, error_message in error_cases:
            with patch.object(rss_storage, '_make_api_request') as mock_api_request:
                mock_api_request.side_effect = Exception(error_message)
                
                with pytest.raises(Exception) as exc_info:
                    await rss_storage.save_rss_item(sample_item)
                
                assert str(exc_info.value) == error_message

    @pytest.mark.asyncio
    async def test_save_rss_item_with_base64_content(self, rss_storage):
        """Test RSS item saving with base64 encoded content."""
        import base64
        
        encoded_content = base64.b64encode(b"Test content").decode('utf-8')
        base64_item = RSSItem(
            title="Article with Base64",
            link="https://example.com/base64",
            description=encoded_content,
            pub_date="2023-01-01T00:00:00Z",
            rss_feed_id=1,
            content=encoded_content,
            guid="test-guid-base64"
        )
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Article with Base64"}
            
            result = await rss_storage.save_rss_item(base64_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert json_data["description"] == encoded_content
            assert json_data["content"] == encoded_content

    @pytest.mark.asyncio
    async def test_save_rss_item_with_null_feed_id(self, rss_storage, sample_item):
        """Test RSS item saving with null feed ID."""
        sample_item.rss_feed_id = None
        
        with patch.object(rss_storage, '_make_api_request') as mock_api_request:
            mock_api_request.return_value = {"id": 1, "title": "Test Article"}
            
            result = await rss_storage.save_rss_item(sample_item)
            
            assert result == 1
            mock_api_request.assert_called_once()
            call_args = mock_api_request.call_args
            json_data = call_args[1]['json']
            
            assert json_data["rss_feed_id"] is None