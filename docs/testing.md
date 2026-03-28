# FireFeed RSS Parser - Testing Guide

This document provides comprehensive testing guidelines for the FireFeed RSS Parser microservice.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Testing Tools](#testing-tools)
- [Test Data Management](#test-data-management)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The FireFeed RSS Parser follows a comprehensive testing strategy with multiple testing levels:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows
- **Performance Tests** - Test under load
- **Security Tests** - Test security measures

### Testing Philosophy

- **Test-Driven Development (TDD)** - Write tests before implementation
- **High Coverage** - Aim for 90%+ code coverage
- **Fast Feedback** - Quick test execution for rapid development
- **Reliable Tests** - Tests should be deterministic and stable
- **Maintainable Tests** - Easy to understand and update

## Test Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Global test configuration and fixtures
├── test_api_client.py       # API client tests
├── test_rss_manager.py      # RSS manager tests
├── test_rss_fetcher.py      # RSS fetcher tests
├── test_rss_parser.py       # RSS parser tests
├── test_rss_storage.py      # RSS storage tests
├── test_media_extractor.py  # Media extractor tests
├── test_duplicate_detector.py # Duplicate detector tests
├── test_main.py             # Main module tests
├── test_integration.py      # Integration tests
└── README.md               # Test documentation
```

### Test Naming Conventions

- **Files:** `test_*.py` or `*_test.py`
- **Classes:** `Test*` prefix
- **Methods:** `test_*` prefix
- **Fixtures:** `fixture_*` or descriptive names

## Unit Testing

### RSS Fetcher Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from firefeed_rss_parser.services.rss_fetcher import RSSFetcher
from exceptions.base_exceptions import NetworkError, ValidationError


class TestRSSFetcher:
    """Test cases for RSS Fetcher service."""
    
    @pytest.fixture
    def rss_fetcher(self):
        """Create RSS fetcher instance for testing."""
        return RSSFetcher()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<rss>...</rss>"
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
    async def test_fetch_rss_http_error(self, rss_fetcher):
        """Test RSS feed fetching with HTTP error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("HTTP Error")
            
            with pytest.raises(Exception):
                await rss_fetcher.fetch_rss("https://example.com/rss")
    
    @pytest.mark.asyncio
    async def test_fetch_rss_invalid_url(self, rss_fetcher):
        """Test RSS feed fetching with invalid URL."""
        with pytest.raises(ValidationError):
            await rss_fetcher.fetch_rss("invalid-url")
```

### RSS Parser Tests

```python
import pytest
from unittest.mock import patch
from firefeed_rss_parser.services.rss_parser import RSSParser


class TestRSSParser:
    """Test cases for RSS Parser service."""
    
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
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>Test article description</description>
                    <pubDate>Mon, 01 Jan 2023 10:00:00 GMT</pubDate>
                    <guid>test-guid-123</guid>
                </item>
            </channel>
        </rss>"""
    
    @pytest.mark.asyncio
    async def test_parse_rss_success(self, rss_parser, sample_rss_content):
        """Test successful RSS content parsing."""
        result = await rss_parser.parse_rss(sample_rss_content)
        
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["link"] == "https://example.com/article"
        assert result["description"] == "Test article description"
        assert result["guid"] == "test-guid-123"
    
    @pytest.mark.asyncio
    async def test_parse_rss_invalid_content(self, rss_parser):
        """Test RSS parsing with invalid content."""
        invalid_content = "<invalid xml content>"
        
        result = await rss_parser.parse_rss(invalid_content)
        
        assert result is None
```

### Media Extractor Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from firefeed_rss_parser.services.media_extractor import MediaExtractor


class TestMediaExtractor:
    """Test cases for Media Extractor service."""
    
    @pytest.fixture
    def media_extractor(self):
        """Create media extractor instance for testing."""
        return MediaExtractor()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta property="og:title" content="Test Article">
                <meta property="og:image" content="https://example.com/image.jpg">
            </head>
            <body>
                <img src="https://example.com/body-image.jpg" alt="Body image">
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
            assert result["url"] == "https://example.com/image.jpg"
            assert result["type"] == "image"
            assert result["title"] == "Test Article"
```

## Integration Testing

### Full Pipeline Integration

```python
import pytest
from unittest.mock import AsyncMock, patch
from firefeed_rss_parser.main import process_feed
from firefeed_rss_parser.services.rss_manager import RSSManager
from firefeed_rss_parser.models import RSSFeed, RSSItem


class TestIntegration:
    """Integration test cases for RSS Parser service."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for integration testing."""
        return {
            'fetcher': AsyncMock(),
            'parser': AsyncMock(),
            'storage': AsyncMock(),
            'media_extractor': AsyncMock(),
            'duplicate_detector': AsyncMock()
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
            is_active=True
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
            "guid": "test-guid-123",
            "media": {
                "url": "https://example.com/image.jpg",
                "type": "image",
                "title": "Test Image",
                "description": "Test image description"
            }
        }
    
    @pytest.mark.asyncio
    async def test_full_feed_processing_pipeline(
        self, 
        mock_services, 
        rss_manager, 
        sample_feed, 
        sample_parsed_data
    ):
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
            RSSFeed(id=1, name="Feed 1", url="https://example.com/rss1", category_id=1, is_active=True),
            RSSFeed(id=2, name="Feed 2", url="https://example.com/rss2", category_id=1, is_active=True),
            RSSFeed(id=3, name="Feed 3", url="https://example.com/rss3", category_id=2, is_active=True)
        ]
        
        # Setup mocks for all feeds
        mock_services['fetcher'].fetch_rss.return_value = "<rss>...</rss>"
        mock_services['parser'].parse_rss.return_value = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "content": "Test content",
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
```

### API Integration Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from firefeed_core.api_client.client import APIClient


class TestAPIClient:
    """Test cases for FireFeed API client."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client instance for testing."""
        return APIClient(
            base_url="http://localhost:8000",
            token="test-api-key",
            service_id="test-service",
            timeout=30.0
        )
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 1,
                    "name": "Test Feed",
                    "url": "https://example.com/rss",
                    "category_id": 1
                }
            ],
            "total": 1,
            "page": 1,
            "size": 10
        }
        return mock_response
    
    @pytest.mark.asyncio
    async def test_get_rss_feeds_success(self, api_client, mock_response):
        """Test successful RSS feeds retrieval."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = mock_response
            
            feeds = await api_client.get_rss_feeds()
            
            assert len(feeds) == 1
            assert feeds[0]["name"] == "Test Feed"
            assert feeds[0]["url"] == "https://example.com/rss"
            assert feeds[0]["category_id"] == 1
    
    @pytest.mark.asyncio
    async def test_create_rss_item_success(self, api_client):
        """Test successful RSS item creation."""
        item_data = {
            "title": "Test Item",
            "link": "https://example.com/item",
            "description": "Test description",
            "pub_date": "2023-01-01T00:00:00Z",
            "rss_feed_id": 1,
            "content": "Test content"
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "title": "Test Item",
            "link": "https://example.com/item",
            "description": "Test description"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = mock_response
            
            result = await api_client.create_rss_item(item_data)
            
            assert result["id"] == 1
            assert result["title"] == "Test Item"
            assert result["link"] == "https://example.com/item"
```

## End-to-End Testing

### Complete Workflow Tests

```python
import pytest
import asyncio
from firefeed_rss_parser.main import main
from firefeed_rss_parser.config import config


class TestEndToEnd:
    """End-to-end test cases for RSS Parser service."""
    
    @pytest.mark.asyncio
    async def test_complete_service_workflow(self):
        """Test complete service workflow from start to finish."""
        # This would typically require a real FireFeed API instance
        # For now, we'll test with mocked dependencies
        
        # Configure test settings
        original_config = config.base_url
        config.base_url = "http://test-api:8000"
        
        try:
            # Start the service
            service_task = asyncio.create_task(main())
            
            # Wait for service to start
            await asyncio.sleep(2)
            
            # Test service is running (this would be more comprehensive in real E2E tests)
            assert True  # Placeholder for actual E2E validation
            
            # Stop the service
            service_task.cancel()
            await service_task
            
        finally:
            # Restore original config
            config.base_url = original_config
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling throughout the complete workflow."""
        # Test various error scenarios in the complete workflow
        # This would include network errors, parsing errors, storage errors, etc.
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_workflow(self):
        """Test concurrent processing of multiple feeds."""
        # Test that multiple feeds can be processed concurrently
        # without conflicts or resource issues
        pass
```

## Performance Testing

### Load Testing

```python
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from firefeed_rss_parser.services.rss_manager import RSSManager
from firefeed_rss_parser.models import RSSFeed


class TestPerformance:
    """Performance test cases for RSS Parser service."""
    
    @pytest.mark.asyncio
    async def test_concurrent_feed_processing_performance(self):
        """Test performance of concurrent feed processing."""
        # Create many test feeds
        feeds = [
            RSSFeed(
                id=i,
                name=f"Feed {i}",
                url=f"https://example.com/rss{i}",
                category_id=1,
                is_active=True
            )
            for i in range(100)
        ]
        
        # Measure processing time
        start_time = time.time()
        
        # Process feeds concurrently
        tasks = []
        for feed in feeds:
            task = process_feed(feed, rss_manager)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance requirements
        assert processing_time < 60  # Should complete in under 60 seconds
        assert sum(1 for result in results if result is True) > 80  # 80% success rate
        
        print(f"Processed {len(feeds)} feeds in {processing_time:.2f} seconds")
        print(f"Average time per feed: {processing_time/len(feeds):.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process many feeds
        feeds = [
            RSSFeed(
                id=i,
                name=f"Feed {i}",
                url=f"https://example.com/rss{i}",
                category_id=1,
                is_active=True
            )
            for i in range(50)
        ]
        
        tasks = [process_feed(feed, rss_manager) for feed in feeds]
        await asyncio.gather(*tasks)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase
        
        print(f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB")
        print(f"Memory increase: {memory_increase:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_network_performance(self):
        """Test network performance and timeout handling."""
        # Test with various network conditions
        # This would typically use tools like toxiproxy for network simulation
        pass
```

### Benchmarking

```python
import pytest
import time
from firefeed_rss_parser.services.rss_parser import RSSParser


class TestBenchmarking:
    """Benchmark test cases for RSS Parser service."""
    
    @pytest.mark.benchmark
    def test_rss_parsing_benchmark(self, benchmark):
        """Benchmark RSS parsing performance."""
        rss_parser = RSSParser()
        sample_content = self._generate_large_rss_content()
        
        def parse_rss():
            return rss_parser.parse_rss(sample_content)
        
        result = benchmark(parse_rss)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_media_extraction_benchmark(self, benchmark):
        """Benchmark media extraction performance."""
        media_extractor = MediaExtractor()
        sample_url = "https://example.com/article-with-media"
        
        def extract_media():
            return media_extractor.extract_media(sample_url)
        
        result = benchmark(extract_media)
        assert result is not None
    
    def _generate_large_rss_content(self):
        """Generate large RSS content for benchmarking."""
        items = []
        for i in range(1000):
            items.append(f"""
            <item>
                <title>Article {i}</title>
                <link>https://example.com/article{i}</link>
                <description>Article {i} description</description>
                <pubDate>Mon, 01 Jan 2023 {i%24:02d}:00:00 GMT</pubDate>
                <guid>guid-{i}</guid>
            </item>
            """)
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Large Test Feed</title>
                <description>Large RSS feed for benchmarking</description>
                <link>https://example.com</link>
                {''.join(items)}
            </channel>
        </rss>"""
```

## Testing Tools

### pytest Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --strict-config
    --strict-markers
    --cov=firefeed_rss_parser
    --cov-report=html
    --cov-report=term
    --cov-report=xml
    --cov-fail-under=90
    -v

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    fast: Fast running tests
    benchmark: Performance benchmark tests
    network: Tests requiring network access
```

### Test Fixtures

```python
# conftest.py
import pytest
from datetime import datetime, timezone
from firefeed_rss_parser.models import RSSFeed, RSSItem, MediaContent


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
        guid="test-guid-123"
    )


