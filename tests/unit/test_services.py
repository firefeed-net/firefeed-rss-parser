"""
Tests for services in FireFeed RSS Parser microservice.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from firefeed_core.api_client.client import APIClient
from firefeed_rss_parser.services import (
    MediaExtractor,
    DuplicateDetector,
    TranslationService,
    HealthChecker,
    RSSParserService
)
from firefeed_rss_parser.models import (
    RSSFeed, RSSItem, ProcessingResult,
    HealthStatus, DuplicateCheckResult, TranslationResult
)
from firefeed_rss_parser.exceptions import (
    ServiceUnavailableException, AuthenticationError, ValidationException,
    MediaProcessingError, DuplicateDetectionError, TranslationError
)


class TestAPIClient:
    """Test APIClient from firefeed_core."""
    
    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test API client initialization."""
        client = APIClient(
            base_url="http://test-api:8000",
            token="test-token",
            service_id="test-service"
        )
        
        assert client.base_url == "http://test-api:8000"
        assert client.token == "test-token"
        assert client.service_id == "test-service"
    
    @pytest.mark.asyncio
    async def test_api_client_headers(self):
        """Test API client headers generation."""
        client = APIClient(
            base_url="http://test-api:8000",
            token="test-token",
            service_id="test-service"
        )
        
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["X-Service-ID"] == "test-service"
        assert headers["Content-Type"] == "application/json"


class TestDuplicateDetector:
    """Test DuplicateDetector."""
    
    @pytest.mark.asyncio
    async def test_duplicate_detector_initialization(self):
        """Test duplicate detector initialization."""
        detector = DuplicateDetector()
        
        assert detector.api_client is not None


class TestTranslationService:
    """Test TranslationService."""
    
    @pytest.mark.asyncio
    async def test_translation_service_initialization(self):
        """Test translation service initialization."""
        service = TranslationService()
        
        assert service.api_client is None
        assert service.supported_languages == ['en', 'ru', 'de', 'fr', 'es', 'it', 'pt']