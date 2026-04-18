import os
import logging
from typing import Optional, Union
import re
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from config.firefeed_rss_parser_config import get_config

logger = logging.getLogger(__name__)


class RedisService:
    """Async Redis service for duplicate caching."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self.pool: Optional[aioredis.Redis] = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    def _sanitize_url_for_log(self, url: str) -> str:
        """Mask password in URL for safe logging."""
        if '@' in url:
            return re.sub(r'(:[^@]+)@', ':***@', url)
        return url
    
    async def start(self):
        """Start Redis pool."""
        try:
            if self.redis_url:
                # Legacy: use provided URL (may contain password)
                connection_url = self.redis_url
                self.pool = await aioredis.from_url(
                    connection_url,
                    minsize=1,
                    maxsize=5,
                    encoding="utf-8",
                    decode_responses=True
                )
                safe_url = self._sanitize_url_for_log(connection_url)
                logger.info(f"Redis pool started (URL): {safe_url}")
            else:
                # Use config with separate parameters (password not in URL)
                config = get_config()
                pool = aioredis.ConnectionPool(
                    host=config.redis_host,
                    port=config.redis_port,
                    password=config.redis_password,
                    db=config.redis_db,
                    max_connections=5,
                    encoding='utf-8',
                    decode_responses=True
                )
                self.pool = aioredis.Redis(connection_pool=pool)
                logger.info(f"Redis pool started: {config.redis_host}:{config.redis_port}")
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
                if hasattr(self.pool, 'wait_closed'):
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
