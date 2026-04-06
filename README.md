# FireFeed RSS Parser

**Production-ready microservice for RSS feed parsing** within the FireFeed platform.

> **Note**: This service is part of the [FireFeed platform](https://github.com/firefeed-net/firefeed) microservices architecture. It can be run standalone or as part of the complete FireFeed ecosystem with [API](https://github.com/firefeed-net/firefeed-api) and [Telegram Bot](https://github.com/firefeed-net/firefeed-telegram-bot).

## 🎯 Purpose

RSS Parser is an independent microservice responsible for:
- **RSS/Atom feed parsing** from various sources
- **Media content extraction** (images, videos, audio)
- **Duplicate detection** to prevent republication
- **Integration with FireFeed API** for storing processed news

## 🏗️ Architecture

### Microservice Components

```
firefeed-rss-parser/
├── services/                    # Business logic
│   ├── rss_manager.py          # Main processing manager
│   ├── rss_fetcher.py          # RSS feed fetcher
│   ├── rss_parser.py           # RSS/Atom parser
│   ├── rss_storage.py          # Storage (via API)
│   ├── media_extractor.py      # Media extraction
│   └── duplicate_detector.py   # Duplicate detector
├── models/                     # Data models
│   ├── __init__.py
│   ├── rss_feed.py            # RSS feed model
│   ├── rss_item.py            # RSS item model
│   └── media_content.py       # Media content model
├── config/                     # Configuration
│   ├── __init__.py
│   └── firefeed_rss_parser_config.py
├── docs/                       # Documentation
├── main.py                     # Entry point
├── config.py                   # Configuration
├── health_check.py             # Health check
├── docker-compose.yml          # Docker environment
└── tests/                      # Tests
```

### Architectural Principles

- **Microservices Architecture** - Fully independent service
- **API-First Approach** - All interactions via HTTP API
- **Dependency Injection** - Dependency injection for testability
- **Asynchronous Processing** - High performance and scalability
- **Service-to-Service Auth** - Secure authentication between services

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Docker & Docker Compose
- Access to FireFeed API

### Installation

```bash
# Clone the repository
git clone https://github.com/firefeed-net/firefeed-rss-parser.git
cd firefeed-rss-parser

# Install dependencies
pip install -e .

# Run in Docker
docker-compose up -d
```

### Configuration

Create a `.env` file based on `.env.example`:

```bash
# FireFeed API Configuration
FIREFEED_API_BASE_URL=http://host.docker.internal:8001
FIREFEED_API_SERVICE_TOKEN=your-api-key-here
FIREFEED_TIMEOUT=30

# Service Configuration
SERVICE_NAME=rss-parser
LOG_LEVEL=INFO

# Processing Configuration
MAX_CONCURRENT_FEEDS=10
FETCH_TIMEOUT=30
PARSER_TIMEOUT=10
```

### Running

```bash
# Local run
python -m firefeed_rss_parser

# Docker run
docker-compose up -d

# Kubernetes deploy
kubectl apply -f k8s/
```

## 📖 Usage

### Core Features

#### 1. RSS Feed Parsing
```python
from firefeed_rss_parser.services.rss_manager import RSSManager

# Create manager
manager = RSSManager(
    fetcher=RSSFetcher(),
    parser=RSSParser(),
    storage=RSSStorage(),
    media_extractor=MediaExtractor(),
    duplicate_detector=DuplicateDetector()
)

# Process feed
feed = RSSFeed(id=1, url="https://example.com/rss", ...)
result = await manager.process_feed(feed)
```

#### 2. Media Extraction
```python
from firefeed_rss_parser.services.media_extractor import MediaExtractor

extractor = MediaExtractor()
media = await extractor.extract_media("https://example.com/article")
# Returns: {"url": "...", "type": "image", "title": "...", ...}
```

#### 3. Duplicate Detection
```python
from firefeed_rss_parser.services.duplicate_detector import DuplicateDetector

detector = DuplicateDetector()
is_duplicate = await detector.is_duplicate(rss_item)
# Checks by GUID, link, and title
```

### API Interfaces

#### FireFeed API Integration
- **GET /api/v1/rss/feeds** - Get list of feeds
- **POST /api/v1/rss/items** - Save RSS item
- **GET /api/v1/categories** - Get categories

#### Service-to-Service Auth
- **API Key Authentication** - For inter-service communication
- **JWT Tokens** - For request authentication
- **Rate Limiting** - Overload protection

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
FIREFEED_API_BASE_URL=http://host.docker.internal:8001
FIREFEED_API_SERVICE_TOKEN=your-api-key
FIREFEED_TIMEOUT=30

# Service Configuration
SERVICE_NAME=rss-parser
LOG_LEVEL=INFO
MAX_WORKERS=10

# Processing Configuration
MAX_CONCURRENT_FEEDS=10
FETCH_TIMEOUT=30
PARSER_TIMEOUT=10
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8080
HEALTH_CHECK_PORT=8081
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  rss-parser:
    build: .
    environment:
      - FIREFEED_API_BASE_URL=http://host.docker.internal:8001
      - FIREFEED_API_SERVICE_TOKEN=${FIREFEED_API_SERVICE_TOKEN}
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"  # Metrics
      - "8081:8081"  # Health checks
    depends_on:
      - firefeed-api
      - postgres
      - redis
```

## 🧪 Testing

### Running Tests

```bash
# All tests
python -m pytest tests/

# Unit tests
python -m pytest tests/ -m unit

# Integration tests
python -m pytest tests/ -m integration

# With coverage
python -m pytest tests/ --cov=firefeed_rss_parser --cov-report=html
```

### Test Types

- **Unit Tests** - Testing individual components
- **Integration Tests** - Testing service interactions
- **Performance Tests** - Performance testing
- **Error Handling Tests** - Error handling testing

## 📊 Monitoring

### Health Checks

The service provides health check endpoints:

```bash
# Health check endpoint
http://localhost:8081/health

# Readiness probe
http://localhost:8081/ready

# Liveness probe
http://localhost:8081/live
```

### Metrics

Metrics are available for Prometheus:

```bash
# Metrics endpoint
http://localhost:8080/metrics
```

### Logging

```python
import logging
from firefeed_rss_parser.config.logging_config import setup_logging

# Setup logging
setup_logging()

# Use logging
logger = logging.getLogger(__name__)
logger.info("Feed processing started")
logger.error("Feed processing failed", exc_info=True)
```

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t firefeed/rss-parser:latest .

# Run container
docker run -d \
  --name rss-parser \
  -p 8080:8080 \
  -p 8081:8081 \
  -e FIREFEED_API_BASE_URL=http://host.docker.internal:8001 \
  -e FIREFEED_API_SERVICE_TOKEN=your-key \
  firefeed/rss-parser:latest
```

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rss-parser
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rss-parser
  template:
    metadata:
      labels:
        app: rss-parser
    spec:
      containers:
      - name: rss-parser
        image: firefeed/rss-parser:latest
        ports:
        - containerPort: 8080  # metrics
        - containerPort: 8081  # health
        env:
        - name: FIREFEED_API_BASE_URL
          value: "http://firefeed-api:8000"
        - name: FIREFEED_API_SERVICE_TOKEN
          valueFrom:
            secretKeyRef:
              name: firefeed-secrets
              key: api-key
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

## 🔒 Security

### Service-to-Service Authentication
- **API Keys** - For authentication between services
- **JWT Tokens** - For protecting API endpoints
- **Rate Limiting** - DDoS protection
- **Input Validation** - XSS/SQL injection protection

### Security Headers
```python
# Automatically added headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
}
```

## 📈 Performance

### Optimizations
- **Concurrent Processing** - Parallel processing of multiple feeds
- **Connection Pooling** - Efficient HTTP connection usage
- **Caching** - Caching parsing results
- **Rate Limiting** - Load control on sources

### Performance Settings
```bash
# Performance configuration
MAX_CONCURRENT_FEEDS=20          # Maximum simultaneous feeds
FETCH_TIMEOUT=30                 # Feed fetch timeout
PARSER_TIMEOUT=10                # Parsing timeout
CONNECTION_POOL_SIZE=100         # Connection pool size
```

## 🔄 Integration

### With FireFeed API
RSS Parser integrates with FireFeed API for:
- **Getting list of feeds** for processing
- **Saving processed news**
- **Getting categories and metadata**
- **Authentication and authorization**

### With Other Services
- **[FireFeed API](https://github.com/firefeed-net/firefeed-api)** - Main API service
- **[FireFeed Telegram Bot](https://github.com/firefeed-net/firefeed-telegram-bot)** - For Telegram notifications
- **Translation Service** - For content translation
- **User Service** - For subscription management

## 🐛 Debugging

### Logging
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG

# View logs
docker logs rss-parser
kubectl logs deployment/rss-parser
```

### Monitoring
```bash
# Check status
curl http://localhost:8081/health

# View metrics
curl http://localhost:8080/metrics

# Check configuration
curl http://localhost:8081/config
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Monitoring](docs/monitoring.md)
- [Testing](docs/testing.md)
- [FireFeed Platform Documentation](https://github.com/firefeed-net/firefeed)

## 🤝 Contributing

### Development
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linter
ruff check firefeed_rss_parser/

# Run formatting
ruff format firefeed_rss_parser/

# Run type checking
mypy firefeed_rss_parser/
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=firefeed_rss_parser

# Run integration tests
python -m pytest tests/ -m integration
```

## 📄 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

Created for the **FireFeed** project - a modern news aggregation system.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/firefeed-net/firefeed-rss-parser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/firefeed-net/firefeed-rss-parser/discussions)
- **Documentation**: [docs.firefeed.net](https://docs.firefeed.net)
- **Email**: mail@firefeed.net

---

**FireFeed RSS Parser** - Production-ready solution for RSS feed parsing in microservices architecture! 🚀
