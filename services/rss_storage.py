"""RSS storage service for FireFeed RSS Parser."""

import logging
from typing import Optional, List, Dict, Any
from models import RSSItem
from firefeed_core.exceptions import ServiceException, ValidationException, ServiceUnavailableException
from firefeed_core.api_client.client import APIClient
from utils.retry import retry_on_network_error, retry_on_parsing_error


logger = logging.getLogger(__name__)


class RSSStorage:
    """Service for storing RSS items via FireFeed API."""
    
    def __init__(self, api_client: Optional[APIClient] = None, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        """
        Initialize RSS storage.
        
        Args:
            api_client: FireFeed API client
            timeout: Request timeout in seconds (for compatibility)
            max_retries: Maximum number of retry attempts (for compatibility)
        """
        import os
        self.api_client = api_client or APIClient(
            base_url=os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8001"),
            token=os.getenv("RSS_PARSER_TOKEN", ""),
            service_id="rss-parser-storage",
            timeout=timeout or 30,
            max_retries=max_retries or 3
        )
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
    async def save_rss_item(self, item: RSSItem) -> int:
        """
        Save RSS item to FireFeed API.
        
        Args:
            item: RSS item to save
            
        Returns:
            Saved item ID
            
        Raises:
            ValidationException: If item validation fails
            StorageError: If storage operation fails
        """
        if not item:
            raise ValidationException("RSS item cannot be None")
        
        try:
            # Convert item to API format
            item_data = self._convert_to_api_format(item)
            
            # Validate data before sending
            self._validate_item_data(item_data)
            
            # Save to API
            result = await self.api_client.post("/api/v1/internal/rss/items", json_data=item_data)
            
            logger.info(f"Successfully saved RSS item: {item.original_title}")
            return result.get("id")
            
        except ValidationException as e:
            logger.error(f"Validation error saving RSS item: {e}")
            raise
        except ServiceUnavailableException as e:
            logger.error(f"Network error saving RSS item: {e}")
            raise ServiceException(f"Failed to save RSS item due to network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving RSS item: {e}")
            raise ServiceException(f"Failed to save RSS item: {e}")
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def update_rss_item(self, item_id: int, item: RSSItem) -> bool:
        """
        Update existing RSS item.
        
        Args:
            item_id: Item ID to update
            item: Updated item data
            
        Returns:
            True if update successful, False otherwise
        """
        if not item:
            raise ValidationException("RSS item cannot be None", field="item", value=None)
        
        try:
            # Convert item to API format
            item_data = self._convert_to_api_format(item)
            
            # Validate data before sending
            self._validate_item_data(item_data)
            
            # Update via API
            result = await self.api_client.update_rss_item(item_id, item_data)
            
            logger.info(f"Successfully updated RSS item {item_id}: {item.title}")
            return True
            
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error updating RSS item {item_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating RSS item {item_id}: {e}")
            return False
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def delete_rss_item(self, item_id: int) -> bool:
        """
        Delete RSS item.
        
        Args:
            item_id: Item ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = await self.api_client.delete_rss_item(item_id)
            
            if result:
                logger.info(f"Successfully deleted RSS item {item_id}")
            else:
                logger.warning(f"Failed to delete RSS item {item_id}")
            
            return result
            
        except ServiceUnavailableException as e:
            logger.error(f"Network error deleting RSS item {item_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting RSS item {item_id}: {e}")
            return False
    
    def _convert_to_api_format(self, item: RSSItem) -> dict:
        """
        Convert RSSItem to API format.
        
        Args:
            item: RSS item
            
        Returns:
            Dictionary in API format
        """
        # Map RSSItem fields to API's RSSItemCreate model fields
        # API expects: title, content, link, guid, pub_date, feed_id, category_id, source_id, language, image_url, video_url, metadata
        return {
            "title": item.original_title,
            "content": item.original_content,
            "link": item.source_url or "",
            "guid": item.news_id,
            "pub_date": item.pub_date.isoformat() if item.pub_date else "",
            "feed_id": item.rss_feed_id,
            "category_id": item.category_id,
            "source_id": None,  # Will be determined from feed
            "language": item.original_language,
            "image_url": item.image_filename,
            "video_url": None,
            "metadata": None
        }
    
    def _validate_item_data(self, item_data: dict) -> None:
        """
        Validate item data before sending to API.
        
        Args:
            item_data: Item data dictionary
            
        Raises:
            ValidationException: If validation fails
        """
        # API expects: title, content, link, guid, pub_date, feed_id
        required_fields = ['title', 'content', 'link', 'guid', 'pub_date', 'feed_id']
        
        for field in required_fields:
            if field not in item_data or item_data[field] is None:
                raise ValidationException(
                    f"Missing required field: {field}",
                    details={"field": field, "value": item_data.get(field)}
                )
    
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
    
    async def create_rss_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new RSS item.
        
        Args:
            item_data: RSS item data
            
        Returns:
            Created item data
        """
        return await self.api_client.post("/api/v1/internal/rss/items", json_data=item_data)
    
    async def update_rss_item(self, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing RSS item.
        
        Args:
            item_id: Item ID
            item_data: Updated item data
            
        Returns:
            Updated item data
        """
        return await self.api_client.put(f"/api/v1/internal/rss/items/{item_id}", json_data=item_data)
    
    async def delete_rss_item(self, item_id: int) -> bool:
        """
        Delete RSS item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            await self.api_client.delete(f"/api/v1/internal/rss/items/{item_id}")
            return True
        except Exception:
            return False
    
    async def get_feeds_to_process(self) -> List[Dict[str, Any]]:
        """
        Get RSS feeds that need to be processed.
        
        Returns:
            List of RSS feeds to process
        """
        params = {"page": 1, "size": 100}
        try:
            response = await self.api_client.get("/api/v1/internal/rss/feeds", params=params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching RSS feeds list: {e}")
            return []