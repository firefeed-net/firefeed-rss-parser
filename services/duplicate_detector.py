"""Duplicate detection service for RSS items."""

import logging
from typing import Optional, List, Dict, Any
from models import RSSItem
from firefeed_core.exceptions import ServiceUnavailableException, ValidationException
from utils.retry import retry_on_network_error
from firefeed_core.api_client.client import APIClient


logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Service for detecting duplicate RSS items."""
    
    def __init__(self, api_client: Optional[APIClient] = None, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        """
        Initialize duplicate detector.
        
        Args:
            api_client: FireFeed API client
            timeout: Request timeout in seconds (for compatibility)
            max_retries: Maximum number of retry attempts (for compatibility)
        """
        import os
        self.api_client = api_client or APIClient(
            base_url=os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001"),
            token=os.getenv("RSS_PARSER_TOKEN", ""),
            service_id="rss-parser-duplicate-detector",
            timeout=30,
            max_retries=max_retries or 3
        )
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def is_duplicate(self, item: RSSItem) -> bool:
        """
        Check if RSS item is a duplicate.
        
        Args:
            item: RSS item to check
            
        Returns:
            True if item is duplicate, False otherwise
        """
        if not item:
            return False
        
        # Check by news_id first (most reliable)
        if item.news_id:
            if await self._check_news_id_duplicate(item.news_id):
                logger.info(f"Duplicate found by news_id: {item.news_id}")
                return True
        
        # Check by source_url if news_id is not available
        if item.source_url:
            if await self._check_link_duplicate(item.source_url):
                logger.info(f"Duplicate found by link: {item.source_url}")
                return True
        
        # Check by title as last resort (less reliable)
        if item.original_title:
            if await self._check_title_duplicate(item.original_title):
                logger.info(f"Duplicate found by title: {item.original_title}")
                return True
        
        return False
    
    async def _check_news_id_duplicate(self, news_id: str) -> bool:
        """
        Check for duplicate by news_id.
        
        Args:
            news_id: Item news_id
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            response = await self.api_client.get("/api/v1/internal/rss/items", params={"news_id": news_id})
            items = response.get("data", [])
            return len(items) > 0
        except Exception as e:
            logger.error(f"Error checking news_id duplicate for {news_id}: {e}")
            return False
    
    async def _check_guid_duplicate(self, guid: str) -> bool:
        """
        Check for duplicate by GUID.
        
        Args:
            guid: Item GUID
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            items = await self.api_client.get_rss_items_list(guid=guid)
            return len(items) > 0
        except Exception as e:
            logger.error(f"Error checking GUID duplicate for {guid}: {e}")
            return False
    
    async def _check_link_duplicate(self, link: str) -> bool:
        """
        Check for duplicate by link.
        
        Args:
            link: Item link
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            response = await self.api_client.get("/api/v1/internal/rss/items", params={"source_url": link})
            items = response.get("data", [])
            return len(items) > 0
        except Exception as e:
            logger.error(f"Error checking link duplicate for {link}: {e}")
            return False
    
    async def _check_title_duplicate(self, title: str) -> bool:
        """
        Check for duplicate by title.
        
        Args:
            title: Item title
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            response = await self.api_client.get("/api/v1/internal/rss/items", params={"title": title})
            items = response.get("data", [])
            return len(items) > 0
        except Exception as e:
            logger.error(f"Error checking title duplicate for {title}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self.api_client, 'close'):
            await self.api_client.close()
    
    async def get_rss_items_list(
        self,
        feed_id: Optional[int] = None,
        guid: Optional[str] = None,
        link: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get list of RSS items with optional filters.
        
        Args:
            feed_id: Filter by feed ID
            guid: Filter by GUID
            link: Filter by link
            title: Filter by title
            page: Page number
            size: Page size
            
        Returns:
            List of RSS items
        """
        params = {
            "page": page,
            "size": size
        }
        
        if feed_id:
            params["feed_id"] = feed_id
        if guid:
            params["guid"] = guid
        if link:
            params["link"] = link
        if title:
            params["title"] = title
        
        try:
            response = await self.api_client.get("/api/v1/internal/rss/items", params=params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching RSS items list: {e}")
            return []