"""
Tests for data models in FireFeed RSS Parser microservice.
"""

import pytest
from datetime import datetime, timezone
from firefeed_rss_parser.models import (
    RSSFeed, RSSItem, MediaItem, ProcessingResult,
    HealthStatus, DuplicateCheckResult, TranslationResult,
    MediaType, ProcessingStatus, TranslationRequest
)


class TestRSSFeed:
    """Test RSSFeed model."""
    
    def test_rss_feed_creation(self):
        """Test RSSFeed creation with all fields."""
        feed = RSSFeed(
            id=1,
            url="https://example.com/feed.xml",
            name="Test Feed",
            language="en",
            source_id=1,
            category_id=1,
            is_active=True
        )
        
        assert feed.id == 1
        assert feed.url == "https://example.com/feed.xml"
        assert feed.name == "Test Feed"
        assert feed.language == "en"
        assert feed.source_id == 1
        assert feed.category_id == 1
        assert feed.is_active is True
        assert feed.source == "source_1"
        assert feed.category == "category_1"
    
    def test_rss_feed_defaults(self):
        """Test RSSFeed default values."""
        feed = RSSFeed(
            id=1,
            url="https://example.com/feed.xml",
            name="Test Feed",
            language="en",
            source_id=1,
            category_id=1,
            is_active=True
        )
        
        assert feed.cooldown_minutes == 60
        assert feed.max_news_per_hour == 10
        assert isinstance(feed.created_at, datetime)
        assert isinstance(feed.updated_at, datetime)
    
    def test_rss_feed_properties(self):
        """Test RSSFeed computed properties."""
        feed = RSSFeed(
            id=1,
            url="https://example.com/feed.xml",
            name="Test Feed",
            language="en",
            source_id=123,
            category_id=456,
            is_active=True
        )
        
        assert feed.source == "source_123"
        assert feed.category == "category_456"


class TestRSSItem:
    """Test RSSItem model."""
    
    def test_rss_item_creation(self):
        """Test RSSItem creation with all fields."""
        item = RSSItem(
            id="test-news-id",
            title="Test News Title",
            content="Test content",
            link="https://example.com/news",
            language="en",
            category="news",
            source="test-source",
            feed_id=1
        )
        
        assert item.id == "test-news-id"
        assert item.title == "Test News Title"
        assert item.content == "Test content"
        assert item.link == "https://example.com/news"
        assert item.language == "en"
        assert item.category == "news"
        assert item.source == "test-source"
        assert item.feed_id == 1
        assert isinstance(item.published, datetime)
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
    
    def test_rss_item_optional_fields(self):
        """Test RSSItem optional fields."""
        item = RSSItem(
            id="test-news-id",
            title="Test News Title",
            content="Test content",
            link="https://example.com/news",
            language="en",
            category="news",
            source="test-source",
            feed_id=1,
            image_filename="test-image.jpg",
            video_filename="test-video.mp4"
        )
        
        assert item.image_filename == "test-image.jpg"
        assert item.video_filename == "test-video.mp4"


class TestMediaItem:
    """Test MediaItem model."""
    
    def test_media_item_creation(self):
        """Test MediaItem creation."""
        media = MediaItem(
            type=MediaType.IMAGE,
            original_url="https://example.com/image.jpg",
            processed_url="https://example.com/processed/image.jpg",
            filename="image.jpg"
        )
        
        assert media.type == MediaType.IMAGE
        assert media.original_url == "https://example.com/image.jpg"
        assert media.processed_url == "https://example.com/processed/image.jpg"
        assert media.filename == "image.jpg"
    
    def test_media_item_optional_fields(self):
        """Test MediaItem optional fields."""
        media = MediaItem(
            type=MediaType.VIDEO,
            original_url="https://example.com/video.mp4",
            processed_url="https://example.com/processed/video.mp4",
            filename="video.mp4",
            size=1024000,
            width=1920,
            height=1080,
            format="mp4",
            quality="720p"
        )
        
        assert media.size == 1024000
        assert media.width == 1920
        assert media.height == 1080
        assert media.format == "mp4"
        assert media.quality == "720p"


