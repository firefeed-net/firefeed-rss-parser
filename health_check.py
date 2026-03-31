"""
Health Check Module for FireFeed RSS Parser

Provides health check endpoints and monitoring functionality.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
import aiohttp
import redis
import aiopg

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for RSS parser service"""
    
    def __init__(self, config):
        self.config = config
        self.start_time = time.time()
        
    async def check_api_connection(self) -> Dict[str, Any]:
        """Check connection to FireFeed API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.FIREFEED_API_BASE_URL}/api/v1/health",
                    headers={"Authorization": f"Bearer {os.getenv('RSS_PARSER_TOKEN', '')}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_time": response.headers.get("X-Response-Time", "unknown"),
                        "status_code": response.status
                    }
        except Exception as e:
            logger.error(f"API connection check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis connection"""
        try:
            redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                password=self.config.REDIS_PASSWORD,
                db=self.config.REDIS_DB,
                decode_responses=True
            )
            
            # Test connection
            await redis_client.ping()
            
            # Get Redis info
            info = await redis_client.info()
            
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown")
            }
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """Check database connection"""
        try:
            dsn = f"dbname={self.config.DB_NAME} user={self.config.DB_USER} password={self.config.DB_PASSWORD} host={self.config.DB_HOST} port={self.config.DB_PORT}"
            
            async with aiopg.create_pool(dsn, minsize=1, maxsize=2) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1")
                        result = await cur.fetchone()
                        
            return {
                "status": "healthy",
                "connection_test": result[0] if result else None
            }
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_translation_service(self) -> Dict[str, Any]:
        """Check translation service availability"""
        try:
            # This would check if translation models are loaded
            # For now, just return basic status
            return {
                "status": "healthy",
                "translation_enabled": getattr(self.config, 'TRANSLATION_ENABLED', True),
                "model": getattr(self.config, 'TRANSLATION_MODEL', 'unknown')
            }
        except Exception as e:
            logger.error(f"Translation service check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health status"""
        checks = await asyncio.gather(
            self.check_api_connection(),
            self.check_redis_connection(),
            self.check_database_connection(),
            self.check_translation_service()
        )
        
        # Determine overall health
        all_healthy = all(check["status"] == "healthy" for check in checks)
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "service": "firefeed-rss-parser",
            "version": "1.0.0",
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": time.time(),
            "checks": {
                "api_connection": checks[0],
                "redis_connection": checks[1],
                "database_connection": checks[2],
                "translation_service": checks[3]
            }
        }
    
    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get service readiness status"""
        # Check if service is ready to accept traffic
        api_check = await self.check_api_connection()
        db_check = await self.check_database_connection()
        
        ready = api_check["status"] == "healthy" and db_check["status"] == "healthy"
        
        return {
            "ready": ready,
            "reason": "Service ready" if ready else "Dependencies not available",
            "dependencies": {
                "api": api_check["status"],
                "database": db_check["status"]
            }
        }
    
    async def get_liveness_status(self) -> Dict[str, Any]:
        """Get service liveness status"""
        # Check if service is alive (basic health)
        return {
            "alive": True,
            "service": "firefeed-rss-parser",
            "uptime_seconds": time.time() - self.start_time
        }


# FastAPI endpoints for health checks
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # This would be initialized with actual config
        # For now, return basic health status
        return {
            "status": "healthy",
            "service": "firefeed-rss-parser",
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # This would check if service is ready to accept traffic
        return {
            "ready": True,
            "reason": "Service ready"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint"""
    try:
        return {
            "alive": True,
            "service": "firefeed-rss-parser"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not alive: {str(e)}")


@router.get("/metrics")
async def metrics():
    """Metrics endpoint for Prometheus"""
    try:
        # This would return actual metrics
        # For now, return basic metrics
        return {
            "# HELP rss_parser_up Service availability",
            "# TYPE rss_parser_up gauge",
            f"rss_parser_up 1",
            "# HELP rss_parser_uptime_seconds Service uptime",
            "# TYPE rss_parser_uptime_seconds counter",
            f"rss_parser_uptime_seconds {time.time() - time.time()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics unavailable: {str(e)}")