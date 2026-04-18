"""Health check service for FireFeed RSS Parser."""

import httpx
import logging
from typing import Dict, Any
from config.firefeed_rss_parser_config import get_config
config = get_config()
from firefeed_core.exceptions import ServiceUnavailableException


logger = logging.getLogger(__name__)


class HealthChecker:
    """Service for health checks and monitoring."""
    
    def __init__(self, api_client=None):
        """
        Initialize health checker.
        
        Args:
            api_client: FireFeed API client (optional)
        """
        self.api_client = api_client
    
    async def check_api_health(self) -> Dict[str, Any]:
        """
        Check FireFeed API health.
        
        Returns:
            Health check result
        """
        if not self.api_client:
            return {"status": "error", "message": "API client not available"}
        
        try:
            # Try to get categories as a health check
            categories = await self.api_client.get_categories(page=1, size=1)
            return {
                "status": "healthy",
                "message": "API is accessible",
                "categories_count": len(categories)
            }
        except ServiceUnavailableException as e:
            return {
                "status": "unhealthy",
                "message": f"API health check failed: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error during health check: {e}"
            }
    
    async def check_connectivity(self) -> Dict[str, Any]:
        """
        Check network connectivity.
        
        Returns:
            Connectivity check result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    config.base_url,
                    timeout=5.0
                )
                response.raise_for_status()
                
                return {
                    "status": "connected",
                    "message": "Network connectivity is OK",
                    "status_code": response.status_code
                }
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "message": "Connection timeout"
            }
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "message": f"HTTP error {e.response.status_code}",
                "status_code": e.response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connectivity check failed: {e}"
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status.
        
        Returns:
            Combined health status
        """
        api_health = await self.check_api_health()
        connectivity = await self.check_connectivity()
        
        overall_status = "healthy"
        if api_health["status"] != "healthy" or connectivity["status"] != "connected":
            overall_status = "degraded"
        
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        return {
            "status": overall_status,
            "timestamp": timestamp,
            "services": {
                "api": api_health,
                "connectivity": connectivity
            }
        }