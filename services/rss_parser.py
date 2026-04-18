"""RSS feed parsing service."""

import feedparser
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dateutil import parser as date_parser
from firefeed_core.exceptions import ServiceException, ValidationException
from utils.retry import retry_on_parsing_error
from utils.validation import validate_rss_content, validate_item_data


logger = logging.getLogger(__name__)


class RSSParser:
    """Service for parsing RSS and Atom feeds."""
    
    def __init__(self, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        """
        Initialize RSS parser.
        
        Args:
            timeout: Request timeout in seconds (for compatibility)
            max_retries: Maximum number of retry attempts (for compatibility)
        """
        # Configure feedparser - use only safe built-in XML parser to prevent XXE attacks
        # html5lib and lxml can process external entities which is a security risk
        feedparser.PREFERRED_XML_PARSERS = ['xml']
    
    @retry_on_parsing_error(max_retries=2, base_delay=0.5)
    async def parse_rss(self, rss_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse RSS/Atom feed content.
        
        Args:
            rss_content: RSS/Atom feed content
            
        Returns:
            Parsed feed data or None if parsing fails
            
        Raises:
            ServiceException: If parsing fails
            ValidationException: If content is invalid
        """
        # Validate input
        if not validate_rss_content(rss_content):
            raise ValidationException(
                "Invalid RSS content format",
                details={"field": "content", "value": rss_content[:100] if rss_content else None}
            )
        
        try:
            # Parse feed (run in executor to avoid blocking event loop)
            import asyncio
            parsed = await asyncio.to_thread(feedparser.parse, rss_content)
            
            # Check for parsing errors
            if parsed.bozo:
                bozo_exception = parsed.bozo_exception
                logger.warning(f"Bozo feed detected: {bozo_exception}")
                # Continue parsing even with errors
            
            # Extract feed information
            feed_data = self._extract_feed_data(parsed)
            
            # Extract items
            items = self._extract_items(parsed)
            
            if items:
                feed_data["items"] = items
                logger.info(f"Successfully parsed feed with {len(items)} items")
                return feed_data
            else:
                logger.warning("No items found in feed")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing RSS content: {e}")
            raise ServiceException(
                "Failed to parse RSS content",
                details={"content_preview": rss_content[:100] if rss_content else None, "error": str(e)}
            )
    
    def _extract_feed_data(self, parsed: Any) -> Dict[str, Any]:
        """Extract feed-level data."""
        feed_data = {}
        
        # Extract basic feed information
        if hasattr(parsed.feed, 'title'):
            feed_data["title"] = self._sanitize_text(parsed.feed.title)
        
        if hasattr(parsed.feed, 'link'):
            feed_data["link"] = self._sanitize_text(parsed.feed.link)
        
        if hasattr(parsed.feed, 'description'):
            feed_data["description"] = self._sanitize_text(parsed.feed.description)
        
        if hasattr(parsed.feed, 'language'):
            feed_data["language"] = self._sanitize_text(parsed.feed.language)
        
        if hasattr(parsed.feed, 'published'):
            feed_data["published"] = self._parse_date(parsed.feed.published)
        
        if hasattr(parsed.feed, 'updated'):
            feed_data["updated"] = self._parse_date(parsed.feed.updated)
        
        # Extract additional metadata
        if hasattr(parsed.feed, 'generator'):
            feed_data["generator"] = self._sanitize_text(parsed.feed.generator)
        
        if hasattr(parsed.feed, 'copyright'):
            feed_data["copyright"] = self._sanitize_text(parsed.feed.copyright)
        
        return feed_data
    
    def _extract_items(self, parsed: Any) -> List[Dict[str, Any]]:
        """Extract items from parsed feed."""
        items = []
        
        if not hasattr(parsed, 'entries') or not parsed.entries:
            return items
        
        for entry in parsed.entries:
            item = self._extract_item_data(entry)
            if item:
                items.append(item)
        
        return items
    
    def _extract_item_data(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Extract data from single entry."""
        item = {}
        
        # Extract basic item information
        if hasattr(entry, 'title'):
            item["title"] = self._sanitize_text(entry.title)
        
        if hasattr(entry, 'link'):
            item["link"] = self._sanitize_text(entry.link)
        
        if hasattr(entry, 'description'):
            item["description"] = self._sanitize_text(entry.description)
        
        # Extract content (may have multiple content types)
        if hasattr(entry, 'content') and entry.content:
            item["content"] = self._extract_content(entry.content)
        elif hasattr(entry, 'summary'):
            item["content"] = self._sanitize_text(entry.summary)
        
        # Extract publication date
        if hasattr(entry, 'published'):
            item["pub_date"] = self._parse_date(entry.published)
        elif hasattr(entry, 'updated'):
            item["pub_date"] = self._parse_date(entry.updated)
        else:
            item["pub_date"] = datetime.utcnow()
        
        # Extract GUID
        if hasattr(entry, 'id'):
            item["guid"] = self._sanitize_text(entry.id)
        elif item.get("link"):
            item["guid"] = item["link"]
        
        # Extract author
        if hasattr(entry, 'author'):
            item["author"] = self._sanitize_text(entry.author)
        
        # Extract categories
        if hasattr(entry, 'tags') and entry.tags:
            item["categories"] = [self._sanitize_text(tag.term) for tag in entry.tags]
        
        # Extract media content
        media = self._extract_media_content(entry)
        if media:
            item["media"] = media
        
        # Validate item
        validation_errors = validate_item_data(item)
        if validation_errors:
            logger.warning(f"Item validation failed: {validation_errors}")
            return None
        
        return item
    
    def _extract_content(self, content_list: List[Any]) -> str:
        """Extract content from content list."""
        if not content_list:
            return ""
        
        # Prefer HTML content
        for content in content_list:
            if hasattr(content, 'type') and 'html' in content.type:
                return self._sanitize_text(content.value)
        
        # Fall back to first content
        return self._sanitize_text(content_list[0].value)
    
    def _extract_media_content(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Extract media content from entry."""
        media = {}
        
        # Extract media content (RSS enclosures)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if hasattr(enclosure, 'href'):
                    media["url"] = self._sanitize_text(enclosure.href)
                    if hasattr(enclosure, 'type'):
                        media["type"] = self._sanitize_text(enclosure.type)
                    break
        
        # Extract media from media_content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media_item in entry.media_content:
                if hasattr(media_item, 'url'):
                    media["url"] = self._sanitize_text(media_item.url)
                    if hasattr(media_item, 'type'):
                        media["type"] = self._sanitize_text(media_item.type)
                    break
        
        # Extract thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            if isinstance(entry.media_thumbnail, list) and entry.media_thumbnail:
                # Safely extract URL from first thumbnail
                first_thumb = entry.media_thumbnail[0]
                if first_thumb and isinstance(first_thumb, dict):
                    media["thumbnail"] = self._sanitize_text(first_thumb.get('url', ''))
            elif isinstance(entry.media_thumbnail, dict):
                media["thumbnail"] = self._sanitize_text(entry.media_thumbnail.get('url', ''))
        
        return media if media else None
    
    def _sanitize_text(self, text: Any) -> str:
        """Sanitize text content by stripping HTML tags and normalizing whitespace."""
        if text is None:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        try:
            # Use BeautifulSoup for safe HTML stripping (handles malformed HTML, entities)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            # Get text and collapse whitespace
            cleaned = ' '.join(soup.stripped_strings)
            return cleaned
        except Exception as e:
            logger.debug(f"BeautifulSoup sanitization failed: {e}, falling back to regex")
            # Fallback to regex-based stripping (less safe but better than nothing)
            import re
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _parse_date(self, date_string: Any) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_string:
            return None
        
        # First try dateutil with fuzzy parsing for GMT/RFC-822
        try:
            parsed_date = date_parser.parse(str(date_string), fuzzy=True)
            logger.debug(f"Successfully parsed date with dateutil: {date_string} -> {parsed_date}")
            return parsed_date
        except Exception:
            pass
        
        # Fallback to feedparser
        try:
            parsed_date = feedparser._parse_date(date_string)
            logger.debug(f"Successfully parsed date with feedparser: {date_string} -> {parsed_date}")
            return parsed_date
        except Exception:
            logger.warning(f"Could not parse date: {date_string}")
            return None
    
    async def parse_multiple_feeds(self, feeds_content: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Parse multiple RSS feeds concurrently.
        
        Args:
            feeds_content: List of RSS feed contents
            
        Returns:
            List of parsed feed data
        """
        import asyncio
        
        tasks = [self.parse_rss(content) for content in feeds_content]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        parsed_feeds = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to parse feed {i}: {result}")
                parsed_feeds.append(None)
            else:
                parsed_feeds.append(result)
        
        return parsed_feeds