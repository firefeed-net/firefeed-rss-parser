# FireFeed RSS Parser - Deployment Guide

This document provides comprehensive deployment instructions for the FireFeed RSS Parser microservice.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

- **Operating System:** Linux, macOS, or Windows
- **Python:** 3.10 or higher
- **Docker:** 20.10 or higher
- **Docker Compose:** 2.0 or higher
- **Kubernetes:** 1.20 or higher (for K8s deployment)

### External Dependencies

- **FireFeed API** - Must be accessible and configured
- **Database** - PostgreSQL or compatible (managed by FireFeed API)
- **Network Access** - Outbound internet access for RSS feeds

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd firefeed-rss-parser
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```bash
# FireFeed API Configuration
FIREFEED_API_BASE_URL=http://your-firefeed-api:8000
FIREFEED_API_SERVICE_TOKEN=your-api-key-here

# Service Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_FEEDS=10

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8080
HEALTH_CHECK_PORT=8081
```

### 3. Install Dependencies (Development)

For development environment:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or using poetry
poetry install
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build production image
docker build -t firefeed/rss-parser:latest .

# Build development image
docker build --target development -t firefeed/rss-parser:dev .
```

### 2. Run with Docker Compose

```bash
# Start in development mode
docker-compose up -d rss-parser-dev

# Start in production mode
docker-compose up -d rss-parser

# View logs
docker-compose logs -f rss-parser
```

### 3. Run with Plain Docker

```bash
# Run container
docker run -d \
  --name rss-parser \
  -p 8080:8080 \
  -p 8081:8081 \
  --env-file .env \
  firefeed/rss-parser:latest

# View logs
docker logs -f rss-parser
```

### 4. Docker Image Tags

```bash
# Tag image for registry
docker tag firefeed/rss-parser:latest your-registry/firefeed/rss-parser:v1.0.0

# Push to registry
docker push your-registry/firefeed/rss-parser:v1.0.0
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace firefeed
```

### 2. Create Secrets

```bash
kubectl create secret generic firefeed-secrets \
  --namespace=firefeed \
  --from-literal=api-key="your-api-key-here"
```

### 3. Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Application

```bash
# Apply all manifests
kubectl apply -f k8s/ --namespace=firefeed

# Or apply individually
kubectl apply -f k8s/deployment.yaml --namespace=firefeed
kubectl apply -f k8s/service.yaml --namespace=firefeed
kubectl apply -f k8s/ingress.yaml --namespace=firefeed
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n firefeed

# Check services
kubectl get services -n firefeed

# Check events
kubectl get events -n firefeed --sort-by=.metadata.creationTimestamp
```

### 6. Kubernetes Manifests

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rss-parser
  namespace: firefeed
  labels:
    app: rss-parser
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rss-parser
  template:
    metadata:
      labels:
        app: rss-parser
        version: v1.0.0
    spec:
      containers:
      - name: rss-parser
        image: firefeed/rss-parser:latest
        ports:
        - containerPort: 8080  # metrics
          name: metrics
        - containerPort: 8081  # health
          name: health
        env:
        - name: FIREFEED_API_BASE_URL
          value: "http://firefeed-api:8000"
        - name: FIREFEED_API_SERVICE_TOKEN
          valueFrom:
            secretKeyRef:
              name: firefeed-secrets
              key: api-key
        - name: LOG_LEVEL
          value: "INFO"
        - name: MAX_CONCURRENT_FEEDS
          value: "10"
        livenessProbe:
          httpGet:
            path: /live
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: rss-parser-config
      restartPolicy: Always
```

#### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rss-parser-service
  namespace: firefeed
  labels:
    app: rss-parser
spec:
  selector:
    app: rss-parser
  ports:
  - name: metrics
    port: 8080
    targetPort: 8080
    protocol: TCP
  - name: health
    port: 8081
    targetPort: 8081
    protocol: TCP
  type: ClusterIP
```

#### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rss-parser-ingress
  namespace: firefeed
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - rss-parser.your-domain.com
    secretName: rss-parser-tls
  rules:
  - host: rss-parser.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rss-parser-service
            port:
              number: 8081
```

## Configuration

### Environment Variables

