# Multi-stage Dockerfile for FireFeed RSS Parser

# Build stage
FROM python:3.13-slim AS builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels for metadata
LABEL maintainer="mail@firefeed.net"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="firefeed-rss-parser"
LABEL org.label-schema.description="Production-ready RSS parsing microservice for FireFeed"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.schema-version="1.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY firefeed-rss-parser/requirements.txt ./firefeed-rss-parser/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r firefeed-rss-parser/requirements.txt

# Copy application code
COPY firefeed-rss-parser/ ./firefeed-rss-parser/

# Production stage
FROM python:3.13-slim AS production

# Set production environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
# (includes firefeed-core and all other deps)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy application code
COPY --chown=appuser:appuser firefeed-rss-parser/ .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose ports
EXPOSE 8080 8081

# Default command
CMD ["python", "main.py"]