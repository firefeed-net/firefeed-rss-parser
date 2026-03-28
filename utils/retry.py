"""Retry utilities for FireFeed RSS Parser."""

import asyncio
import logging
from functools import wraps
from typing import Callable, Type, Union, Any
from firefeed_core.exceptions import FireFeedException


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
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        if raise_last_error:
                            raise
                        return None
                    
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    logger.info(f"Retrying in {delay} seconds...")
                    
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
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        if raise_last_error:
                            raise
                        return None
                    
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    logger.info(f"Retrying in {delay} seconds...")
                    
                    asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            return None
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying on network errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
    """
    from firefeed_core.exceptions import ServiceUnavailableException
    
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(ServiceUnavailableException, asyncio.TimeoutError, ConnectionError),
        raise_last_error=True
    )


def retry_on_parsing_error(max_retries: int = 2, base_delay: float = 0.5):
    """
    Decorator for retrying on parsing errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
    """
    from firefeed_core.exceptions import ServiceException
    
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(ServiceException,),
        raise_last_error=True
    )