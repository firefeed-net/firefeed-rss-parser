import asyncio
import logging
from typing import Callable, Any
from firefeed_core.exceptions.api_exceptions import RateLimitException

logger = logging.getLogger(__name__)

def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator for network errors."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}, retry in {delay}s")
                        await asyncio.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

async def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff for general errors."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, backoff {delay}s")
                        await asyncio.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

def retry_on_parsing_error(max_retries: int = 2, base_delay: float = 0.3):
    """Retry decorator for parsing errors."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if 'parser' in str(e).lower() or 'html' in str(e).lower():
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            logger.debug(f"Parsing error (attempt {attempt + 1}): {e}, retry in {delay}s")
                            await asyncio.sleep(delay)
                        else:
                            logger.warning(f"Max parsing retries exceeded: {e}")
                            raise
                    else:
                        raise
            return None
        return wrapper
    return decorator


def retry_on_rate_limit(max_retries: int = 5, base_delay: float = 2.0):
    """Retry decorator for rate limits with retry_after support."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RateLimitException as e:
                    retry_after = getattr(e.details, 'retry_after', None) or 46
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit (attempt {attempt + 1}): wait {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        logger.error(f"Max rate limit retries: {e}")
                        raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