class TestProcessingResult:
    """Test ProcessingResult model."""
    
    def test_processing_result_creation(self):
        """Test ProcessingResult creation."""
        result = ProcessingResult(
            feed_id=1,
            feed_name="Test Feed",
            items_processed=10,
            items_created=8,
            items_updated=2,
            duplicates_found=0,
            media_processed=5
        )
        
        assert result.feed_id == 1
        assert result.feed_name == "Test Feed"
        assert result.items_processed == 10
        assert result.items_created == 8
        assert result.items_updated == 2
        assert result.duplicates_found == 0
        assert result.media_processed == 5
        assert result.status == ProcessingStatus.COMPLETED
        assert isinstance(result.started_at, datetime)
        assert result.completed_at is None
    
    def test_processing_result_with_errors(self):
        """Test ProcessingResult with errors."""
        errors = ["Error 1", "Error 2"]
        result = ProcessingResult(
            feed_id=1,
            feed_name="Test Feed",
            items_processed=5,
            items_created=3,
            items_updated=1,
            duplicates_found=1,
            media_processed=2,
            errors=errors,
            duration_seconds=2.5,
            status=ProcessingStatus.FAILED
        )
        
        assert result.errors == errors
        assert result.duration_seconds == 2.5
        assert result.status == ProcessingStatus.FAILED


class TestHealthStatus:
    """Test HealthStatus model."""
    
    def test_health_status_creation(self):
        """Test HealthStatus creation."""
        dependencies = {
            "api": {"healthy": True, "status": "ok"},
            "database": {"healthy": True, "status": "ok"}
        }
        
        metrics = {
            "check_count": 100,
            "error_count": 5,
            "uptime_seconds": 3600.0
        }
        
        errors = ["Warning message"]
        
        status = HealthStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            uptime_seconds=3600.0,
            dependencies=dependencies,
            metrics=metrics,
            errors=errors
        )
        
        assert status.status == "healthy"
        assert status.version == "0.1.0"
        assert status.uptime_seconds == 3600.0
        assert status.dependencies == dependencies
        assert status.metrics == metrics
        assert status.errors == errors
    
    def test_health_status_defaults(self):
        """Test HealthStatus default values."""
        status = HealthStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            uptime_seconds=0.0
        )
        
        assert status.dependencies == {}
        assert status.metrics == {}
        assert status.errors == []


class TestDuplicateCheckResult:
    """Test DuplicateCheckResult model."""
    
    def test_duplicate_check_result_creation(self):
        """Test DuplicateCheckResult creation."""
        duplicate_info = {
            "news_id": "duplicate-id",
            "title": "Duplicate Title",
            "similarity": 0.95
        }
        
        result = DuplicateCheckResult(
            is_duplicate=True,
            similarity_score=0.95,
            duplicate_info=duplicate_info,
            duration_seconds=0.1
        )
        
        assert result.is_duplicate is True
        assert result.similarity_score == 0.95
        assert result.duplicate_info == duplicate_info
        assert result.duration_seconds == 0.1
    
    def test_duplicate_check_result_no_duplicate(self):
        """Test DuplicateCheckResult for non-duplicate."""
        result = DuplicateCheckResult(
            is_duplicate=False,
            similarity_score=0.0,
            duplicate_info=None,
            duration_seconds=0.05
        )
        
        assert result.is_duplicate is False
        assert result.similarity_score == 0.0
        assert result.duplicate_info is None
        assert result.duration_seconds == 0.05


class TestTranslationResult:
    """Test TranslationResult model."""
    
    def test_translation_result_creation(self):
        """Test TranslationResult creation."""
        result = TranslationResult(
            original_text="Hello world",
            translated_text="Привет мир",
            source_lang="en",
            target_lang="ru",
            confidence=0.95,
            duration_seconds=0.5
        )
        
        assert result.original_text == "Hello world"
        assert result.translated_text == "Привет мир"
        assert result.source_lang == "en"
        assert result.target_lang == "ru"
        assert result.confidence == 0.95
        assert result.duration_seconds == 0.5


class TestTranslationRequest:
    """Test TranslationRequest model."""
    
    def test_translation_request_creation(self):
        """Test TranslationRequest creation."""
        context = {"domain": "news", "style": "formal"}
        
        request = TranslationRequest(
            text="Hello world",
            source_lang="en",
            target_lang="ru",
            context=context
        )
        
        assert request.text == "Hello world"
        assert request.source_lang == "en"
        assert request.target_lang == "ru"
        assert request.context == context
    
    def test_translation_request_without_context(self):
        """Test TranslationRequest without context."""
        request = TranslationRequest(
            text="Hello world",
            source_lang="en",
            target_lang="ru"
        )
        
        assert request.text == "Hello world"
        assert request.source_lang == "en"
        assert request.target_lang == "ru"
        assert request.context is None


class TestEnums:
    """Test enum values."""
    
    def test_media_type_enum(self):
        """Test MediaType enum values."""
        assert MediaType.IMAGE.value == "image"
        assert MediaType.VIDEO.value == "video"
        assert MediaType.NONE.value == "none"
    
    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"