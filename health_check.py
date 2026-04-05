"""
Health Check Module for FireFeed RSS Parser

Provides health check endpoints and monitoring functionality.
"""

import asyncio
import logging
import time
import os
import json
from typing import Dict, Any, Optional
from aiohttp import web

logger = logging.getLogger(__name__)

# Global start time for uptime tracking
_start_time = time.time()


# aiohttp request handlers
async def health_handler(request: web.Request) -> web.Response:
    """Health check endpoint"""
    body = {
        "status": "healthy",
        "service": "firefeed-rss-parser",
        "uptime_seconds": time.time() - _start_time,
        "timestamp": time.time()
    }
    return web.json_response(body)


async def readiness_handler(request: web.Request) -> web.Response:
    """Readiness check endpoint"""
    body = {
        "ready": True,
        "reason": "Service ready"
    }
    return web.json_response(body)


async def liveness_handler(request: web.Request) -> web.Response:
    """Liveness check endpoint"""
    body = {
        "alive": True,
        "service": "firefeed-rss-parser",
        "uptime_seconds": time.time() - _start_time
    }
    return web.json_response(body)


async def metrics_handler(request: web.Request) -> web.Response:
    """Metrics endpoint for Prometheus"""
    metrics_text = (
        "# HELP rss_parser_up Service availability\n"
        "# TYPE rss_parser_up gauge\n"
        "rss_parser_up 1\n"
        "# HELP rss_parser_uptime_seconds Service uptime\n"
        "# TYPE rss_parser_uptime_seconds counter\n"
        f"rss_parser_uptime_seconds {time.time() - _start_time}\n"
    )
    return web.Response(text=metrics_text, content_type="text/plain")


def create_health_app() -> web.Application:
    """Create and configure the aiohttp health check application"""
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_get('/ready', readiness_handler)
    app.router.add_get('/live', liveness_handler)
    app.router.add_get('/metrics', metrics_handler)
    return app


async def start_health_server(host: str = "0.0.0.0", port: int = 8081) -> web.AppRunner:
    """Start the health check HTTP server in the background"""
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health check server started on {host}:{port}")
    return runner