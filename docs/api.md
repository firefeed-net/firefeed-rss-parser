# FireFeed RSS Parser - API Documentation

This document describes the API endpoints and interfaces provided by the FireFeed RSS Parser microservice.

## Table of Contents

- [Overview](#overview)
- [Health Check Endpoints](#health-check-endpoints)
- [Metrics Endpoint](#metrics-endpoint)
- [Configuration API](#configuration-api)
- [Service Interfaces](#service-interfaces)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The FireFeed RSS Parser microservice provides several endpoints for monitoring, health checking, and configuration. All endpoints are designed to be used by monitoring systems, orchestration platforms (like Kubernetes), and administrative tools.

## Health Check Endpoints

### Readiness Probe

**Endpoint:** `GET /ready`

**Purpose:** Check if the service is ready to accept traffic.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2023-01-01T00:00:00Z",
  "details": {
    "api_connection": "healthy",
    "database_connection": "healthy"
  }
}
```

**Status Codes:**
- `200` - Service is ready
- `503` - Service is not ready

### Liveness Probe

**Endpoint:** `GET /live`

**Purpose:** Check if the service is alive and should be restarted.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2023-01-01T00:00:00Z",
  "uptime": 3600
}
```

**Status Codes:**
- `200` - Service is alive
- `503` - Service is not alive and should be restarted

### Health Check

**Endpoint:** `GET /health`

**Purpose:** Comprehensive health check of all service components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "services": {
    "api": {
      "status": "healthy",
      "message": "API is accessible",
      "categories_count": 5
    },
    "connectivity": {
      "status": "connected",
      "message": "Network connectivity is OK",
      "status_code": 200
    }
  }
}
```

**Status Codes:**
- `200` - All services are healthy
- `503` - One or more services are unhealthy

## Metrics Endpoint

### Prometheus Metrics

**Endpoint:** `GET /metrics`

**Purpose:** Expose metrics for Prometheus monitoring.

**Response:** Prometheus format metrics

**Available Metrics:**
- `rss_parser_feeds_processed_total` - Total number of feeds processed
- `rss_parser_items_saved_total` - Total number of items saved
- `rss_parser_fetch_duration_seconds` - Time spent fetching RSS feeds
- `rss_parser_parse_duration_seconds` - Time spent parsing RSS content
- `rss_parser_errors_total` - Total number of errors
- `rss_parser_active_connections` - Number of active HTTP connections

**Example:**
```
# HELP rss_parser_feeds_processed_total Total number of feeds processed
# TYPE rss_parser_feeds_processed_total counter
rss_parser_feeds_processed_total 150

# HELP rss_parser_items_saved_total Total number of items saved
# TYPE rss_parser_items_saved_total counter
rss_parser_items_saved_total 1200

# HELP rss_parser_fetch_duration_seconds Time spent fetching RSS feeds
# TYPE rss_parser_fetch_duration_seconds histogram
rss_parser_fetch_duration_seconds_bucket{le="0.1"} 50
rss_parser_fetch_duration_seconds_bucket{le="0.5"} 120
rss_parser_fetch_duration_seconds_bucket{le="1.0"} 145
rss_parser_fetch_duration_seconds_bucket{le="+Inf"} 150
rss_parser_fetch_duration_seconds_count 150
rss_parser_fetch_duration_seconds_sum 45.32
```

## Configuration API

### Get Configuration

**Endpoint:** `GET /config`

**Purpose:** Retrieve current service configuration (for debugging).

**Response:**
```json
{
  "firefeed": {
    "base_url": "http://localhost:8000",
    "api_key": "****",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0
  },
  "service": {
    "name": "rss-parser",
    "log_level": "INFO",
    "max_concurrent_feeds": 10,
    "fetch_timeout": 30.0,
    "parser_timeout": 10.0,
    "storage_timeout": 30.0,
    "media_timeout": 15.0,
    "duplicate_check_timeout": 5.0
  },
  "monitoring": {
    "enable_metrics": true,
    "metrics_port": 8080,
    "health_check_port": 8081,
    "metrics_path": "/metrics",
    "health_path": "/health",
    "readiness_path": "/ready",
    "liveness_path": "/live"
  },
  "security": {
    "api_key_required": true,
    "rate_limit_enabled": true,
    "rate_limit_requests": 100,
    "rate_limit_window": 60,
    "allowed_hosts": ["localhost", "127.0.0.1"]
  }
}
```

**Status Codes:**
- `200` - Configuration retrieved successfully

## Service Interfaces

### RSS Manager Interface

The main service interface for processing RSS feeds.

```python
class RSSManager:
    async def process_feed(self, feed: RSSFeed) -> bool:
        """Process a single RSS feed."""
        
    async def cleanup(self):
        """Cleanup resources."""
```

### RSS Fetcher Interface

Interface for fetching RSS feed content.

```python
class RSSFetcher:
    async def fetch_rss(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Any] = None,
        proxies: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        allow_redirects: bool = True
    ) -> str:
        """Fetch RSS feed content."""
```

### RSS Parser Interface

Interface for parsing RSS/Atom content.

```python
class RSSParser:
    async def parse_rss(self, rss_content: str) -> Optional[Dict[str, Any]]:
        """Parse RSS/Atom feed content."""
        
    async def parse_multiple_feeds(
        self, 
        feeds_content: List[str]
    ) -> List[Optional[Dict[str, Any]]]:
        """Parse multiple RSS feeds concurrently."""
```

### RSS Storage Interface

Interface for storing RSS items.

```python
class RSSStorage:
    async def save_rss_item(self, item: RSSItem) -> int:
        """Save RSS item to storage."""
        
    async def update_rss_item(self, item_id: int, item: RSSItem) -> bool:
        """Update existing RSS item."""
        
    async def delete_rss_item(self, item_id: int) -> bool:
        """Delete RSS item."""
```

### Media Extractor Interface

Interface for extracting media content.

```python
class MediaExtractor:
    async def extract_media(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract media content from URL."""
```

### Duplicate Detector Interface

Interface for detecting duplicate RSS items.

```python
class DuplicateDetector:
    async def is_duplicate(self, item: RSSItem) -> bool:
        """Check if RSS item is a duplicate."""
```

## Error Handling

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid RSS feed URL",
    "details": {
      "field": "url",
      "value": "invalid-url",
      "code": "INVALID_URL"
    },
    "timestamp": "2023-01-01T00:00:00Z"
  }
}
```

### Error Types

#### NetworkError
Raised for network-related issues.

```json
{
  "error": {
    "type": "NetworkError",
    "message": "Request timeout",
    "details": {
      "url": "https://example.com/rss",
      "timeout": 30
    }
  }
}
```

#### ParsingError
Raised for parsing-related issues.

```json
{
  "error": {
    "type": "ParsingError",
    "message": "Failed to parse RSS content",
    "details": {
      "content_preview": "<?xml version='1.0'?>...",
      "parser_error": "XML syntax error"
    }
  }
}
```

#### ValidationError
Raised for validation issues.

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid RSS content format",
    "details": {
      "field": "content",
      "value": "Invalid content",
      "code": "INVALID_FORMAT"
    }
  }
}
```

#### StorageError
Raised for storage-related issues.

```json
{
  "error": {
    "type": "StorageError",
    "message": "Failed to save RSS item",
    "details": {
      "operation": "create",
      "original_error": "Database connection lost"
    }
  }
}
```

## Examples

### Kubernetes Health Checks

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rss-parser
spec:
  template:
    spec:
      containers:
      - name: rss-parser
        image: firefeed/rss-parser:latest
        ports:
        - containerPort: 8080
        - containerPort: 8081
        livenessProbe:
          httpGet:
            path: /live
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Prometheus Monitoring

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rss-parser'
    static_configs:
      - targets: ['rss-parser:8080']
    metrics_path: /metrics
    scrape_interval: 30s
```

### Grafana Dashboard Queries

```promql
# Feeds processed per minute
rate(rss_parser_feeds_processed_total[5m]) * 60

# Average fetch duration
rate(rss_parser_fetch_duration_seconds_sum[5m]) / rate(rss_parser_fetch_duration_seconds_count[5m])

# Error rate
rate(rss_parser_errors_total[5m])

# Items saved per minute
rate(rss_parser_items_saved_total[5m]) * 60
```

### Health Check Script

```bash
#!/bin/bash

HEALTH_URL="http://localhost:8081/health"
READY_URL="http://localhost:8081/ready"
LIVE_URL="http://localhost:8081/live"

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $1)
    if [ $response -eq 200 ]; then
        echo "✓ $2 is healthy"
        return 0
    else
        echo "✗ $2 is unhealthy (HTTP $response)"
        return 1
    fi
}

echo "Checking RSS Parser health..."
check_health $HEALTH_URL "Health check"
check_health $READY_URL "Readiness probe"
check_health $LIVE_URL "Liveness probe"
```

## Rate Limiting

The service implements rate limiting to protect against abuse:

- **Default limit:** 100 requests per 60 seconds per IP
- **Headers:** Rate limit information is included in response headers
- **Burst capacity:** Configurable burst capacity for handling traffic spikes

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Security

### API Key Authentication

For protected endpoints, include the API key in the request header:

```
X-API-Key: your-api-key-here
```

### CORS

Cross-Origin Resource Sharing is configured to allow requests from trusted domains:

```
Access-Control-Allow-Origin: https://your-domain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, X-API-Key
```

## Troubleshooting

### Common Issues

1. **Health check failing**
   - Check API connectivity
   - Verify configuration settings
   - Check logs for error messages

2. **High error rate**
   - Review network connectivity
   - Check feed URLs for validity
   - Monitor resource usage

3. **Slow performance**
   - Check fetch timeout settings
   - Monitor concurrent feed processing
   - Review database performance

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python -m firefeed_rss_parser
```

### Log Analysis

Key log messages to monitor:

```
INFO: Successfully processed feed: TechCrunch (https://techcrunch.com/feed/)
WARNING: Duplicate item found: New iPhone Release
ERROR: Network error fetching RSS feed: Timeout
DEBUG: Processing item: Article Title
```

## Support

For support and questions:

- **Documentation:** [README.md](../README.md)
- **Issues:** [GitHub Issues](https://github.com/firefeed-net/firefeed-rss-parser/issues)
- **Email:** mail@firefeed.nwt