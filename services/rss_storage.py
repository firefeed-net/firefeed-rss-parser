
"""RSS storage service for FireFeed RSS Parser."""

import logging
from typing import Optional, List, Dict, Any
from firefeed_core.exceptions import ServiceException, ValidationException, ServiceUnavailableException
from firefeed_core.api_client.client import APIClient
from utils.retry import retry_on_network_error

logger = logging.getLogger(__name__)

class RSSStorage:
    "Service for storing RSS items via FireFeed API."

    def __init__(self, api_client=None, timeout=None, max_retries=None):
        import os
        self.api_client = api_client or APIClient(
            base_url=os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001"),
            token=os.getenv("SERVICE_API_TOKEN", ""),
            service_id="rss-parser-storage",
            timeout=timeout or 30,
            max_retries=max_retries or 3
        )

    @retry_on_network_error(max_retries=5, base_delay=2.0)
    async def save_rss_item(self, item_data):
        """Save RSS item dict to API with rate limit handling."""


        """Save RSS item dict to API with rate limit handling."""
        try:
            self._validate_item_data(item_data)
            result = await self.api_client.post("/api/v1/internal/rss/items", json_data=item_data)
            if result is None:
                logger.warning("save_rss_item API returned None")
                return None
            if isinstance(result, dict):
                news_id = result.get("news_id")
                logger.info(f"Saved RSS item news_id: {news_id}")
                return news_id
            logger.warning(f"save_rss_item unexpected result type: {type(result)}")
            return None
        except Exception as e:
            logger.error(f"Save RSS item failed: {e}")
            raise ServiceException(f"Failed to save: {e}")


    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def update_rss_item(self, item_id, item_data):
        "Update RSS item dict."
        try:
            self._validate_item_data(item_data)
            result = await self.api_client.put(f"/api/v1/internal/rss/items/{item_id}", json_data=item_data)
            if result is None:
                logger.warning(f"update_rss_item {item_id} API returned None")
                return False
            logger.info(f"Updated RSS item {item_id}: {item_data.get('original_title', 'unknown')[:50]}")
            return True
        except Exception as e:
            logger.error(f"Update RSS item {item_id} failed: {e}")
            return False

    def _validate_item_data(self, item_data):
        # Strict validation for RSS items - check all essential fields
        required = ['news_id', 'source_url', 'original_title', 'original_content', 'pub_date']
        for field in required:
            if field not in item_data or item_data[field] is None or item_data[field] == '':
                raise ValidationException(f"Missing/empty required field: {field}")
        if 'rss_feed_id' in item_data and item_data['rss_feed_id'] is None:
            raise ValidationException("rss_feed_id cannot be None")
        logger.debug(f"Validated RSS item: news_id={item_data.get('news_id')[:8]}...")


    async def cleanup(self):
        "Cleanup resources."
        if hasattr(self.api_client, 'close'):
            await self.api_client.close()

    async def get_rss_items_list(self, page=1, size=10, **filters):
        params = {"page": page, "size": size, **filters}
        try:
            response = await self.api_client.get("/api/v1/internal/rss/items", params=params)
            return response.get("data", []) if isinstance(response, dict) else []
        except Exception as e:
            logger.error(f"Error fetching RSS items: {e}")
            return []

    async def get_feeds_to_process(self):
        params = {"page": 1, "size": 100, "is_active": True}
        try:
            response = await self.api_client.get("/api/v1/internal/rss/feeds", params=params)
            return response.get("data", []) if isinstance(response, dict) else []
        except Exception as e:
            logger.error(f"Error fetching feeds: {e}")
            return []
