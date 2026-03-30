"""RSS manager for FireFeed RSS Parser."""

import logging
from typing import Optional
from models import RSSFeed, RSSItem
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.rss_storage import RSSStorage
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from firefeed_core.api_client.client import APIClient
from firefeed_core.exceptions import FireFeedException, ServiceUnavailableException, ServiceException
from utils.logging_config import get_logger


logger = get_logger(__name__)


class RSSManager:
    """Main RSS processing manager."""
    
    def __init__(
        self,
        fetcher: Optional[RSSFetcher] = None,
        parser: Optional[RSSParser] = None,
        storage: Optional[RSSStorage] = None,
        media_extractor: Optional[MediaExtractor] = None,
        duplicate_detector: Optional[DuplicateDetector] = None,
        max_concurrent_feeds: Optional[int] = None
    ):
        """
        Initialize RSS manager.
        
        Args:
            fetcher: RSS fetcher service
            parser: RSS parser service
            storage: RSS storage service
            media_extractor: Media extractor service
            duplicate_detector: Duplicate detector service
            max_concurrent_feeds: Maximum concurrent feeds (for compatibility)
        """
        self.fetcher = fetcher or RSSFetcher()
        self.parser = parser or RSSParser()
        self.storage = storage or RSSStorage()
        self.media_extractor = media_extractor or MediaExtractor()
        self.duplicate_detector = duplicate_detector or DuplicateDetector()
    
    async def process_feed(self, feed: RSSFeed) -> bool:
        """
        Process single RSS feed.
        
        Args:
            feed: RSS feed to process
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            logger.info(f"Processing feed: {feed.name} ({feed.url})")
            
            # Fetch RSS content
            rss_content = await self.fetcher.fetch_rss(feed.url)
            
            # Parse RSS content
            parsed_data = await self.parser.parse_rss(rss_content)
            if not parsed_data or 'items' not in parsed_data:
                logger.warning(f"No items found in feed: {feed.name}")
                return False
            
            # Process each item
            processed_count = 0
            for item_data in parsed_data['items']:
                try:
                    # Create RSS item
                    rss_item = self._create_rss_item(item_data, feed)
                    
                    # Check for duplicates
                    is_duplicate = await self.duplicate_detector.is_duplicate(rss_item)
                    if is_duplicate:
                        logger.info(f"Skipping duplicate item: {rss_item.original_title}")
                        continue
                    
                    # Save item first
                    item_id = await self.storage.save_rss_item(rss_item)
                    if item_id:
                        processed_count += 1
                        logger.info(f"Successfully saved RSS item to DB (ID: {item_id}): {rss_item.original_title}")
                    else:
                        logger.error(f"Failed to save RSS item to DB: {rss_item.original_title}")
                        continue
                    
                    # === POST-SAVE PROCESSING ===
                    post_save_errors = []
                    
                    # 1. Extract and update media (non-blocking)
                    try:
                        from config.firefeed_rss_parser_config import get_config
                        config = get_config()
                        media = await self.media_extractor.extract_media(rss_item.source_url, rss_item.news_id, config)
                        if media and isinstance(media, dict) and media.get('local_path'):
                            rss_item.image_filename = media['local_path']
                            await self.storage.update_rss_item(item_id, rss_item)
                            logger.info(f"✓ Media updated for item {item_id}: {media['local_path']}")
                        else:
                            logger.debug(f"No media found for {rss_item.source_url}")
                    except Exception as media_exc:
                        media_error = f"Media extraction failed: {str(media_exc)}"
                        post_save_errors.append(media_error)
                        logger.warning(f"⚠ {media_error}")
                    
                    # 2. Final duplicate check/update if needed (non-blocking)
                    try:
                        if await self.duplicate_detector.is_duplicate(rss_item):
                            logger.info(f"Item {item_id} marked as duplicate after processing")
                            # Could update status here if needed
                    except Exception as dup_exc:
                        dup_error = f"Final duplicate check failed: {str(dup_exc)}"
                        post_save_errors.append(dup_error)
                        logger.warning(f"⚠ {dup_error}")
                    
                    # 3. Translation (if configured, non-blocking)
                    try:
                        # Placeholder for translation if implemented
                        pass
                    except Exception as trans_exc:
                        trans_error = f"Translation failed: {str(trans_exc)}"
                        post_save_errors.append(trans_error)
                        logger.warning(f"⚠ {trans_error}")
                    
                    # Log post-save summary
                    if post_save_errors:
                        logger.error(f"Post-save processing had {len(post_save_errors)} errors for '{rss_item.original_title}': {'; '.join(post_save_errors)}")
                        logger.info(f"Item still saved to DB (ID: {item_id}) despite post-save errors")
                    else:
                        logger.info(f"✓ Fully processed item {item_id}: {rss_item.original_title}")

                        
                except Exception as e:
                    logger.error(f"Error processing item {item_data.get('title', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Completed processing feed {feed.name}: {processed_count} items processed")
            return processed_count > 0
            
        except ServiceUnavailableException as e:
            logger.error(f"Network error processing feed {feed.name}: {e}")
            return False
        except ServiceException as e:
            logger.error(f"Service error processing feed {feed.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing feed {feed.name}: {str(e)}")
            return False
    
    def _create_rss_item(self, item_data: dict, feed: RSSFeed) -> RSSItem:
        """
        Create RSSItem from parsed data.
        
        Args:
            item_data: Parsed item data
            feed: RSS feed
            
        Returns:
            RSSItem instance
        """
        import hashlib
        from datetime import datetime, timezone
        
        # Parse publication date
        pub_date = item_data.get('pub_date')
        if isinstance(pub_date, str):
            pub_date = datetime.fromisoformat(pub_date)
        elif not isinstance(pub_date, datetime):
            pub_date = datetime.now(timezone.utc)
        
        # Generate news_id from guid or link
        guid = item_data.get('guid') or item_data.get('link', '')
        news_id = hashlib.md5(guid.encode()).hexdigest() if guid else hashlib.md5(str(datetime.now()).encode()).hexdigest()
        
        # Get title and content - use description as fallback for content
        title = item_data.get('title', '')
        content = item_data.get('content') or item_data.get('description') or item_data.get('summary', '')
        
        # If content is still empty, use title as content (minimum requirement)
        if not content:
            content = title
        
        return RSSItem(
            news_id=news_id,
            original_title=title,
            original_content=content,
            original_language=feed.language or 'en',
            category_id=feed.category_id,
            rss_feed_id=feed.id,
            source_url=item_data.get('link'),
            pub_date=pub_date
        )
    
    async def process_feeds(self, feeds: list) -> dict:
        """
        Process multiple RSS feeds.
        
        Args:
            feeds: List of feed dictionaries with keys: id, url, name, language, is_active
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'total_feeds': len(feeds),
            'processed_feeds': 0,
            'failed_feeds': 0,
            'total_items_processed': 0,
            'errors': []
        }
        
        for feed_data in feeds:
            try:
                # Convert feed dictionary to RSSFeed-like object
                feed = self._create_feed_object(feed_data)
                
                # Process the feed
                success = await self.process_feed(feed)
                
                if success:
                    results['processed_feeds'] += 1
                else:
                    results['failed_feeds'] += 1
                    results['errors'].append(f"Failed to process feed: {feed_data.get('name', 'Unknown')}")
                    
            except Exception as e:
                results['failed_feeds'] += 1
                error_str = str(e)
                error_msg = f"Error processing feed {feed_data.get('name', 'Unknown')}: {error_str}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                continue
        
        logger.info(f"Completed processing {results['processed_feeds']}/{results['total_feeds']} feeds")
        return results
    
    def _create_feed_object(self, feed_data: dict):
        """
        Create a simple feed object from dictionary data.
        
        Args:
            feed_data: Feed dictionary with keys: id, url, name, language, is_active
            
        Returns:
            Simple object with required attributes
        """
        class SimpleFeed:
            def __init__(self, data):
                self.id = data.get('id')
                self.url = data.get('url')
                self.name = data.get('name', 'Unknown Feed')
                self.language = data.get('language', 'en')
                self.is_active = data.get('is_active', True)
                self.category_id = data.get('category_id')
                
        return SimpleFeed(feed_data)

    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self.duplicate_detector, 'cleanup'):
            await self.duplicate_detector.cleanup()
        if hasattr(self.storage, 'cleanup'):
            await self.storage.cleanup()