@pytest.fixture
def sample_media_content():
    """Create sample media content for testing."""
    return MediaContent(
        url="https://example.com/image.jpg",
        type="image",
        title="Test Image",
        description="Test image description"
    )


@pytest.fixture
def sample_parsed_data():
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


@pytest.fixture
async def mock_services():
    """Create mock services for testing."""
    from unittest.mock import AsyncMock
    
    return {
        'fetcher': AsyncMock(),
        'parser': AsyncMock(),
        'storage': AsyncMock(),
        'media_extractor': AsyncMock(),
        'duplicate_detector': AsyncMock()
    }
```

### Mocking Utilities

```python
# test_utils.py
from unittest.mock import AsyncMock, MagicMock
import pytest


def create_mock_response(status_code=200, text="", json_data=None):
    """Create a mock HTTP response."""
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.json.return_value = json_data or {}
    return mock_response


def create_mock_rss_content(title="Test Feed", items_count=5):
    """Create mock RSS content."""
    items = []
    for i in range(items_count):
        items.append(f"""
        <item>
            <title>{title} Article {i}</title>
            <link>https://example.com/article{i}</link>
            <description>Article {i} description</description>
            <pubDate>Mon, 01 Jan 2023 {i%24:02d}:00:00 GMT</pubDate>
            <guid>guid-{i}</guid>
        </item>
        """)
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>{title}</title>
            <description>{title} description</description>
            <link>https://example.com</link>
            {''.join(items)}
        </channel>
    </rss>"""


def create_mock_html_content(title="Test Article", has_og_image=True, has_body_image=True):
    """Create mock HTML content for media extraction."""
    og_image = ""
    if has_og_image:
        og_image = '<meta property="og:image" content="https://example.com/og-image.jpg">'
    
    body_image = ""
    if has_body_image:
        body_image = '<img src="https://example.com/body-image.jpg" alt="Body image">'
    
    return f"""
    <html>
        <head>
            <title>{title}</title>
            {og_image}
            <meta property="og:title" content="{title}">
            <meta property="og:description" content="Test description">
        </head>
        <body>
            {body_image}
            <p>Article content</p>
        </body>
    </html>
    """
```

## Test Data Management

### Test Data Factories

```python
# test_factories.py
from datetime import datetime, timezone
from firefeed_rss_parser.models import RSSFeed, RSSItem, MediaContent


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_rss_feed(
        id=1,
        name="Test Feed",
        url="https://example.com/rss",
        category_id=1,
        is_active=True
    ):
        """Create a test RSS feed."""
        return RSSFeed(
            id=id,
            name=name,
            url=url,
            category_id=category_id,
            is_active=is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def create_rss_item(
        title="Test Article",
        link="https://example.com/article",
        description="Test description",
        rss_feed_id=1,
        guid=None,
        content="Test content"
    ):
        """Create a test RSS item."""
        return RSSItem(
            title=title,
            link=link,
            description=description,
            pub_date=datetime.now(timezone.utc),
            rss_feed_id=rss_feed_id,
            content=content,
            guid=guid or link
        )
    
    @staticmethod
    def create_media_content(
        url="https://example.com/image.jpg",
        type="image",
        title="Test Image",
        description="Test image description"
    ):
        """Create test media content."""
        return MediaContent(
            url=url,
            type=type,
            title=title,
            description=description
        )
    
    @staticmethod
    def create_parsed_data(
        title="Test Article",
        link="https://example.com/article",
        description="Test description",
        guid="test-guid-123",
        media=None
    ):
        """Create test parsed data."""
        return {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": datetime.now(timezone.utc),
            "content": "Test content",
            "author": "Test Author",
            "guid": guid,
            "media": media or {
                "url": "https://example.com/image.jpg",
                "type": "image",
                "title": "Test Image",
                "description": "Test image description"
            }
        }
```

### Test Data Cleanup

```python
# test_cleanup.py
import pytest
import asyncio
from firefeed_rss_parser.services.rss_manager import RSSManager


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up resources after each test."""
    yield
    
    # Clean up any async resources
    await asyncio.sleep(0.1)  # Allow async operations to complete
    
    # Reset any global state if needed
    # RSSManager.reset_global_state()
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run linting
      run: |
        ruff check firefeed_rss_parser/
        mypy firefeed_rss_parser/
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=firefeed_rss_parser --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true
```

### Docker Testing

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  rss-parser-test:
    build:
      context: .
      target: development
    environment:
      - FIREFEED_API_BASE_URL=http://mock-api:8000
      - FIREFEED_API_KEY=test-key
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
      - /app/__pycache__
      - /app/.pytest_cache
    command: ["python", "-m", "pytest", "tests/", "-v", "-s", "--cov=firefeed_rss_parser"]
  
  mock-api:
    image: mockserver/mockserver:latest
    environment:
      - MOCKSERVER_PROPERTY_FILE=/config/application.properties
    volumes:
      - ./test-config:/config
    ports:
      - "8000:8080"
```

