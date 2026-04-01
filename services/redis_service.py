import os
import logging
from typing import Optional, Union
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from config.firefeed_rss_parser_config import get_config

logger = logging.getLogger(__name__)


class RedisService:
    """Async Redis service for duplicate caching."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or get_config().redis_url
        self.pool: Optional[aioredis.Redis] = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def start(self):
        """Start Redis pool."""
        try:
            self.pool = await aioredis.from_url(
                self.redis_url,
                minsize=1,
                maxsize=5,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Redis pool started: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to start Redis pool: {e}")
            raise
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self.pool:
            return None
        try:
            value = await self.pool.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis GET {key} failed: {e}")
            return None
    
    async def set(self, key: str, value: Union[str, int], ttl: int = 3600) -> bool:
        """Set key-value with TTL."""
        if not self.pool:
            return False
        try:
            await self.pool.set(key, str(value), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis SET {key} failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        if not self.pool:
            return False
        try:
            result = await self.pool.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE {key} failed: {e}")
            return False
    
    async def cleanup(self):
        """Close Redis pool."""
        if self.pool:
            try:
                await self.pool.close()
                await self.pool.wait_closed()
                logger.info("Redis pool closed")
            except Exception as e:
                logger.error(f"Redis cleanup failed: {e}")
            finally:
                self.pool = None


async def get_redis_service(redis_url: Optional[str] = None) -> RedisService:
    """Get Redis service instance."""
    service = RedisService(redis_url)
    await service.start()
    return service

