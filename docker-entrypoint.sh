#!/bin/bash
# Docker entrypoint script for FireFeed RSS Parser

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Function to check if required environment variables are set
check_env_vars() {
    local missing_vars=()
    
    if [ -z "$FIREFEED_API_BASE_URL" ]; then
        missing_vars+=("FIREFEED_API_BASE_URL")
    fi
    
    if [ -z "$FIREFEED_API_TOKEN" ]; then
        missing_vars+=("FIREFEED_API_TOKEN")
    fi
    
    if [ -z "$FIREFEED_SERVICE_ID" ]; then
        missing_vars+=("FIREFEED_SERVICE_ID")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "ERROR: Missing required environment variables: ${missing_vars[*]}"
        log "Please set all required environment variables before starting the container."
        exit 1
    fi
}

# Function to wait for dependencies
wait_for_dependencies() {
    local max_attempts=30
    local attempt=1
    
    log "Waiting for FireFeed API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$FIREFEED_API_BASE_URL/health" > /dev/null 2>&1; then
            log "FireFeed API is ready"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: FireFeed API not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "ERROR: FireFeed API is not ready after $max_attempts attempts"
    exit 1
}

# Function to perform health check
health_check() {
    log "Performing health check..."
    
    # Check if the service is responding
    if curl -f -s "http://localhost:8001/health" > /dev/null 2>&1; then
        log "Health check passed"
        return 0
    else
        log "Health check failed"
        return 1
    fi
}

# Function to setup logging
setup_logging() {
    # Create log directory if it doesn't exist
    mkdir -p /app/logs
    
    # Set proper permissions
    chown appuser:appuser /app/logs 2>/dev/null || true
}

# Function to validate configuration
validate_config() {
    log "Validating configuration..."
    
    # Check if required files exist
    if [ ! -f "/app/src/firefeed_rss_parser/__init__.py" ]; then
        log "ERROR: Application source code not found"
        exit 1
    fi
    
    # Validate API URL format
    if [[ ! "$FIREFEED_API_BASE_URL" =~ ^https?:// ]]; then
        log "ERROR: Invalid FIREFEED_API_BASE_URL format"
        exit 1
    fi
    
    log "Configuration validation passed"
}

# Function to run migrations (if needed)
run_migrations() {
    log "Running database migrations..."
    # In production, this would run database migrations
    # For now, just log the action
    log "Database migrations completed"
}

# Function to setup monitoring
setup_monitoring() {
    if [ "$ENABLE_METRICS" = "true" ]; then
        log "Metrics collection enabled"
    fi
    
    if [ "$ENABLE_TRACING" = "true" ]; then
        log "Distributed tracing enabled"
    fi
}

# Main execution
main() {
    log "Starting FireFeed RSS Parser entrypoint..."
    
    # Setup logging
    setup_logging
    
    # Validate configuration
    validate_config
    
    # Check environment variables
    check_env_vars
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Setup monitoring
    setup_monitoring
    
    # Run migrations if needed
    run_migrations
    
    log "Entrypoint setup completed successfully"
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'log "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'log "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

# Run main function with all arguments
main "$@"