## Best Practices

### 1. Test Organization

- **Group related tests** in appropriate directories
- **Use descriptive test names** that explain what is being tested
- **Follow naming conventions** consistently
- **Separate unit, integration, and E2E tests**

### 2. Test Data

- **Use factories** for creating test data
- **Keep test data minimal** and focused
- **Use realistic test data** that represents real-world scenarios
- **Clean up test data** after tests complete

### 3. Mocking

- **Mock external dependencies** to isolate units under test
- **Use realistic mock responses** that match real API responses
- **Avoid over-mocking** - test real interactions when possible
- **Verify mock calls** to ensure expected interactions

### 4. Assertions

- **Use specific assertions** that clearly express expectations
- **Include meaningful error messages** in assertions
- **Test both success and failure cases**
- **Assert on behavior, not implementation details**

### 5. Performance

- **Keep unit tests fast** (< 1 second each)
- **Use integration tests sparingly** as they are slower
- **Run performance tests separately** from regular test suite
- **Monitor test execution time** and optimize slow tests

### 6. Maintenance

- **Update tests when code changes** to keep them relevant
- **Remove obsolete tests** that no longer test meaningful behavior
- **Refactor test code** for clarity and maintainability
- **Review test coverage** regularly and improve as needed

### 7. Documentation

- **Document complex test scenarios** with clear comments
- **Include examples** in test documentation
- **Explain test setup and teardown** when non-trivial
- **Document test data sources** and any special considerations

## Conclusion

Comprehensive testing is essential for maintaining code quality and reliability in the FireFeed RSS Parser service. By following these testing guidelines and best practices, you can ensure that your code is robust, maintainable, and ready for production use.

Regular testing, combined with code reviews and continuous integration, helps catch issues early and maintain high code quality throughout the development lifecycle.