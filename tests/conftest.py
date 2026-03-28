"""Test configuration and fixtures for RSS Parser service."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from firefeed_rss_parser.models import RSSFeed, RSSItem, Category


@pytest.fixture
def sample_feed():
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
def sample_item():
    """Create sample RSS item for testing."""
    return RSSItem(
        title="Test Article",
        link="https://example.com/article",
        description="Test description",
        pub_date=datetime.now(timezone.utc),
        rss_feed_id=1,
        content="Test content",
        guid="test-guid-123",
        media_url="https://example.com/image.jpg",
        media_type="image",
        media_title="Test Image",
        media_description="Test image description"
    )


@pytest.fixture
def sample_category():
    """Create sample category for testing."""
    return Category(
        id=1,
        name="Technology",
        description="Technology news",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_parsed_data():
    """Create sample parsed RSS data for testing."""
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


@pytest.fixture
def mock_rss_manager():
    """Create mock RSS manager for testing."""
    return AsyncMock()


@pytest.fixture
def mock_api_client():
    """Create mock API client for testing."""
    return AsyncMock()


@pytest.fixture
def mock_fetcher():
    """Create mock RSS fetcher for testing."""
    return AsyncMock()


@pytest.fixture
def mock_parser():
    """Create mock RSS parser for testing."""
    return AsyncMock()


@pytest.fixture
def mock_storage():
    """Create mock RSS storage for testing."""
    return AsyncMock()


@pytest.fixture
def mock_media_extractor():
    """Create mock media extractor for testing."""
    return AsyncMock()


@pytest.fixture
def mock_duplicate_detector():
    """Create mock duplicate detector for testing."""
    return AsyncMock()


@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "api_base_url": "http://localhost:8000",
        "api_key": "test-api-key",
        "timeout": 30.0,
        "max_retries": 3,
        "retry_delay": 1.0
    }


@pytest.fixture
def sample_rss_content():
    """Create sample RSS content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <description>Test RSS feed description</description>
            <link>https://example.com</link>
            <language>en</language>
            <pubDate>Mon, 01 Jan 2023 00:00:00 GMT</pubDate>
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
def sample_atom_content():
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


@pytest.fixture
def sample_html_content():
    """Create sample HTML content for media extraction testing."""
    return """
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


@pytest.fixture
def sample_media_content():
    """Create sample media content for testing."""
    return {
        "url": "https://example.com/image.jpg",
        "type": "image",
        "title": "Test Image",
        "description": "Test image description"
    }


@pytest.fixture
def sample_feeds_list():
    """Create sample list of feeds for testing."""
    return [
        RSSFeed(
            id=1,
            name="Feed 1",
            url="https://example.com/rss1",
            category_id=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        RSSFeed(
            id=2,
            name="Feed 2",
            url="https://example.com/rss2",
            category_id=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        RSSFeed(
            id=3,
            name="Feed 3",
            url="https://example.com/rss3",
            category_id=2,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def sample_items_list():
    """Create sample list of items for testing."""
    return [
        RSSItem(
            title="Item 1",
            link="https://example.com/item1",
            description="Item 1 description",
            pub_date=datetime.now(timezone.utc),
            rss_feed_id=1,
            content="Item 1 content",
            guid="guid-1"
        ),
        RSSItem(
            title="Item 2",
            link="https://example.com/item2",
            description="Item 2 description",
            pub_date=datetime.now(timezone.utc),
            rss_feed_id=1,
            content="Item 2 content",
            guid="guid-2"
        ),
        RSSItem(
            title="Item 3",
            link="https://example.com/item3",
            description="Item 3 description",
            pub_date=datetime.now(timezone.utc),
            rss_feed_id=2,
            content="Item 3 content",
            guid="guid-3"
        )
    ]


@pytest.fixture
def sample_categories_list():
    """Create sample list of categories for testing."""
    return [
        Category(
            id=1,
            name="Technology",
            description="Technology news",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        ),
        Category(
            id=2,
            name="Science",
            description="Science news",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        ),
        Category(
            id=3,
            name="Sports",
            description="Sports news",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def mock_http_response():
    """Create mock HTTP response for testing."""
    class MockResponse:
        def __init__(self, status_code=200, text="", json_data=None):
            self.status_code = status_code
            self.text = text
            self._json_data = json_data or {}
        
        def json(self):
            return self._json_data
    
    return MockResponse


@pytest.fixture
def mock_async_http_response():
    """Create mock async HTTP response for testing."""
    class MockAsyncResponse:
        def __init__(self, status_code=200, text="", json_data=None):
            self.status_code = status_code
            self.text = text
            self._json_data = json_data or {}
        
        async def json(self):
            return self._json_data
    
    return MockAsyncResponse


# Test markers for categorizing tests
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.fast = pytest.mark.fast


# Custom pytest configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "fast: mark test as fast running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test file names."""
    for item in items:
        # Add unit marker to tests in unit test directories
        if "test_" in item.name and "_unit" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration test directories
        if "test_" in item.name and "_integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if "performance" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add fast marker to tests that should be fast
        if "simple" in item.name or "basic" in item.name:
            item.add_marker(pytest.mark.fast)