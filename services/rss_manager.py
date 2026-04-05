"""RSS manager for FireFeed RSS Parser."""

import logging
from typing import Optional, Dict, Any
from models import RSSFeed
from services.rss_fetcher import RSSFetcher
from services.rss_parser import RSSParser
from services.rss_storage import RSSStorage
from services.media_extractor import MediaExtractor
from services.duplicate_detector import DuplicateDetector
from firefeed_core.api_client.client import APIClient
from firefeed_core.exceptions import ServiceUnavailableException, ServiceException
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
        self.fetcher = fetcher or RSSFetcher()
        self.parser = parser or RSSParser()
        self.storage = storage or RSSStorage()
        self.media_extractor = media_extractor or MediaExtractor()
        self.duplicate_detector = duplicate_detector or DuplicateDetector()
    
    async def process_feed(self, feed: RSSFeed) -> bool:
        try:
            logger.info(f"Processing feed: {feed.name} ({feed.url})")
            
            rss_content = await self.fetcher.fetch_rss(feed.url)
            parsed_data = await self.parser.parse_rss(rss_content)
            if not parsed_data or 'items' not in parsed_data:
                logger.warning(f"No items found in feed: {feed.name}")
                return False
            
            processed_count = 0
            for item_data in parsed_data['items']:
                if item_data is None:
                    logger.warning(f"Skipping None item in feed: {feed.name}")
                    continue
                if not isinstance(item_data, dict):
                    logger.warning(f"Skipping non-dict item_data in feed {feed.name}: type={type(item_data)}, data={item_data}")
                    continue
                
                try:
                    rss_item = self._create_rss_item(item_data, feed)

                    if rss_item is None:
                        logger.warning(f"Skipping invalid rss_item with item_data: {item_data}")
                        continue
                    logger.info(f"rss_item created: news_id={rss_item.get('news_id', 'N/A')[:8]}..., keys={list(rss_item.keys())}")
                        
                    # Safe duplicate check
                    try:
                        is_duplicate = await self.duplicate_detector.is_duplicate(rss_item)
                    except Exception as dup_exc:
                        safe_title = rss_item.get('original_title', 'unknown')[:50] if rss_item and isinstance(rss_item, dict) else 'unknown'
                        logger.warning(f"Duplicate check failed, assuming unique: {dup_exc} | item={safe_title}")
                        is_duplicate = False
                    
                    if is_duplicate:
                        logger.info(f"Skipping duplicate: {rss_item.get('original_title', 'unknown')[:50]}...")
                        continue
                    
                    item_id = await self.storage.save_rss_item(rss_item)
                    if item_id:
                        processed_count += 1
                        logger.info(f"Saved RSS item ID: {item_id}")
                        
                        # Post-save processing
                        post_save_errors = []
                        
                        # Media extraction
                        try:
                            from config.firefeed_rss_parser_config import get_config
                            config = get_config()
                            media = await self.media_extractor.extract_media(rss_item.get('source_url'), rss_item['news_id'], config)
                            if media and isinstance(media, dict) and media.get('local_path'):
                                rss_item['image_filename'] = media['local_path']
                                await self.storage.update_rss_item(item_id, rss_item)
                                logger.info(f"Media updated: {media['local_path']}")
                        except Exception as media_exc:
                            logger.warning(f"Media failed: {media_exc}")
                            post_save_errors.append(str(media_exc))
                        
                        if post_save_errors:
                            logger.error(f"Post-save errors ({len(post_save_errors)}): {post_save_errors}")
                        else:
                            logger.info(f"✓ Fully processed item {item_id}")
                    else:
                        logger.error(f"Failed to save item: {rss_item.get('original_title', 'unknown')}")
                        
                except Exception as e:
                    safe_item_data = repr(item_data)[:200] + '...' if item_data is not None else 'None'
                    logger.exception(f"Item processing error in feed '{feed.name}' ({feed.url}): {e} | item_data={safe_item_data} | type(item_data)={type(item_data)}")
                    continue

            
            logger.info(f"Feed {feed.name} complete: {processed_count} items")
            return processed_count > 0
            
        except ServiceUnavailableException as e:
            logger.error(f"Network error: {e}")
            return False
        except ServiceException as e:
            logger.error(f"Service error: {e}")
            return False
        except Exception as e:
            logger.error(f"Feed error: {e}")
            return False
    
    def _create_rss_item(self, item_data: dict, feed: RSSFeed) -> dict:
        """Create RSS item dict for storage."""
        if item_data is None:
            logger.error(f"_create_rss_item received None item_data for feed '{getattr(feed, 'name', 'unknown')}' ({getattr(feed, 'url', 'unknown')})")
            return None
        
        if not isinstance(item_data, dict):
            raise ValueError(f"item_data must be dict, got {type(item_data)}: {item_data}")

        
        import hashlib
        from datetime import datetime, timezone
        
        logger.debug(f"_create_rss_item: processing item_data type={type(item_data)}, keys={list(item_data.keys()) if isinstance(item_data, dict) else 'N/A'}")
        pub_date = item_data.get('pub_date')
        if isinstance(pub_date, str):
            pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
        elif not hasattr(pub_date, 'tzinfo') and pub_date is not None:
            pub_date = datetime.now(timezone.utc)
        elif pub_date is None:
            pub_date = datetime.now(timezone.utc)
        
        if not item_data.get('link', '').strip():
            logger.debug(f"Skipping item without link: {item_data.get('title', 'unknown')[:50]}")
            return None
        
        guid = item_data.get('guid') or item_data.get('link', '')
        news_id = hashlib.md5(guid.encode()).hexdigest() if guid else hashlib.md5(str(datetime.now()).encode()).hexdigest()
        
        title = item_data.get('title', '')
        content = item_data.get('content') or item_data.get('description', '') or item_data.get('summary', '') or title
        
        return {
            'news_id': news_id,
            'original_title': title,
            'original_content': content,
            'original_language': getattr(feed, 'language', 'en'),
            'category_id': getattr(feed, 'category_id', None),
            'rss_feed_id': getattr(feed, 'id', None),
            'source_url': item_data.get('link'),
            'pub_date': pub_date.isoformat() if hasattr(pub_date, 'isoformat') else str(pub_date)
        }

    
    async def process_feeds(self, feeds: list) -> dict:
        results = {'total_feeds': len(feeds), 'processed': 0, 'failed': 0, 'items': 0, 'errors': []}
        for feed_data in feeds:
            try:
                if feed_data is None:
                    results['failed'] += 1
                    continue
                feed = self._create_feed_object(feed_data)
                success = await self.process_feed(feed)
                if success:
                    results['processed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Feed processing error: {e}")
                results['failed'] += 1
        logger.info(f"Batch complete: {results}")
        return results
    
    @staticmethod
    def _create_feed_object(feed_data: dict):
        class SimpleFeed:
            def __init__(self, data):
                self.id = data.get('id')
                self.url = data.get('url')
                self.name = data.get('name', 'Unknown')
                self.language = data.get('language', 'en')
                self.category_id = data.get('category_id')
        return SimpleFeed(feed_data) if feed_data else SimpleFeed({})
    
    async def cleanup(self):
        pass

