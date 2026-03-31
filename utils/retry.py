"""Retry utilities for FireFeed RSS Parser."""

import asyncio
import logging
import re
from functools import wraps
from typing import Callable, Type, Union, Any
from firefeed_core.exceptions import FireFeedException, RateLimitException, ServiceUnavailableException, ServiceException


logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple] = (Exception,),
    raise_last_error: bool = True
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Exception types to catch and retry
        raise_last_error: Whether to raise the last error if all retries fail
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    if attempt == max_retries:
                        logger.error(f'Max retries ({max_retries}) exceeded for {func.__name__}: {e}')
                        if raise_last_error:
                            raise
                        return None
                    
                    logger.warning(f'Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}')
                    logger.info(f'Retrying in {delay} seconds...')
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            return None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    if attempt == max_retries:
                        logger.error(f'Max retries ({max_retries}) exceeded for {func.__name__}: {e}')
                        if raise_last_error:
                            raise
                        return None
                    
                    logger.warning(f'Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}')
                    logger.info(f'Retrying in {delay} seconds...')
                    
                    asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            return None
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying on network errors with exponential backoff.
    """
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(ServiceUnavailableException, asyncio.TimeoutError, ConnectionError),
        raise_last_error=True
    )


def retry_on_parsing_error(max_retries: int = 2, base_delay: float = 0.5):
    """
    Decorator for retrying on parsing errors with exponential backoff.
    """
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(ServiceException,),
        raise_last_error=True
    )


def retry_on_rate_limit(max_retries: int = 10, base_delay: float = 2.0):
    """
    Decorator for retrying on RateLimitException with dynamic backoff using retry_after.
    """
    import random
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except RateLimitException as e:
                    if attempt == max_retries:
                        logger.error(f'Max rate limit retries ({max_retries}) exceeded for {func.__name__}: {e}')
                        raise
                    retry_after = base_delay * (2 ** attempt)
                    # Improved regex for retry_after
                    match = re.search(r'retry_after[=:]?(\d+)', str(e).lower())
                    if match:
                        retry_after = min(int(match.group(1)), 300)
                    # Add jitter to avoid thundering herd
                    retry_after += random.uniform(0, 1)
                    logger.warning(f'Rate limited for {func.__name__} (attempt {attempt+1}/{max_retries+1}), waiting {retry_after:.1f}s')
                    await asyncio.sleep(retry_after)
            return None
        return wrapper
    return decorator
