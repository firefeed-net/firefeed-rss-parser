"""Validation utilities for FireFeed RSS Parser."""

import re
import logging
from typing import Optional
from urllib.parse import urlparse
from firefeed_core.exceptions import ValidationException


logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        # Check if scheme and netloc are present
        if not all([result.scheme, result.netloc]):
            return False
        
        # Check if scheme is HTTP or HTTPS
        if result.scheme not in ['http', 'https']:
            return False
        
        # Basic URL format validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+'  # domain name
            r'(?::\d+)?'  # optional port
            r'(?:[/?:].*)?$',  # path, query, fragment
            re.IGNORECASE
        )
        
        return bool(url_pattern.match(url))
        
    except Exception as e:
        logger.error(f"Error validating URL '{url}': {e}")
        return False


def validate_rss_content(content: str) -> bool:
    """
    Validate RSS content format.
    
    Args:
        content: RSS content to validate
        
    Returns:
        True if content appears to be valid RSS, False otherwise
    """
    if not content or not isinstance(content, str):
        return False
    
    # Check for basic RSS elements
    rss_indicators = [
        '<rss',
        '<feed',  # Atom feeds
        '<?xml'
    ]
    
    content_lower = content.lower().strip()
    
    # Check if content starts with XML declaration
    if not content_lower.startswith('<?xml'):
        logger.warning("RSS content does not start with XML declaration")
        return False
    
    # Check for RSS or Atom indicators
    has_rss_indicator = any(indicator in content_lower for indicator in rss_indicators)
    
    if not has_rss_indicator:
        logger.warning("RSS content does not contain expected RSS/Atom indicators")
        return False
    
    # Basic well-formedness check (simplified)
    open_tags = content_lower.count('<')
    close_tags = content_lower.count('>')
    
    if open_tags != close_tags:
        logger.warning("RSS content has mismatched XML tags")
        return False
    
    return True


def validate_feed_data(feed_data: dict) -> list:
    """
    Validate feed data dictionary.
    
    Args:
        feed_data: Dictionary containing feed data
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not isinstance(feed_data, dict):
        errors.append("Feed data must be a dictionary")
        return errors
    
    # Required fields
    required_fields = ['title', 'link', 'description']
    
    for field in required_fields:
        if field not in feed_data:
            errors.append(f"Missing required field: {field}")
        elif not feed_data[field]:
            errors.append(f"Field '{field}' cannot be empty")
    
    # Validate link URL
    if 'link' in feed_data and feed_data['link']:
        if not validate_url(feed_data['link']):
            errors.append(f"Invalid URL format: {feed_data['link']}")
    
    # Validate items if present
    if 'items' in feed_data:
        if not isinstance(feed_data['items'], list):
            errors.append("Items must be a list")
        else:
            for i, item in enumerate(feed_data['items']):
                if not isinstance(item, dict):
                    errors.append(f"Item {i} must be a dictionary")
                    continue
                
                # Check for required item fields
                if 'title' not in item or not item['title']:
                    errors.append(f"Item {i} missing required field: title")
                
                if 'link' in item and item['link'] and not validate_url(item['link']):
                    errors.append(f"Item {i} has invalid URL: {item['link']}")
    
    return errors


def validate_item_data(item_data: dict) -> list:
    """
    Validate individual item data.
    
    Args:
        item_data: Dictionary containing item data
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not isinstance(item_data, dict):
        errors.append("Item data must be a dictionary")
        return errors
    
    # Required fields for items
    required_fields = ['title', 'link']
    
    for field in required_fields:
        if field not in item_data:
            errors.append(f"Missing required field: {field}")
        elif not item_data[field]:
            errors.append(f"Field '{field}' cannot be empty")
    
    # Validate link URL
    if 'link' in item_data and item_data['link']:
        if not validate_url(item_data['link']):
            errors.append(f"Invalid URL format: {item_data['link']}")
    
    # Validate publication date format if present
    if 'pub_date' in item_data and item_data['pub_date']:
        # Basic check for date-like string
        pub_date = str(item_data['pub_date'])
        if not re.match(r'\d{4}-\d{2}-\d{2}', pub_date):
            errors.append(f"Invalid date format: {pub_date}")
    
    return errors


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Truncate if too long
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized


def validate_and_sanitize_url(url: str) -> str:
    """
    Validate and sanitize URL.
    
    Args:
        url: URL to validate and sanitize
        
    Returns:
        Sanitized URL if valid, raises ValidationException otherwise
    """
    if not validate_url(url):
        raise ValidationException(f"Invalid URL format: {url}")
    
    # Basic sanitization
    sanitized = sanitize_string(url, max_length=2048)
    
    return sanitized