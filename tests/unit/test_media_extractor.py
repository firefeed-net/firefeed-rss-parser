"""Test media extractor for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from firefeed_rss_parser.services.media_extractor import MediaExtractor
from firefeed_rss_parser.models import MediaContent


class TestMediaExtractor:
    """Test cases for Media Extractor."""

    @pytest.fixture
    def media_extractor(self):
        """Create media extractor instance for testing."""
        return MediaExtractor()

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:title" content="Test Article">
                <meta property="og:description" content="Test description">
                <meta property="og:image" content="https://example.com/image.jpg">
                <meta property="og:type" content="article">
                <meta name="twitter:card" content="summary_large_image">
                <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
                <video src="https://example.com/video.mp4"></video>
                <audio src="https://example.com/audio.mp3"></audio>
            </body>
        </html>
        """
        return mock_response

    @pytest.mark.asyncio
    async def test_extract_media_success(self, media_extractor, mock_response):
        """Test successful media extraction."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/image.jpg"
            assert result.type == "image"
            assert result.title == "Test Article"
            assert result.description == "Test description"

    @pytest.mark.asyncio
    async def test_extract_media_no_og_image(self, media_extractor):
        """Test media extraction with no OpenGraph image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:title" content="Test Article">
                <meta property="og:description" content="Test description">
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/body-image.jpg"
            assert result.type == "image"

    @pytest.mark.asyncio
    async def test_extract_media_no_media_found(self, media_extractor):
        """Test media extraction with no media found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Article</title>
            </head>
            <body>
                <p>No media content</p>
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_media_http_error(self, media_extractor):
        """Test media extraction with HTTP error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("HTTP Error")
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_media_timeout(self, media_extractor):
        """Test media extraction with timeout."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_media_video_content(self, media_extractor):
        """Test media extraction with video content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:type" content="video">
                <meta property="og:video" content="https://example.com/video.mp4">
            </head>
            <body>
                <video src="https://example.com/body-video.mp4"></video>
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/video.mp4"
            assert result.type == "video"

    @pytest.mark.asyncio
    async def test_extract_media_audio_content(self, media_extractor):
        """Test media extraction with audio content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:type" content="music">
                <meta property="og:audio" content="https://example.com/audio.mp3">
            </head>
            <body>
                <audio src="https://example.com/body-audio.mp3"></audio>
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/audio.mp3"
            assert result.type == "audio"

    @pytest.mark.asyncio
    async def test_extract_media_priority_order(self, media_extractor):
        """Test media extraction priority order."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="https://example.com/og-image.jpg">
                <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            # Should prioritize OpenGraph image over Twitter image and body images
            assert result.url == "https://example.com/og-image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_twitter_fallback(self, media_extractor):
        """Test media extraction with Twitter image as fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta name="twitter:card" content="summary_large_image">
                <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            # Should use Twitter image when OpenGraph is not available
            assert result.url == "https://example.com/twitter-image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_body_image_fallback(self, media_extractor):
        """Test media extraction with body image as fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Article</title>
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
                <img src="https://example.com/second-image.jpg" alt="Second image">
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            # Should use first body image when no OpenGraph or Twitter images
            assert result.url == "https://example.com/body-image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_invalid_url(self, media_extractor):
        """Test media extraction with invalid URL."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Invalid URL")
            
            result = await media_extractor.extract_media("invalid-url")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_media_empty_response(self, media_extractor):
        """Test media extraction with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_media_malformed_html(self, media_extractor):
        """Test media extraction with malformed HTML."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><img src='https://example.com/image.jpg'></body></html>"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_https_url(self, media_extractor):
        """Test media extraction with HTTPS URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="https://secure.example.com/image.jpg">
            </head>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://secure.example.com/article")
            
            assert result is not None
            assert result.url == "https://secure.example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_relative_image_url(self, media_extractor):
        """Test media extraction with relative image URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="/images/article-image.jpg">
            </head>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url == "https://example.com/images/article-image.jpg"

    @pytest.mark.asyncio
    async def test_extract_media_data_url(self, media_extractor):
        """Test media extraction with data URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==">
            </head>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert result.url.startswith("data:image/png;base64")

    @pytest.mark.asyncio
    async def test_extract_media_with_query_params(self, media_extractor):
        """Test media extraction with query parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="https://example.com/image.jpg?width=800&height=600">
            </head>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await media_extractor.extract_media("https://example.com/article")
            
            assert result is not None
            assert "width=800" in result.url
            assert "height=600" in result.url

    @pytest.mark.asyncio
    async def test_extract_media_concurrent_requests(self, media_extractor):
        """Test concurrent media extraction requests."""
        import asyncio
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:image" content="https://example.com/image.jpg">
            </head>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = [
                media_extractor.extract_media("https://example.com/article1"),
                media_extractor.extract_media("https://example.com/article2"),
                media_extractor.extract_media("https://example.com/article3")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert result is not None
                assert result.url == "https://example.com/image.jpg"
            
            # Verify that all requests were made
            assert mock_get.call_count == 3