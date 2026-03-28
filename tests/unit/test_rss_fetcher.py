"""Test RSS fetcher for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from firefeed_rss_parser.services.rss_fetcher import RSSFetcher


class TestRSSFetcher:
    """Test cases for RSS Fetcher."""

    @pytest.fixture
    def rss_fetcher(self):
        """Create RSS fetcher instance for testing."""
        return RSSFetcher()

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <description>Test RSS feed</description>
                <link>https://example.com</link>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>Test article description</description>
                    <pubDate>Mon, 01 Jan 2023 00:00:00 GMT</pubDate>
                    <guid>test-guid-123</guid>
                </item>
            </channel>
        </rss>"""
        return mock_response

    @pytest.mark.asyncio
    async def test_fetch_rss_success(self, rss_fetcher, mock_response):
        """Test successful RSS feed fetching."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_custom_headers(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with custom headers."""
        custom_headers = {
            "User-Agent": "Custom User Agent",
            "X-API-Key": "test-api-key"
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", headers=custom_headers)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers=custom_headers,
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_timeout(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with custom timeout."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", timeout=60.0)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=60.0
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_http_error(self, rss_fetcher):
        """Test RSS feed fetching with HTTP error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("HTTP Error")
            
            with pytest.raises(Exception):
                await rss_fetcher.fetch_rss("https://example.com/rss")

    @pytest.mark.asyncio
    async def test_fetch_rss_timeout_error(self, rss_fetcher):
        """Test RSS feed fetching with timeout error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            with pytest.raises(Exception):
                await rss_fetcher.fetch_rss("https://example.com/rss")

    @pytest.mark.asyncio
    async def test_fetch_rss_invalid_url(self, rss_fetcher):
        """Test RSS feed fetching with invalid URL."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Invalid URL")
            
            with pytest.raises(Exception):
                await rss_fetcher.fetch_rss("invalid-url")

    @pytest.mark.asyncio
    async def test_fetch_rss_empty_response(self, rss_fetcher):
        """Test RSS feed fetching with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == ""

    @pytest.mark.asyncio
    async def test_fetch_rss_non_xml_response(self, rss_fetcher):
        """Test RSS feed fetching with non-XML response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is not XML content"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == "This is not XML content"

    @pytest.mark.asyncio
    async def test_fetch_rss_with_query_params(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with query parameters."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss?param=value")
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss?param=value",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_https_url(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with HTTPS URL."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://secure.example.com/rss")
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://secure.example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_auth(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with authentication."""
        auth = ("username", "password")
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", auth=auth)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0,
                auth=auth
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_proxy(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with proxy."""
        proxies = {"http": "http://proxy.example.com:8080"}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", proxies=proxies)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0,
                proxies=proxies
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_cookies(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with cookies."""
        cookies = {"session": "test-session-id"}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", cookies=cookies)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0,
                cookies=cookies
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_redirects(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with redirects."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", allow_redirects=True)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0,
                allow_redirects=True
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_with_verify_ssl(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with SSL verification."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss", verify_ssl=False)
            
            assert result == mock_response.text
            mock_get.assert_called_once_with(
                "https://example.com/rss",
                headers={
                    "User-Agent": "FireFeed RSS Parser/1.0",
                    "Accept": "application/rss+xml, application/atom+xml, text/xml"
                },
                timeout=30.0,
                verify=False
            )

    @pytest.mark.asyncio
    async def test_fetch_rss_concurrent_requests(self, rss_fetcher, mock_response):
        """Test concurrent RSS feed fetching requests."""
        import asyncio
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = [
                rss_fetcher.fetch_rss("https://example.com/rss1"),
                rss_fetcher.fetch_rss("https://example.com/rss2"),
                rss_fetcher.fetch_rss("https://example.com/rss3")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert result == mock_response.text
            
            # Verify that all requests were made
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_rss_with_different_content_types(self, rss_fetcher):
        """Test RSS feed fetching with different content types."""
        content_types = [
            "application/rss+xml",
            "application/atom+xml", 
            "text/xml",
            "application/xml"
        ]
        
        for content_type in content_types:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = f"<{content_type.split('/')[-1]}>Test content</{content_type.split('/')[-1]}>"
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = mock_response
                
                result = await rss_fetcher.fetch_rss("https://example.com/rss")
                
                assert result == mock_response.text

    @pytest.mark.asyncio
    async def test_fetch_rss_with_encoding(self, rss_fetcher, mock_response):
        """Test RSS feed fetching with different encodings."""
        mock_response.text = "<?xml version='1.0' encoding='UTF-8'?><rss>Test content</rss>"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == mock_response.text

    @pytest.mark.asyncio
    async def test_fetch_rss_with_large_content(self, rss_fetcher):
        """Test RSS feed fetching with large content."""
        large_content = "<?xml version='1.0'?><rss>" + ("x" * 10000) + "</rss>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = large_content
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == large_content

    @pytest.mark.asyncio
    async def test_fetch_rss_with_special_characters(self, rss_fetcher):
        """Test RSS feed fetching with special characters."""
        special_content = "<?xml version='1.0'?><rss><title>Test with ñáéíóú and 🚀</title></rss>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = special_content
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == special_content

    @pytest.mark.asyncio
    async def test_fetch_rss_with_malformed_xml(self, rss_fetcher):
        """Test RSS feed fetching with malformed XML."""
        malformed_content = "<?xml version='1.0'?><rss><title>Test</title>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = malformed_content
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await rss_fetcher.fetch_rss("https://example.com/rss")
            
            assert result == malformed_content