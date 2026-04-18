"""Duplicate detection service for RSS items."""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from firefeed_core.exceptions import ServiceUnavailableException, ValidationException
from utils.retry import retry_on_rate_limit
from firefeed_core.api_client.client import APIClient
from .redis_service import RedisService

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Service for detecting duplicate RSS items."""
    
    def __init__(self, api_client: Optional[APIClient] = None, redis_service: Optional[RedisService] = None):
        import os
        self.api_client = api_client or APIClient(
            base_url=os.getenv("API_BASE_URL", "http://localhost:8001"),
            token=os.getenv("FIREFEED_API_SERVICE_TOKEN", ""),
            service_id="rss-parser-duplicate-detector",
            timeout=30,
            max_retries=3
        )
        self.redis_service = redis_service
        self.semaphore = asyncio.Semaphore(2)  # Limit concurrent API calls to avoid rate limits
    
    async def is_duplicate(self, item_data: dict) -> bool:
        """Check if RSS item dict is duplicate.
        
        Raises:
            ValidationException: If item_data is invalid (None, non-dict, missing required fields)
        """
        # Check if duplicate detection is enabled
        from config.firefeed_rss_parser_config import get_config
        config = get_config()
        
        if not config.duplicate_detection_enabled:
            logger.debug("Duplicate detection is disabled, skipping check")
            return False
        
        if item_data is None:
            raise ValidationException("item_data cannot be None")
        if not isinstance(item_data, dict):
            raise ValidationException(f"item_data must be dict, got {type(item_data)}")
        if not item_data.get('news_id') or not item_data.get('source_url'):
            raise ValidationException(
                "Missing essential fields for duplicate check",
                details={
                    "has_news_id": bool(item_data.get('news_id')),
                    "has_source_url": bool(item_data.get('source_url'))
                }
            )
        news_id = item_data.get('news_id')

        cache_key = f"dup:{news_id}"

        # Cache check (only if redis_service is available)
        cached = None
        if self.redis_service is not None:
            try:
                cached = await self.redis_service.get(cache_key)
            except Exception as redis_exc:
                logger.debug(f"Redis cache check failed for {news_id}: {redis_exc}")

        if cached == "1":
            logger.debug(f"Cache HIT duplicate: {news_id}")
            return True
        if cached == "0":
            logger.debug(f"Cache MISS non-duplicate: {news_id}")
            return False

        # API composite check
        async with self.semaphore:
            try:
                params = {
                    "news_id": news_id,
                    "size": 1
                }
                params["source_url"] = item_data.get('source_url')
                original_title = item_data.get('original_title') or ''
                params["title"] = original_title[:100]  # Truncate for query

                @retry_on_rate_limit(max_retries=5, base_delay=2.0)
                async def check_composite():
                    response = await self.api_client.get("/api/v1/internal/rss/items", params=params)
                    if response is None:
                        logger.warning(f"API returned None for duplicate check: {params.get('news_id')}")
                        return False
                    if not isinstance(response, dict):
                        logger.warning(f"Unexpected API response type for duplicate check: {type(response)}")
                        return False
                    return len(response.get("data", [])) > 0

                is_dup = await check_composite()

            except Exception as e:
                logger.error(f"Duplicate check failed for {news_id}: {e}")
                is_dup = False

        # Cache result (TTL 1h) — only if redis_service is available
        if self.redis_service is not None:
            try:
                await self.redis_service.set(cache_key, str(int(is_dup)), ttl=3600)
            except Exception as redis_exc:
                logger.debug(f"Redis cache set failed for {news_id}: {redis_exc}")

        if is_dup:
            logger.info(f"Duplicate found: {news_id}")

        return bool(is_dup)
    
    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self.api_client, 'close'):
            await self.api_client.close()
        if self.redis_service:
            await self.redis_service.cleanup()

