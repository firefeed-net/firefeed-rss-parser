"""Media extraction service for RSS items."""

import httpx
import aiohttp
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from firefeed_core.exceptions import ServiceUnavailableException, ServiceException
from utils.retry import retry_on_network_error, retry_on_parsing_error
from utils.validation import validate_url
from utils.image import ImageProcessor
from config.firefeed_rss_parser_config import get_config


logger = logging.getLogger(__name__)


class MediaExtractor:
    """Service for extracting media content from RSS items."""
    
    def __init__(self, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        """
        Initialize media extractor.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts (for compatibility)
        """
        self.timeout = timeout or 15.0
        self._aiohttp_session: Optional[aiohttp.ClientSession] = None
    
    async def _get_aiohttp_session(self) -> aiohttp.ClientSession:
        """Get or create a shared aiohttp session for image downloads."""
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self._aiohttp_session = aiohttp.ClientSession(timeout=timeout)
        return self._aiohttp_session
    
    async def cleanup(self):
        """Close shared aiohttp session."""
        if self._aiohttp_session and not self._aiohttp_session.closed:
            await self._aiohttp_session.close()
    
    async def extract_media(self, url: str, rss_item_id: str, config=None) -> Optional[Dict[str, Any]]:
        """
        Extract and save media content from URL.

        Args:
            url: URL to extract media from
            rss_item_id: ID for saving file name
            config: Config object

        Returns:
            Media information with local_path or None
        """
        if not validate_url(url) or not rss_item_id:
            logger.warning(f"Invalid URL or no rss_item_id for media extraction: {url}")
            return None

        config = config or get_config()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                media_info = await self._parse_html_for_media(response.text, url)
                if not media_info:
                    return None

                # If image, download and save using shared aiohttp session
                if media_info.get('type') == 'image':
                    img_url = media_info['url']
                    session = await self._get_aiohttp_session()
                    local_path = await ImageProcessor.process_image_from_url(img_url, rss_item_id, session=session)
                    if local_path:
                        media_info['local_path'] = local_path
                        logger.info(f"Image saved at local_path: {local_path}")
                    else:
                        logger.warning(f"Failed to save image from {img_url}")

                return media_info

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors immediately without retry (client errors are not retryable)
            status_code = e.response.status_code
            if 400 <= status_code < 500:
                logger.warning(f"Client error {status_code} for {url} (e.g. paywall), skipping media")
                return None
            else:
                logger.error(f"Server error {status_code} for {url}: {e}")
                return None
        except httpx.TimeoutException as e:
            logger.error(f"Media extraction timeout for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting media from {url}: {e}")
            return None
    
    @retry_on_parsing_error(max_retries=2, base_delay=0.3)
    async def _parse_html_for_media(self, html_content: str, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse HTML content for media elements.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Media content information or None if no media found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract OpenGraph image (highest priority)
            og_image = self._extract_og_image(soup, base_url)
            if og_image:
                return og_image
            
            # Extract Twitter image
            twitter_image = self._extract_twitter_image(soup, base_url)
            if twitter_image:
                return twitter_image
            
            # Extract first body image
            body_image = self._extract_body_image(soup, base_url)
            if body_image:
                return body_image
            
            # Extract video
            video = self._extract_video(soup, base_url)
            if video:
                return video
            
            # Extract audio
            audio = self._extract_audio(soup, base_url)
            if audio:
                return audio
            
            logger.debug(f"No media found in {base_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing HTML for media: {e}")
            raise ServiceException(f"Failed to parse HTML for media", html_content[:100], e)
    
    def _extract_og_image(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract OpenGraph image."""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = urljoin(base_url, og_image['content'])
            title = self._extract_og_title(soup)
            description = self._extract_og_description(soup)
            
            return {
                "url": image_url,
                "type": "image",
                "title": title,
                "description": description
            }
        return None
    
    def _extract_twitter_image(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract Twitter image."""
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            image_url = urljoin(base_url, twitter_image['content'])
            title = self._extract_og_title(soup)
            description = self._extract_og_description(soup)
            
            return {
                "url": image_url,
                "type": "image",
                "title": title,
                "description": description
            }
        return None
    
    def _extract_body_image(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract first image from body."""
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image_url = urljoin(base_url, img_tag['src'])
            title = img_tag.get('alt', '')
            description = img_tag.get('title', '')
            
            return {
                "url": image_url,
                "type": "image",
                "title": title,
                "description": description
            }
        return None
    
    def _extract_video(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract video element."""
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = urljoin(base_url, video_tag['src'])
            
            return {
                "url": video_url,
                "type": "video",
                "title": "",
                "description": ""
            }
        
        # Also check for source elements inside video
        source_tag = soup.find('source', type=lambda x: x and 'video' in x)
        if source_tag and source_tag.get('src'):
            video_url = urljoin(base_url, source_tag['src'])
            
            return {
                "url": video_url,
                "type": "video",
                "title": "",
                "description": ""
            }
        return None
    
    def _extract_audio(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract audio element."""
        audio_tag = soup.find('audio')
        if audio_tag and audio_tag.get('src'):
            audio_url = urljoin(base_url, audio_tag['src'])
            
            return {
                "url": audio_url,
                "type": "audio",
                "title": "",
                "description": ""
            }
        
        # Also check for source elements inside audio
        source_tag = soup.find('source', type=lambda x: x and 'audio' in x)
        if source_tag and source_tag.get('src'):
            audio_url = urljoin(base_url, source_tag['src'])
            
            return {
                "url": audio_url,
                "type": "audio",
                "title": "",
                "description": ""
            }
        return None
    
    def _extract_og_title(self, soup: BeautifulSoup) -> str:
        """Extract OpenGraph title."""
        og_title = soup.find('meta', property='og:title')
        return og_title.get('content', '') if og_title else ''
    
    def _extract_og_description(self, soup: BeautifulSoup) -> str:
        """Extract OpenGraph description."""
        og_description = soup.find('meta', property='og:description')
        return og_description.get('content', '') if og_description else ''
    

