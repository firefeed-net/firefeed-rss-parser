# FireFeed RSS Parser - Monitoring Guide

This document describes how to monitor the FireFeed RSS Parser microservice for optimal performance and reliability.

## Table of Contents

- [Overview](#overview)
- [Metrics](#metrics)
- [Health Checks](#health-checks)
- [Logging](#logging)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

Monitoring is crucial for maintaining the reliability and performance of the RSS Parser service. This guide covers all aspects of monitoring including metrics, health checks, logging, and alerting.

### Monitoring Stack

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alerting and notifications
- **structlog** - Structured logging
- **Health Checks** - Kubernetes readiness/liveness probes

## Metrics

### Prometheus Metrics

The service exposes Prometheus metrics on port 8080 at the `/metrics` endpoint.

#### Available Metrics

##### Counter Metrics

```promql
# Total number of feeds processed
rss_parser_feeds_processed_total

# Total number of items saved
rss_parser_items_saved_total

# Total number of errors
rss_parser_errors_total{
  error_type="network|parsing|validation|storage"
}

# Total number of duplicate items detected
rss_parser_duplicates_detected_total

# Total number of media items extracted
rss_parser_media_extracted_total{
  media_type="image|video|audio"
}
```

##### Histogram Metrics

```promql
# Time spent fetching RSS feeds
rss_parser_fetch_duration_seconds{
  feed_url="https://example.com/rss"
}

# Time spent parsing RSS content
rss_parser_parse_duration_seconds

# Time spent saving items
rss_parser_save_duration_seconds

# Time spent extracting media
rss_parser_media_extraction_duration_seconds

# HTTP request duration to FireFeed API
rss_parser_api_request_duration_seconds{
  endpoint="/api/v1/rss/items",
  method="POST",
  status_code="200"
}
```

##### Gauge Metrics

```promql
# Number of active HTTP connections
rss_parser_active_connections

# Number of concurrent feed processing tasks
rss_parser_concurrent_tasks

# Memory usage
rss_parser_memory_usage_bytes

# CPU usage
rss_parser_cpu_usage_percent
```

### Custom Metrics

#### Business Metrics

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
feeds_processed = Counter('rss_parser_feeds_processed_total', 
                         'Total feeds processed', 
                         ['feed_name', 'feed_category'])

items_saved = Counter('rss_parser_items_saved_total', 
                     'Total items saved', 
                     ['feed_name'])

processing_time = Histogram('rss_parser_processing_duration_seconds', 
                           'Time spent processing feeds',
                           ['feed_name'])

active_tasks = Gauge('rss_parser_concurrent_tasks', 
                    'Number of concurrent processing tasks')
```

#### Usage Examples

```python
# Increment counters
feeds_processed.labels(feed_name="TechCrunch", feed_category="Technology").inc()
items_saved.labels(feed_name="TechCrunch").inc()

# Record processing time
start_time = time.time()
# ... processing logic ...
processing_time.labels(feed_name="TechCrunch").observe(time.time() - start_time)

# Update gauge
active_tasks.inc()
# ... task execution ...
active_tasks.dec()
```

## Health Checks

### Health Check Endpoints

The service provides several health check endpoints on port 8081:

#### Liveness Probe
```bash
GET /live
```

**Purpose:** Determine if the service should be restarted.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2023-01-01T00:00:00Z",
  "uptime": 3600
}
```

#### Readiness Probe
```bash
GET /ready
```

**Purpose:** Determine if the service is ready to accept traffic.

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

#### Health Check
```bash
GET /health
```

**Purpose:** Comprehensive health check of all components.

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

### Health Check Implementation

```python
from fastapi import FastAPI
from starlette.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    # Check API connectivity
    api_status = await check_api_health()
    
    # Check network connectivity
    network_status = await check_network_health()
    
    overall_status = "healthy" if all([
        api_status["status"] == "healthy",
        network_status["status"] == "connected"
    ]) else "unhealthy"
    
    return JSONResponse(
        status_code=200 if overall_status == "healthy" else 503,
        content={
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": api_status,
                "connectivity": network_status
            }
        }
    )
```

## Logging

### Structured Logging

The service uses structlog for structured logging with JSON output.

#### Log Configuration

```python
import structlog
import logging

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure logging level
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
```

#### Log Examples

```python
import structlog

logger = structlog.get_logger(__name__)

# Info logging
logger.info(
    "feed_processed",
    feed_name="TechCrunch",
    feed_url="https://techcrunch.com/feed/",
    items_processed=10,
    processing_time=2.5
)

# Error logging
logger.error(
    "feed_processing_failed",
    feed_name="TechCrunch",
    error_type="NetworkError",
    error_message="Timeout connecting to RSS feed",
    retry_count=3
)

# Debug logging
logger.debug(
    "item_duplicate_skipped",
    item_title="New iPhone Release",
    duplicate_reason="guid_match",
    existing_item_id=12345
)
```

#### Log Levels

- **DEBUG** - Detailed debugging information
- **INFO** - General information about service operation
- **WARNING** - Warning messages that don't stop the service
- **ERROR** - Error messages that affect service operation
- **CRITICAL** - Critical errors that may cause service shutdown

### Log Aggregation

#### ELK Stack Integration

```yaml
# Filebeat configuration
filebeat.inputs:
- type: docker
  containers.ids:
    - "rss-parser-*"
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"

output.logstash:
  hosts: ["logstash:5044"]
```

#### Fluentd Configuration

```xml
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match rss.parser.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name rss-parser-logs
  type_name _doc
</match>
```

## Alerting

### AlertManager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'mail@firefeed.net'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'

- name: 'critical-alerts'
  email_configs:
  - to: 'mail@firefeed.net'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts-critical'
    title: 'Critical Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'warning-alerts'
  email_configs:
  - to: 'mail@firefeed.net'
    subject: 'WARNING: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

### Prometheus Alerts

```yaml
# alerts.yml
groups:
- name: rss-parser-alerts
  rules:
  
  # High error rate
  - alert: HighErrorRate
    expr: rate(rss_parser_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in RSS parser"
      description: "Error rate is {{ $value }} errors per second"
  
  # Service down
  - alert: ServiceDown
    expr: up{job="rss-parser"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "RSS parser service is down"
      description: "Service rss-parser has been down for more than 1 minute"
  
  # High processing time
  - alert: HighProcessingTime
    expr: histogram_quantile(0.95, rate(rss_parser_processing_duration_seconds_bucket[5m])) > 30
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High processing time in RSS parser"
      description: "95th percentile processing time is {{ $value }} seconds"
  
  # No feeds processed
  - alert: NoFeedsProcessed
    expr: rate(rss_parser_feeds_processed_total[5m]) == 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "No feeds are being processed"
      description: "No feeds have been processed in the last 10 minutes"
  
  # High duplicate rate
  - alert: HighDuplicateRate
    expr: rate(rss_parser_duplicates_detected_total[5m]) / rate(rss_parser_items_saved_total[5m]) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High duplicate detection rate"
      description: "More than 50% of items are being detected as duplicates"
  
  # Memory usage high
  - alert: HighMemoryUsage
    expr: rss_parser_memory_usage_bytes / rss_parser_memory_limit_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }}"
  
  # API errors
  - alert: HighAPIErrorRate
    expr: rate(rss_parser_api_errors_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High API error rate"
      description: "API error rate is {{ $value }} errors per second"
```

## Dashboards

### Grafana Dashboard

#### Dashboard Configuration

```json
{
  "dashboard": {
    "id": null,
    "title": "RSS Parser Dashboard",
    "tags": ["rss", "parser", "firefeed"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Feeds Processed",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rss_parser_feeds_processed_total[5m])",
            "legendFormat": "Feeds/min"
          }
        ],
        "yAxes": [
          {
            "label": "Feeds per minute",
            "min": 0
          }
        ],
        "xAxis": {
          "show": true
        }
      },
      {
        "id": 2,
        "title": "Items Saved",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rss_parser_items_saved_total[5m])",
            "legendFormat": "Items/min"
          }
        ],
        "yAxes": [
          {
            "label": "Items per minute",
            "min": 0
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rss_parser_errors_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ],
        "yAxes": [
          {
            "label": "Errors per second",
            "min": 0
          }
        ],
        "alert": {
          "conditions": [
            {
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "last"
              },
              "type": "gt"
            }
          ],
          "executionErrorState": "alerting",
          "for": "2m",
          "frequency": "10s",
          "handler": 1,
          "name": "High Error Rate",
          "noDataState": "no_data",
          "notifications": []
        }
      },
      {
        "id": 4,
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(rss_parser_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(rss_parser_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(rss_parser_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds",
            "min": 0
          }
        ]
      },
      {
        "id": 5,
        "title": "Active Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rss_parser_active_connections",
            "legendFormat": "Connections"
          }
        ],
        "valueName": "current",
        "format": "short"
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

#### Dashboard Panels

1. **Feeds Processed** - Rate of feeds being processed
2. **Items Saved** - Rate of items being saved to the database
3. **Error Rate** - Rate of errors occurring in the service
4. **Processing Time** - Latency percentiles for processing operations
5. **Active Connections** - Number of active HTTP connections
6. **Memory Usage** - Memory consumption metrics
7. **CPU Usage** - CPU utilization metrics
8. **Duplicate Detection** - Rate of duplicate items detected

### Custom Dashboards

#### Feed-Specific Dashboard

```json
{
  "dashboard": {
    "title": "Feed Performance Dashboard",
    "panels": [
      {
        "title": "TechCrunch Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rss_parser_feeds_processed_total{feed_name='TechCrunch'}[5m])",
            "legendFormat": "TechCrunch Feeds/min"
          }
        ]
      }
    ]
  }
}
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

#### Throughput Metrics

```promql
# Feeds processed per minute
rate(rss_parser_feeds_processed_total[5m]) * 60

# Items saved per minute
rate(rss_parser_items_saved_total[5m]) * 60

# Media extracted per minute
rate(rss_parser_media_extracted_total[5m]) * 60
```

#### Latency Metrics

```promql
# Average processing time
rate(rss_parser_processing_duration_seconds_sum[5m]) / rate(rss_parser_processing_duration_seconds_count[5m])

# 95th percentile processing time
histogram_quantile(0.95, rate(rss_parser_processing_duration_seconds_bucket[5m]))

# 99th percentile processing time
histogram_quantile(0.99, rate(rss_parser_processing_duration_seconds_bucket[5m]))
```

#### Error Metrics

```promql
# Error rate
rate(rss_parser_errors_total[5m])

# Error rate by type
rate(rss_parser_errors_total[5m]) by (error_type)

# Success rate
1 - (rate(rss_parser_errors_total[5m]) / rate(rss_parser_feeds_processed_total[5m]))
```

#### Resource Metrics

```promql
# Memory usage
rss_parser_memory_usage_bytes

# CPU usage
rss_parser_cpu_usage_percent

# Active connections
rss_parser_active_connections

# Concurrent tasks
rss_parser_concurrent_tasks
```

### Performance Benchmarks

#### SLA Targets

- **Availability:** 99.9% uptime
- **Processing Time:** 95th percentile < 30 seconds
- **Error Rate:** < 1% of total requests
- **Throughput:** Process 1000+ feeds per hour

#### Performance Testing

```python
import asyncio
import time
from prometheus_client import Gauge

# Performance test metrics
test_duration = Gauge('performance_test_duration_seconds', 'Duration of performance test')
test_throughput = Gauge('performance_test_throughput', 'Throughput during test')

async def performance_test():
    start_time = time.time()
    
    # Simulate processing 100 feeds
    tasks = []
    for i in range(100):
        task = process_test_feed(f"feed_{i}")
        tasks.append(task)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    throughput = 100 / duration
    
    test_duration.set(duration)
    test_throughput.set(throughput)
    
    print(f"Processed 100 feeds in {duration:.2f} seconds")
    print(f"Average throughput: {throughput:.2f} feeds/second")
```

## Troubleshooting

### Common Issues

#### 1. High Error Rate

**Symptoms:**
- Error rate metrics showing high values
- Many failed requests in logs

**Diagnosis:**
```bash
# Check error metrics
curl http://localhost:8080/metrics | grep rss_parser_errors_total

# Check error logs
grep "ERROR" /var/log/rss-parser.log

# Check specific error types
curl http://localhost:8080/metrics | grep error_type
```

**Solutions:**
- Check API key validity
- Verify network connectivity
- Increase timeout values
- Check rate limiting

#### 2. Slow Processing

**Symptoms:**
- High processing time metrics
- Slow response times

**Diagnosis:**
```bash
# Check processing time percentiles
curl http://localhost:8080/metrics | grep processing_duration

# Check resource usage
top -p $(pgrep -f rss-parser)

# Check for blocking operations
strace -p $(pgrep -f rss-parser)
```

**Solutions:**
- Optimize network configuration
- Increase concurrent processing
- Check database performance
- Review algorithm efficiency

#### 3. Memory Leaks

**Symptoms:**
- Increasing memory usage over time
- Service restarts due to OOM

**Diagnosis:**
```bash
# Monitor memory usage
watch -n 1 'ps aux | grep rss-parser'

# Check memory metrics
curl http://localhost:8080/metrics | grep memory_usage

# Profile memory usage
python -m memory_profiler your_script.py
```

**Solutions:**
- Fix memory leaks in code
- Implement proper cleanup
- Increase memory limits
- Add memory monitoring

#### 4. High CPU Usage

**Symptoms:**
- High CPU utilization
- Slow processing

**Diagnosis:**
```bash
# Check CPU usage
top -p $(pgrep -f rss-parser)

# Check CPU metrics
curl http://localhost:8080/metrics | grep cpu_usage

# Profile CPU usage
python -m cProfile -o profile.stats your_script.py
```

**Solutions:**
- Optimize algorithms
- Add caching
- Reduce processing frequency
- Scale horizontally

### Debugging Tools

#### 1. Prometheus Query Console

Access Prometheus web UI to query metrics:

```promql
# Check current error rate
rate(rss_parser_errors_total[5m])

# Check processing time percentiles
histogram_quantile(0.95, rate(rss_parser_processing_duration_seconds_bucket[5m]))

# Check service availability
up{job="rss-parser"}
```

#### 2. Grafana Dashboards

Use Grafana dashboards to visualize metrics:

- **Overview Dashboard** - High-level service metrics
- **Performance Dashboard** - Detailed performance metrics
- **Error Dashboard** - Error tracking and analysis
- **Resource Dashboard** - Resource utilization metrics

#### 3. Log Analysis

Use log analysis tools:

```bash
# Search for errors in logs
grep "ERROR" /var/log/rss-parser.log

# Analyze log patterns
awk '/ERROR/ {print $NF}' /var/log/rss-parser.log | sort | uniq -c

# Real-time log monitoring
tail -f /var/log/rss-parser.log | grep ERROR
```

## Best Practices

### 1. Metric Naming

- Use consistent naming conventions
- Include relevant labels for filtering
- Avoid high cardinality labels
- Use appropriate metric types

### 2. Alert Configuration

- Set appropriate thresholds
- Use meaningful alert messages
- Configure proper alert routing
- Test alert notifications

### 3. Dashboard Design

- Focus on actionable metrics
- Use appropriate visualization types
- Group related metrics together
- Set appropriate time ranges

### 4. Log Management

- Use structured logging
- Include relevant context
- Set appropriate log levels
- Implement log rotation

### 5. Performance Monitoring

- Monitor key performance indicators
- Set up performance baselines
- Track performance trends
- Regular performance testing

### 6. Incident Response

- Define clear escalation paths
- Document common troubleshooting steps
- Practice incident response procedures
- Conduct post-incident reviews

### 7. Capacity Planning

- Monitor resource utilization trends
- Plan for growth
- Set up auto-scaling
- Regular capacity reviews

### 8. Security Monitoring

- Monitor for security events
- Track authentication failures
- Monitor for unusual patterns
- Set up security alerts

## Conclusion

Effective monitoring is essential for maintaining a reliable and performant RSS parser service. By implementing comprehensive metrics, health checks, logging, and alerting, you can ensure your service remains healthy and responsive to issues.

Regular review and optimization of your monitoring setup will help you catch issues early, respond quickly to incidents, and maintain high service quality for your users.