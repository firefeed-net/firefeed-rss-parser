"""RSS feed fetching service."""

import httpx
import logging
from typing import Optional, Dict, Any
from config.firefeed_rss_parser_config import get_config
config = get_config()
from firefeed_core.exceptions import ServiceUnavailableException, ValidationException
from utils.retry import retry_on_network_error
from utils.validation import validate_url


logger = logging.getLogger(__name__)


class RSSFetcher:
    """Service for fetching RSS feeds."""
    
    def __init__(self, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        """
        Initialize RSS fetcher.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts (for retry decorator)
        """
        self.timeout = timeout or config.fetch_timeout
        self.max_retries = max_retries or 3
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
    async def fetch_rss(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Any] = None,
        proxies: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        allow_redirects: bool = True
    ) -> str:
        """
        Fetch RSS feed content.
        
        Args:
            url: RSS feed URL
            headers: Additional HTTP headers
            auth: Authentication tuple
            proxies: Proxy configuration
            verify_ssl: Whether to verify SSL certificates
            allow_redirects: Whether to follow redirects
            
        Returns:
            RSS feed content as string
            
        Raises:
            ServiceUnavailableException: If fetching fails
            ValidationException: If URL is invalid
        """
        # Validate URL
        if not validate_url(url):
            raise ValidationException(
                f"Invalid RSS feed URL: {url}",
                details={"field": "url", "value": url}
            )
        
        # Prepare headers
        request_headers = {
            "User-Agent": "FireFeed RSS Parser/1.0",
            "Accept": "application/rss+xml, application/atom+xml, text/xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        
        if headers:
            request_headers.update(headers)
        
        try:
            # Create client with custom settings
            client_kwargs = {
                "timeout": self.timeout,
                "headers": request_headers,
                "verify": verify_ssl,
                "follow_redirects": allow_redirects
            }
            
            if auth:
                client_kwargs["auth"] = auth
            if proxies:
                client_kwargs["proxies"] = proxies
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content = response.text
                
                # Validate RSS content
                if not self._is_valid_rss_content(content):
                    logger.warning(f"Fetched content from {url} may not be valid RSS")
                
                logger.info(f"Successfully fetched RSS feed from {url}")
                return content
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching RSS feed from {url}: {e}")
            raise ServiceUnavailableException(
                f"Timeout fetching RSS feed from {url}",
                details={"url": url, "error": str(e)}
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} fetching {url}: {e}")
            if e.response.status_code == 404:
                raise ServiceUnavailableException(
                    f"RSS feed not found: {url}",
                    details={"url": url, "status_code": 404, "error": str(e)}
                )
            elif e.response.status_code == 403:
                raise ServiceUnavailableException(
                    f"Access forbidden for RSS feed: {url}",
                    details={"url": url, "status_code": 403, "error": str(e)}
                )
            elif e.response.status_code == 429:
                raise ServiceUnavailableException(
                    f"Rate limited for RSS feed: {url}",
                    details={"url": url, "status_code": 429, "error": str(e)}
                )
            else:
                raise ServiceUnavailableException(
                    f"HTTP error {e.response.status_code} for {url}",
                    details={"url": url, "status_code": e.response.status_code, "error": str(e)}
                )
                
        except httpx.RequestError as e:
            logger.error(f"Request error fetching RSS feed from {url}: {e}")
            raise ServiceUnavailableException(
                f"Request error fetching RSS feed from {url}",
                details={"url": url, "error": str(e)}
            )
    
    def _is_valid_rss_content(self, content: str) -> bool:
        """
        Check if content appears to be valid RSS.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content appears to be valid RSS
        """
        if not content or not isinstance(content, str):
            return False
        
        content_lower = content.lower().strip()
        
        # Check for XML declaration
        if not content_lower.startswith('<?xml'):
            return False
        
        # Check for RSS or Atom indicators
        rss_indicators = ['<rss', '<feed', '<channel']
        has_rss_indicator = any(indicator in content_lower for indicator in rss_indicators)
        
        return has_rss_indicator
    
    async def fetch_with_etag(
        self, 
        url: str, 
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch RSS feed with ETag and Last-Modified support.
        
        Args:
            url: RSS feed URL
            etag: ETag from previous request
            last_modified: Last-Modified header from previous request
            
        Returns:
            Dictionary with content and headers
        """
        headers = {}
        
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified
        
        content = await self.fetch_rss(url, headers=headers)
        
        # In a real implementation, we would extract ETag and Last-Modified
        # from the response headers. For now, we return the content.
        return {
            "content": content,
            "etag": None,
            "last_modified": None
        }