#### FireFeed API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FIREFEED_API_BASE_URL` | FireFeed API base URL | `http://localhost:8000` | No |
| `FIREFEED_API_SERVICE_TOKEN` | API authentication key | - | Yes |
| `FIREFEED_TIMEOUT` | API request timeout (seconds) | `30` | No |
| `FIREFEED_MAX_RETRIES` | Max API retry attempts | `3` | No |
| `FIREFEED_RETRY_DELAY` | Retry delay (seconds) | `1.0` | No |

#### Service Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_NAME` | Service name | `rss-parser` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `MAX_CONCURRENT_FEEDS` | Max concurrent feed processing | `10` | No |

#### Processing Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FETCH_TIMEOUT` | RSS fetch timeout (seconds) | `30` | No |
| `PARSER_TIMEOUT` | RSS parse timeout (seconds) | `10` | No |
| `STORAGE_TIMEOUT` | Storage operation timeout (seconds) | `30` | No |
| `MEDIA_TIMEOUT` | Media extraction timeout (seconds) | `15` | No |
| `DUPLICATE_CHECK_TIMEOUT` | Duplicate check timeout (seconds) | `5` | No |

#### Monitoring Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | No |
| `METRICS_PORT` | Metrics endpoint port | `8080` | No |
| `HEALTH_CHECK_PORT` | Health check endpoint port | `8081` | No |
| `METRICS_PATH` | Metrics endpoint path | `/metrics` | No |
| `HEALTH_PATH` | Health check path | `/health` | No |
| `READINESS_PATH` | Readiness probe path | `/ready` | No |
| `LIVENESS_PATH` | Liveness probe path | `/live` | No |

#### Security Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_KEY_REQUIRED` | Require API key | `true` | No |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` | No |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` | No |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | `60` | No |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | - | No |

### Configuration Examples

#### Development Environment

```bash
# .env.development
FIREFEED_API_BASE_URL=http://localhost:8000
FIREFEED_API_SERVICE_TOKEN=dev-key-123
LOG_LEVEL=DEBUG
MAX_CONCURRENT_FEEDS=5
ENABLE_METRICS=true
```

#### Production Environment

```bash
# .env.production
FIREFEED_API_BASE_URL=http://host.docker.internal:8001
FIREFEED_API_SERVICE_TOKEN=prod-key-456
LOG_LEVEL=INFO
MAX_CONCURRENT_FEEDS=20
ENABLE_METRICS=true
API_KEY_REQUIRED=true
RATE_LIMIT_ENABLED=true
```

## Monitoring and Logging

### Prometheus Metrics

Access metrics endpoint:

```bash
curl http://localhost:8080/metrics
```

Key metrics to monitor:

- `rss_parser_feeds_processed_total` - Total feeds processed
- `rss_parser_items_saved_total` - Total items saved
- `rss_parser_fetch_duration_seconds` - Fetch duration
- `rss_parser_parse_duration_seconds` - Parse duration
- `rss_parser_errors_total` - Total errors

### Grafana Dashboard

Import dashboard with metrics:

```json
{
  "dashboard": {
    "title": "RSS Parser Dashboard",
    "panels": [
      {
        "title": "Feeds Processed",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rss_parser_feeds_processed_total[5m])",
            "legendFormat": "Feeds/min"
          }
        ]
      }
    ]
  }
}
```

### Health Checks

Check service health:

```bash
# Liveness check
curl http://localhost:8081/live

# Readiness check
curl http://localhost:8081/ready

# Full health check
curl http://localhost:8081/health
```

### Logging

View logs:

```bash
# Docker
docker logs rss-parser

# Kubernetes
kubectl logs -f deployment/rss-parser -n firefeed

# Docker Compose
docker-compose logs -f rss-parser
```

Log levels:

- `DEBUG` - Detailed debugging information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical error messages

## Scaling

### Horizontal Scaling

#### Docker Compose

```bash
# Scale to 3 instances
docker-compose up -d --scale rss-parser=3
```

#### Kubernetes

```bash
# Scale deployment
kubectl scale deployment rss-parser --replicas=5 -n firefeed

# Or update deployment manifest
kubectl patch deployment rss-parser -p '{"spec":{"replicas":5}}' -n firefeed
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rss-parser-hpa
  namespace: firefeed
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rss-parser
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

Update resource limits:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Backup and Recovery

### Configuration Backup

Backup configuration files:

```bash
# Backup environment files
cp .env .env.backup

