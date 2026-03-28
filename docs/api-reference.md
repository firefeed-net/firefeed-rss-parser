# FireFeed RSS Parser API Reference

This document provides detailed API reference for the FireFeed RSS Parser microservice.

## Table of Contents

1. [Health Endpoints](#health-endpoints)
2. [Metrics Endpoints](#metrics-endpoints)
3. [Service Endpoints](#service-endpoints)
4. [Error Handling](#error-handling)
5. [Authentication](#authentication)

## Health Endpoints

### GET /health

Get basic health status of the RSS Parser service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0",
  "uptime_seconds": 3600.0
}
```

**Status Codes:**
- `200` - Service is healthy
- `503` - Service is unhealthy

### GET /health/detailed

Get detailed health status including dependency information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0",
  "uptime_seconds": 3600.0,
  "dependencies": {
    "api": {
      "healthy": true,
      "status": "ok",
      "response_time": 0.1,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "database": {
      "healthy": true,
      "status": "ok",
      "connection_pool_size": 10,
      "active_connections": 2,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "storage": {
      "healthy": true,
      "status": "ok",
      "available_space_gb": 100,
      "used_space_gb": 25,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "translation": {
      "healthy": true,
      "status": "ok",
      "queue_size": 0,
      "supported_languages": ["en", "ru", "de"],
      "timestamp": "2024-01-01T12:00:00Z"
    }
  },
  "metrics": {
    "check_count": 100,
    "error_count": 5,
    "error_rate": 0.05,
    "avg_check_time": 0.1,
    "total_check_time": 10.0
  },
  "errors": []
}
```

**Status Codes:**
- `200` - Service is healthy
- `503` - Service or dependencies are unhealthy

## Metrics Endpoints

### GET /metrics

Get Prometheus metrics for monitoring and observability.

**Response:**
```
# HELP rss_parser_feeds_processed_total Total feeds processed
# TYPE rss_parser_feeds_processed_total counter
rss_parser_feeds_processed_total 100

# HELP rss_parser_items_processed_total Total items processed
# TYPE rss_parser_items_processed_total counter
rss_parser_items_processed_total 1000

# HELP rss_parser_duplicates_found_total Total duplicates found
# TYPE rss_parser_duplicates_found_total counter
rss_parser_duplicates_found_total 50

# HELP rss_parser_media_processed_total Total media processed
# TYPE rss_parser_media_processed_total counter
rss_parser_media_processed_total 200

# HELP rss_parser_processing_duration_seconds Processing duration
# TYPE rss_parser_processing_duration_seconds histogram
rss_parser_processing_duration_seconds_bucket{le="0.1"} 50
rss_parser_processing_duration_seconds_bucket{le="1.0"} 90
rss_parser_processing_duration_seconds_bucket{le="10.0"} 95
rss_parser_processing_duration_seconds_bucket{le="+Inf"} 100
rss_parser_processing_duration_seconds_count 100
rss_parser_processing_duration_seconds_sum 25.5

# HELP rss_parser_error_total Total errors
# TYPE rss_parser_error_total counter
rss_parser_error_total{type="feed_processing"} 5
rss_parser_error_total{type="duplicate_detection"} 2
rss_parser_error_total{type="media_processing"} 1

# HELP rss_parser_service_uptime_seconds Service uptime
# TYPE rss_parser_service_uptime_seconds gauge
rss_parser_service_uptime_seconds 3600.0

# HELP rss_parser_queue_size Queue size
# TYPE rss_parser_queue_size gauge
rss_parser_queue_size{queue="translation"} 5
```

**Status Codes:**
- `200` - Metrics retrieved successfully

## Service Endpoints

### GET /status

Get current service status and statistics.

**Response:**
```json
{
  "service": {
    "running": true,
    "uptime_seconds": 3600.0,
    "start_time": "2024-01-01T11:00:00Z",
    "total_processed_feeds": 50,
    "total_processed_items": 500,
    "total_errors": 10,
    "error_rate": 0.02
  },
  "rss_fetcher": {
    "fetch_count": 100,
    "error_count": 5,
    "error_rate": 0.05,
    "avg_fetch_time": 1.5,
    "total_fetch_time": 150.0,
    "max_concurrent_feeds": 10,
    "max_entries_per_feed": 50,
    "session_active": true
  },
  "duplicate_detector": {
    "check_count": 500,
    "duplicate_count": 50,
    "duplicate_rate": 0.1,
    "avg_check_time": 0.1,
    "total_check_time": 50.0,
    "similarity_threshold": 0.9,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "max_recent_items_check": 100,
    "cache_size": 1000
  },
  "translation_service": {
    "enabled": true,
    "translate_count": 200,
    "error_count": 2,
    "error_rate": 0.01,
    "avg_translate_time": 0.5,
    "total_translate_time": 100.0,
    "queue_size": 5,
    "processing": true,
    "default_source_lang": "auto",
    "target_languages": ["en", "ru", "de"],
    "max_text_length": 5000,
    "batch_size": 10,
    "timeout": 60
  },
  "api_client": {
    "service_id": "firefeed-rss-parser",
    "base_url": "http://firefeed-api:8000",
    "request_count": 200,
    "error_count": 5,
    "error_rate": 0.025,
    "avg_response_time": 0.2,
    "total_response_time": 40.0,
    "session_active": true
  },
  "health_checker": {
    "enabled": true,
    "check_count": 120,
    "error_count": 2,
    "error_rate": 0.017,
    "avg_check_time": 0.1,
    "total_check_time": 12.0,
    "check_interval_seconds": 30,
    "timeout_seconds": 10,
    "dependencies": ["api", "database", "storage"],
    "running": true,
    "last_check_time": "2024-01-01T12:00:00Z",
    "current_status": "healthy"
  }
}
```

**Status Codes:**
- `200` - Status retrieved successfully

### POST /process

Trigger immediate processing of all feeds.

**Request:**
```json
{
  "force": false
}
```

**Response:**
```json
{
  "status": "completed",
  "feeds_processed": 10,
  "items_processed": 100,
  "items_created": 95,
  "items_updated": 3,
  "duplicates_found": 2,
  "media_processed": 50,
  "errors": [],
  "duration_seconds": 15.5,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:00:15Z"
}
```

**Status Codes:**
- `200` - Processing completed successfully
- `500` - Processing failed

### GET /feeds

Get list of active RSS feeds being processed.

**Response:**
```json
{
  "feeds": [
    {
      "id": 1,
      "url": "https://feeds.bbci.co.uk/news/rss.xml",
      "name": "BBC News",
      "language": "en",
      "source_id": 1,
      "category_id": 1,
      "is_active": true,
      "cooldown_minutes": 60,
      "max_news_per_hour": 10,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T11:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10
}
```

**Status Codes:**
- `200` - Feeds retrieved successfully

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field1": "additional details",
      "field2": "more information"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SERVICE_UNAVAILABLE` | 503 | Service is temporarily unavailable |
| `AUTHENTICATION_FAILED` | 401 | Authentication failed |
| `AUTHORIZATION_FAILED` | 403 | Authorization failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `TIMEOUT_ERROR` | 504 | Request timeout |
| `NETWORK_ERROR` | 502 | Network error |

### Example Error Responses

#### Authentication Failed
```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Authentication failed for firefeed-rss-parser",
    "details": {
      "status": 401
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### Rate Limit Exceeded
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for firefeed-rss-parser",
    "details": {
      "status": 429,
      "retry_after": 60
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### Validation Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid RSS feed URL",
    "details": {
      "field": "url",
      "value": "invalid-url",
      "expected_format": "http://example.com/feed.xml"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Authentication

### Service-to-Service Authentication

The RSS Parser uses JWT tokens for service-to-service authentication with the FireFeed API.

**Required Headers:**
```
Authorization: Bearer <service-token>
X-Service-ID: firefeed-rss-parser
```

**Token Format:**
```json
{
  "service_id": "firefeed-rss-parser",
  "scopes": ["rss:read", "rss:write", "user:read"],
  "exp": 1704067200,
  "iat": 1704063600
}
```

**Scopes:**
- `rss:read` - Read RSS feeds and items
- `rss:write` - Create and update RSS feeds and items
- `user:read` - Read user information
- `translation:write` - Submit translations

### Configuration

Set the authentication token in environment variables:

```bash
export FIREFEED_API_TOKEN="your-jwt-token-here"
```

Or in Docker Compose:

```yaml
environment:
  - FIREFEED_API_TOKEN=your-jwt-token-here
```

### Token Management

- Tokens should be rotated regularly
- Use secure storage for tokens in production
- Monitor token usage and expiration
- Implement token refresh mechanisms

## Rate Limiting

### Default Limits

- **API Requests**: 1000 requests per minute
- **Feed Processing**: Configurable per feed
- **Translation Requests**: 100 requests per minute

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704067200
Retry-After: 60
```

### Handling Rate Limits

When rate limits are exceeded:

1. Service returns `429 Too Many Requests`
2. Retry after the specified delay
3. Implement exponential backoff
4. Monitor rate limit usage

## Monitoring and Observability

### Health Check Endpoints

- `/health` - Basic health check
- `/health/detailed` - Detailed health with dependencies

### Metrics Endpoints

- `/metrics` - Prometheus metrics

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### Structured Logging

All logs are in JSON format:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "rss-parser",
  "message": "Feed processed successfully",
  "feed_id": "123",
  "items_processed": 25,
  "duration_seconds": 1.234,
  "trace_id": "abc123"
}
```

## Security

### Security Headers

The service includes security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### Input Validation

All inputs are validated:

- URL format validation
- Content length limits
- SQL injection prevention
- XSS protection

### Network Security

- HTTPS recommended for production
- Firewall rules for service communication
- Network segmentation
- VPN for external access