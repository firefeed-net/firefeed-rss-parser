"""Test RSS parser for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from firefeed_rss_parser.services.rss_parser import RSSParser


class TestRSSParser:
    """Test cases for RSS Parser."""

    @pytest.fixture
    def rss_parser(self):
        """Create RSS parser instance for testing."""
        return RSSParser()

    @pytest.fixture
    def sample_rss_content(self):
        """Create sample RSS content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <description>Test RSS feed description</description>
                <link>https://example.com</link>
                <language>en</language>
                <pubDate>Mon, 01 Jan 2023 00:00:00 GMT</pubDate>
                <lastBuildDate>Mon, 01 Jan 2023 12:00:00 GMT</lastBuildDate>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>Test article description</description>
                    <pubDate>Mon, 01 Jan 2023 10:00:00 GMT</pubDate>
                    <guid>test-guid-123</guid>
                    <author>Test Author</author>
                    <category>Technology</category>
                    <content:encoded>Test article content</content:encoded>
                    <enclosure url="https://example.com/image.jpg" type="image/jpeg" />
                </item>
            </channel>
        </rss>"""

    @pytest.fixture
    def sample_atom_content(self):
        """Create sample Atom content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Feed</title>
            <subtitle>Test Atom feed description</subtitle>
            <link href="https://example.com" />
            <updated>2023-01-01T12:00:00Z</updated>
            <id>https://example.com/feed</id>
            <entry>
                <title>Test Article</title>
                <link href="https://example.com/article" />
                <id>test-guid-123</id>
                <updated>2023-01-01T10:00:00Z</updated>
                <author>
                    <name>Test Author</name>
                </author>
                <category term="Technology" />
                <summary>Test article description</summary>
                <content type="html">Test article content</content>
                <media:content url="https://example.com/image.jpg" type="image/jpeg" />
            </entry>
        </feed>"""

    @pytest.mark.asyncio
    async def test_parse_rss_success(self, rss_parser, sample_rss_content):
        """Test successful RSS content parsing."""
        result = await rss_parser.parse_rss(sample_rss_content)
        
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["link"] == "https://example.com/article"
        assert result["description"] == "Test article description"
        assert result["pub_date"] is not None
        assert result["guid"] == "test-guid-123"
        assert result["author"] == "Test Author"
        assert result["content"] == "Test article content"
        assert result["media"] is not None
        assert result["media"]["url"] == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_parse_atom_success(self, rss_parser, sample_atom_content):
        """Test successful Atom content parsing."""
        result = await rss_parser.parse_rss(sample_atom_content)
        
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["link"] == "https://example.com/article"
        assert result["description"] == "Test article description"
        assert result["pub_date"] is not None
        assert result["guid"] == "test-guid-123"
        assert result["author"] == "Test Author"
        assert result["content"] == "Test article content"
        assert result["media"] is not None
        assert result["media"]["url"] == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_parse_rss_with_missing_fields(self, rss_parser):
        """Test RSS parsing with missing optional fields."""
        minimal_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Minimal Article</title>
                    <link>https://example.com/minimal</link>
                    <description>Minimal description</description>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(minimal_rss)
        
        assert result is not None
        assert result["title"] == "Minimal Article"
        assert result["link"] == "https://example.com/minimal"
        assert result["description"] == "Minimal description"
        assert result["pub_date"] is not None  # Should use current time as fallback
        assert result["guid"] is not None  # Should generate GUID from link
        assert result["author"] is None
        assert result["content"] is None
        assert result["media"] is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_empty_content(self, rss_parser):
        """Test RSS parsing with empty content."""
        empty_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title></title>
                    <link></link>
                    <description></description>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(empty_rss)
        
        assert result is not None
        assert result["title"] == ""
        assert result["link"] == ""
        assert result["description"] == ""
        assert result["pub_date"] is not None
        assert result["guid"] is not None
        assert result["author"] is None
        assert result["content"] is None
        assert result["media"] is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_special_characters(self, rss_parser):
        """Test RSS parsing with special characters."""
        special_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test with ñáéíóú and 🚀</title>
                    <link>https://example.com/special</link>
                    <description>Test with HTML: <b>bold</b> & <i>italic</i></description>
                    <content:encoded>Test with Unicode: 🚀🔥✨</content:encoded>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(special_rss)
        
        assert result is not None
        assert "ñáéíóú" in result["title"]
        assert "🚀" in result["title"]
        assert "<b>bold</b>" in result["description"]
        assert "🔥" in result["content"]

    @pytest.mark.asyncio
    async def test_parse_rss_with_multiple_items(self, rss_parser):
        """Test RSS parsing with multiple items."""
        multi_item_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>First Article</title>
                    <link>https://example.com/first</link>
                    <description>First article description</description>
                </item>
                <item>
                    <title>Second Article</title>
                    <link>https://example.com/second</link>
                    <description>Second article description</description>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(multi_item_rss)
        
        # Should return the first item
        assert result is not None
        assert result["title"] == "First Article"
        assert result["link"] == "https://example.com/first"

    @pytest.mark.asyncio
    async def test_parse_rss_with_invalid_xml(self, rss_parser):
        """Test RSS parsing with invalid XML."""
        invalid_xml = "<invalid xml content>"
        
        result = await rss_parser.parse_rss(invalid_xml)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_empty_string(self, rss_parser):
        """Test RSS parsing with empty string."""
        result = await rss_parser.parse_rss("")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_none(self, rss_parser):
        """Test RSS parsing with None input."""
        result = await rss_parser.parse_rss(None)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_malformed_xml(self, rss_parser):
        """Test RSS parsing with malformed XML."""
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <!-- Missing closing tags -->
        """
        
        result = await rss_parser.parse_rss(malformed_xml)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_rss_with_different_date_formats(self, rss_parser):
        """Test RSS parsing with different date formats."""
        date_formats = [
            "Mon, 01 Jan 2023 10:00:00 GMT",
            "2023-01-01T10:00:00Z",
            "01 Jan 2023 10:00:00 +0000",
            "2023-01-01 10:00:00"
        ]
        
        for date_format in date_formats:
            rss_with_date = f"""<?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <item>
                        <title>Test Article</title>
                        <link>https://example.com/article</link>
                        <pubDate>{date_format}</pubDate>
                    </item>
                </channel>
            </rss>"""
            
            result = await rss_parser.parse_rss(rss_with_date)
            
            assert result is not None
            assert result["pub_date"] is not None

    @pytest.mark.asyncio
    async def test_parse_rss_with_base64_content(self, rss_parser):
        """Test RSS parsing with base64 encoded content."""
        import base64
        
        encoded_content = base64.b64encode(b"Test content").decode('utf-8')
        rss_with_base64 = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>{encoded_content}</description>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(rss_with_base64)
        
        assert result is not None
        assert result["description"] == encoded_content  # Should not decode automatically

    @pytest.mark.asyncio
    async def test_parse_rss_with_cdata(self, rss_parser):
        """Test RSS parsing with CDATA sections."""
        rss_with_cdata = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title><![CDATA[Test Article]]></title>
                    <description><![CDATA[<b>Test</b> description with HTML]]></description>
                    <content:encoded><![CDATA[<p>Full article content</p>]]></content:encoded>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(rss_with_cdata)
        
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["description"] == "<b>Test</b> description with HTML"
        assert result["content"] == "<p>Full article content</p>"

    @pytest.mark.asyncio
    async def test_parse_rss_with_namespaces(self, rss_parser):
        """Test RSS parsing with XML namespaces."""
        rss_with_namespaces = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <media:content url="https://example.com/image.jpg" type="image/jpeg" />
                    <content:encoded>Test article content</content:encoded>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(rss_with_namespaces)
        
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["link"] == "https://example.com/article"
        assert result["content"] == "Test article content"
        assert result["media"] is not None
        assert result["media"]["url"] == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_parse_rss_with_long_content(self, rss_parser):
        """Test RSS parsing with very long content."""
        long_content = "x" * 10000
        rss_with_long_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>{long_content}</description>
                    <content:encoded>{long_content}</content:encoded>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(rss_with_long_content)
        
        assert result is not None
        assert result["description"] == long_content
        assert result["content"] == long_content

    @pytest.mark.asyncio
    async def test_parse_rss_with_unicode_content(self, rss_parser):
        """Test RSS parsing with Unicode content."""
        unicode_content = "测试内容 - Test content - Contenu de test - Testinhoud"
        rss_with_unicode = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>{unicode_content}</title>
                    <link>https://example.com/unicode</link>
                    <description>{unicode_content}</description>
                </item>
            </channel>
        </rss>"""
        
        result = await rss_parser.parse_rss(rss_with_unicode)
        
        assert result is not None
        assert result["title"] == unicode_content
        assert result["description"] == unicode_content

    @pytest.mark.asyncio
    async def test_parse_rss_concurrent_requests(self, rss_parser, sample_rss_content):
        """Test concurrent RSS parsing requests."""
        import asyncio
        
        # Create multiple concurrent requests
        tasks = [
            rss_parser.parse_rss(sample_rss_content),
            rss_parser.parse_rss(sample_rss_content),
            rss_parser.parse_rss(sample_rss_content)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed
        for result in results:
            assert result is not None
            assert result["title"] == "Test Article"
            assert result["link"] == "https://example.com/article"

    @pytest.mark.asyncio
    async def test_parse_rss_with_different_encodings(self, rss_parser):
        """Test RSS parsing with different XML encodings."""
        encodings = ["UTF-8", "UTF-16", "ISO-8859-1"]
        
        for encoding in encodings:
            rss_with_encoding = f"""<?xml version="1.0" encoding="{encoding}"?>
            <rss version="2.0">
                <channel>
                    <item>
                        <title>Test Article</title>
                        <link>https://example.com/article</link>
                        <description>Test description</description>
                    </item>
                </channel>
            </rss>"""
            
            result = await rss_parser.parse_rss(rss_with_encoding)
            
            assert result is not None
            assert result["title"] == "Test Article"
            assert result["link"] == "https://example.com/article"
            assert result["description"] == "Test description"