# Backup Docker Compose files
cp docker-compose.yml docker-compose.yml.backup

# Backup Kubernetes manifests
tar -czf k8s-backup.tar.gz k8s/
```

### Data Backup

Since RSS Parser doesn't store data locally, backup FireFeed API data:

```bash
# Backup database (example for PostgreSQL)
pg_dump -h db-host -U firefeed -d firefeed > firefeed-backup.sql

# Backup to cloud storage
aws s3 cp firefeed-backup.sql s3://your-backup-bucket/
```

### Recovery Procedures

#### Service Recovery

```bash
# Restart service
docker-compose restart rss-parser

# Or in Kubernetes
kubectl rollout restart deployment/rss-parser -n firefeed
```

#### Configuration Recovery

```bash
# Restore environment
cp .env.backup .env

# Restore manifests
tar -xzf k8s-backup.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptoms:**
- Container exits immediately
- Kubernetes pod in CrashLoopBackOff

**Diagnosis:**
```bash
# Check logs
docker logs rss-parser
kubectl logs -f deployment/rss-parser -n firefeed
```

**Solutions:**
- Check environment variables
- Verify API connectivity
- Check resource limits

#### 2. High Error Rate

**Symptoms:**
- Many failed requests
- High error metrics

**Diagnosis:**
```bash
# Check error metrics
curl http://localhost:8080/metrics | grep error

# Check logs for errors
docker logs rss-parser | grep ERROR
```

**Solutions:**
- Check API key validity
- Verify network connectivity
- Increase timeout values
- Check rate limiting

#### 3. Slow Performance

**Symptoms:**
- High response times
- Slow feed processing

**Diagnosis:**
```bash
# Check performance metrics
curl http://localhost:8080/metrics | grep duration

# Check resource usage
docker stats
kubectl top pods -n firefeed
```

**Solutions:**
- Increase concurrent feeds
- Optimize network
- Scale horizontally
- Check database performance

#### 4. Health Check Failures

**Symptoms:**
- Health endpoints return 503
- Kubernetes restarts pods

**Diagnosis:**
```bash
# Check health endpoint
curl -v http://localhost:8081/health

# Check API connectivity
curl -v http://localhost:8080/metrics
```

**Solutions:**
- Check API connectivity
- Verify configuration
- Check resource availability
- Review error logs

### Debug Mode

Enable debug logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Restart service
docker-compose restart rss-parser
```

### Performance Profiling

Profile service performance:

```bash
# Enable profiling
export PROFILING_ENABLED=true

# Run with profiler
python -m cProfile -o profile.stats -m firefeed_rss_parser

# Analyze results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

## Security Considerations

### 1. Network Security

- **Firewall Rules:** Restrict access to necessary ports only
- **VPN:** Use VPN for management access
- **TLS:** Enable TLS for all communications
- **Network Policies:** Use Kubernetes network policies

### 2. Authentication and Authorization

- **API Keys:** Use strong, unique API keys
- **Rotation:** Regularly rotate API keys
- **Least Privilege:** Grant minimal required permissions
- **Audit Logs:** Monitor authentication events

### 3. Data Protection

- **Encryption:** Encrypt sensitive data at rest
- **Backups:** Regular encrypted backups
- **Access Control:** Restrict data access
- **Data Retention:** Implement data retention policies

### 4. Container Security

- **Image Scanning:** Scan images for vulnerabilities
- **Non-root User:** Run containers as non-root
- **Read-only Root:** Use read-only root filesystem
- **Security Context:** Configure security contexts

### 5. Monitoring and Alerting

- **Security Metrics:** Monitor security-related metrics
- **Alerting:** Set up security alerts
- **Incident Response:** Have incident response plan
- **Regular Audits:** Conduct security audits

### Security Checklist

- [ ] API keys are stored securely
- [ ] Network access is restricted
- [ ] TLS is enabled for all communications
- [ ] Containers run as non-root user
- [ ] Regular security scans are performed
- [ ] Monitoring and alerting are configured
- [ ] Backup and recovery procedures are tested
- [ ] Security documentation is up to date

## Conclusion

This deployment guide covers the essential aspects of deploying the FireFeed RSS Parser microservice. Always follow security best practices and monitor your deployment for optimal performance and security.