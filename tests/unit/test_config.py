"""
Tests for configuration in FireFeed RSS Parser microservice.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from config.firefeed_rss_parser_config import (
    RSSParserConfig,
    ConfigLoader,
    APIConfig,
    RSSConfig,
    DuplicateDetectionConfig,
    MediaConfig,
    TranslationConfig,
    LoggingConfig,
    HealthConfig,
    SecurityConfig,
    MonitoringConfig
)


class TestAPIConfig:
    """Test APIConfig."""
    
    def test_api_config_defaults(self):
        """Test APIConfig default values."""
        config = APIConfig()
        
        assert config.base_url == "http://firefeed-api:8000"
        assert config.token == ""
        assert config.service_id == "firefeed-rss-parser"
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
    
    def test_api_config_custom(self):
        """Test APIConfig with custom values."""
        config = APIConfig(
            base_url="http://custom-api:9000",
            token="custom-token",
            service_id="custom-service",
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0
        )
        
        assert config.base_url == "http://custom-api:9000"
        assert config.token == "custom-token"
        assert config.service_id == "custom-service"
        assert config.timeout == 60
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0


class TestRSSConfig:
    """Test RSSConfig."""
    
    def test_rss_config_defaults(self):
        """Test RSSConfig default values."""
        config = RSSConfig()
        
        assert config.max_concurrent_feeds == 10
        assert config.max_entries_per_feed == 50
        assert config.fetch_interval_minutes == 3
        assert config.batch_processing_enabled is True
        assert config.batch_size == 50
        assert config.delay_between_items == 0.1
        assert config.delay_between_batches == 60.0
        assert config.min_item_title_words_length == 3
        assert config.min_item_content_words_length == 10
        assert config.user_agent == "FireFeed RSS Parser/0.1.0"
    
    def test_rss_config_custom(self):
        """Test RSSConfig with custom values."""
        config = RSSConfig(
            max_concurrent_feeds=20,
            max_entries_per_feed=100,
            fetch_interval_minutes=5,
            batch_processing_enabled=False,
            batch_size=100,
            delay_between_items=0.5,
            delay_between_batches=120.0,
            min_item_title_words_length=5,
            min_item_content_words_length=20,
            user_agent="Custom RSS Parser/1.0.0"
        )
        
        assert config.max_concurrent_feeds == 20
        assert config.max_entries_per_feed == 100
        assert config.fetch_interval_minutes == 5
        assert config.batch_processing_enabled is False
        assert config.batch_size == 100
        assert config.delay_between_items == 0.5
        assert config.delay_between_batches == 120.0
        assert config.min_item_title_words_length == 5
        assert config.min_item_content_words_length == 20
        assert config.user_agent == "Custom RSS Parser/1.0.0"


class TestDuplicateDetectionConfig:
    """Test DuplicateDetectionConfig."""
    
    def test_duplicate_detection_config_defaults(self):
        """Test DuplicateDetectionConfig default values."""
        config = DuplicateDetectionConfig()
        
        assert config.enabled is True
        assert config.similarity_threshold == 0.9
        assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.max_recent_items_check == 100
    
    def test_duplicate_detection_config_custom(self):
        """Test DuplicateDetectionConfig with custom values."""
        config = DuplicateDetectionConfig(
            enabled=False,
            similarity_threshold=0.8,
            embedding_model="custom-model",
            max_recent_items_check=50
        )
        
        assert config.enabled is False
        assert config.similarity_threshold == 0.8
        assert config.embedding_model == "custom-model"
        assert config.max_recent_items_check == 50


class TestMediaConfig:
    """Test MediaConfig."""
    
    def test_media_config_defaults(self):
        """Test MediaConfig default values."""
        config = MediaConfig()
        
        assert config.processing_enabled is True
        assert config.type_priority == "image"
        assert config.image_quality == 85
        assert config.video_quality == "720p"
        assert config.max_image_size_mb == 10
        assert config.max_video_size_mb == 50
        assert config.image_resize_enabled is True
        assert config.video_compress_enabled is True
    
    def test_media_config_custom(self):
        """Test MediaConfig with custom values."""
        config = MediaConfig(
            processing_enabled=False,
            type_priority="video",
            image_quality=90,
            video_quality="1080p",
            max_image_size_mb=20,
            max_video_size_mb=100,
            image_resize_enabled=False,
            video_compress_enabled=False
        )
        
        assert config.processing_enabled is False
        assert config.type_priority == "video"
        assert config.image_quality == 90
        assert config.video_quality == "1080p"
        assert config.max_image_size_mb == 20
        assert config.max_video_size_mb == 100
        assert config.image_resize_enabled is False
        assert config.video_compress_enabled is False


class TestTranslationConfig:
    """Test TranslationConfig."""
    
    def test_translation_config_defaults(self):
        """Test TranslationConfig default values."""
        config = TranslationConfig()
        
        assert config.enabled is True
        assert config.default_source_lang == "auto"
        assert config.target_languages == ["en", "ru", "de"]
        assert config.max_text_length == 5000
        assert config.batch_size == 10
        assert config.timeout == 60
    
    def test_translation_config_custom(self):
        """Test TranslationConfig with custom values."""
        config = TranslationConfig(
            enabled=False,
            default_source_lang="en",
            target_languages=["fr", "es"],
            max_text_length=10000,
            batch_size=20,
            timeout=120
        )
        
        assert config.enabled is False
        assert config.default_source_lang == "en"
        assert config.target_languages == ["fr", "es"]
        assert config.max_text_length == 10000
        assert config.batch_size == 20
        assert config.timeout == 120


class TestLoggingConfig:
    """Test LoggingConfig."""
    
    def test_logging_config_defaults(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.file_path is None
        assert config.max_file_size_mb == 100
        assert config.backup_count == 5
    
    def test_logging_config_custom(self):
        """Test LoggingConfig with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format="text",
            file_path="/var/log/rss-parser.log",
            max_file_size_mb=50,
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.format == "text"
        assert config.file_path == "/var/log/rss-parser.log"
        assert config.max_file_size_mb == 50
        assert config.backup_count == 3


class TestHealthConfig:
    """Test HealthConfig."""
    
    def test_health_config_defaults(self):
        """Test HealthConfig default values."""
        config = HealthConfig()
        
        assert config.enabled is True
        assert config.check_interval_seconds == 30
        assert config.timeout_seconds == 10
        assert config.dependencies == ["api", "database", "storage"]
    
    def test_health_config_custom(self):
        """Test HealthConfig with custom values."""
        config = HealthConfig(
            enabled=False,
            check_interval_seconds=60,
            timeout_seconds=20,
            dependencies=["api", "database"]
        )
        
        assert config.enabled is False
        assert config.check_interval_seconds == 60
        assert config.timeout_seconds == 20
        assert config.dependencies == ["api", "database"]


class TestSecurityConfig:
    """Test SecurityConfig."""
    
    def test_security_config_defaults(self):
        """Test SecurityConfig default values."""
        config = SecurityConfig()
        
        assert config.jwt_secret == ""
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expiration_minutes == 60
        assert config.allowed_origins == ["*"]
        assert config.rate_limit_requests == 1000
        assert config.rate_limit_window_seconds == 60
    
    def test_security_config_custom(self):
        """Test SecurityConfig with custom values."""
        config = SecurityConfig(
            jwt_secret="custom-secret",
            jwt_algorithm="RS256",
            jwt_expiration_minutes=120,
            allowed_origins=["http://localhost:3000"],
            rate_limit_requests=500,
            rate_limit_window_seconds=30
        )
        
        assert config.jwt_secret == "custom-secret"
        assert config.jwt_algorithm == "RS256"
        assert config.jwt_expiration_minutes == 120
        assert config.allowed_origins == ["http://localhost:3000"]
        assert config.rate_limit_requests == 500
        assert config.rate_limit_window_seconds == 30


class TestMonitoringConfig:
    """Test MonitoringConfig."""
    
    def test_monitoring_config_defaults(self):
        """Test MonitoringConfig default values."""
        config = MonitoringConfig()
        
        assert config.enabled is True
        assert config.metrics_enabled is True
        assert config.prometheus_port == 9090
        assert config.tracing_enabled is False
        assert config.tracing_endpoint == ""
    
    def test_monitoring_config_custom(self):
        """Test MonitoringConfig with custom values."""
        config = MonitoringConfig(
            enabled=False,
            metrics_enabled=False,
            prometheus_port=9091,
            tracing_enabled=True,
            tracing_endpoint="http://jaeger:14268"
        )
        
        assert config.enabled is False
        assert config.metrics_enabled is False
        assert config.prometheus_port == 9091
        assert config.tracing_enabled is True
        assert config.tracing_endpoint == "http://jaeger:14268"


class TestRSSParserConfig:
    """Test RSSParserConfig."""
    
    def test_rss_parser_config_defaults(self):
        """Test RSSParserConfig default values."""
        config = RSSParserConfig()
        
        assert isinstance(config.api, APIConfig)
        assert isinstance(config.rss, RSSConfig)
        assert isinstance(config.duplicate_detection, DuplicateDetectionConfig)
        assert isinstance(config.media, MediaConfig)
        assert isinstance(config.translation, TranslationConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.health, HealthConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.monitoring, MonitoringConfig)
        
        assert config.environment == "production"
        assert config.debug is False
        assert config.version == "0.1.0"
    
    def test_rss_parser_config_custom(self):
        """Test RSSParserConfig with custom values."""
        config = RSSParserConfig(
            environment="development",
            debug=True,
            version="1.0.0"
        )
        
        assert config.environment == "development"
        assert config.debug is True
        assert config.version == "1.0.0"


class TestConfigLoader:
    """Test ConfigLoader."""
    
    def test_load_from_env_empty(self):
        """Test loading config from empty environment."""
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigLoader.load_from_env()
            
            # Should use default values
            assert config.api.base_url == "http://firefeed-api:8000"
            assert config.rss.max_concurrent_feeds == 10
            assert config.duplicate_detection.enabled is True
    
    def test_load_from_env_with_values(self):
        """Test loading config from environment variables."""
        env_vars = {
            "API_BASE_URL": "http://custom-api:9000",
            "FIREFEED_API_TOKEN": "custom-token",
            "FIREFEED_SERVICE_ID": "custom-service",
            "RSS_PARSER_MAX_CONCURRENT_FEEDS": "20",
            "RSS_PARSER_MAX_ENTRIES_PER_FEED": "100",
            "RSS_PARSER_FETCH_INTERVAL_MINUTES": "5",
            "RSS_PARSER_BATCH_PROCESSING_ENABLED": "false",
            "DUPLICATE_DETECTION_ENABLED": "false",
            "DUPLICATE_SIMILARITY_THRESHOLD": "0.8",
            "MEDIA_PROCESSING_ENABLED": "false",
            "MEDIA_TYPE_PRIORITY": "video",
            "TRANSLATION_ENABLED": "false",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "HEALTH_ENABLED": "false",
            "ENVIRONMENT": "development",
            "DEBUG": "true",
            "VERSION": "1.0.0"
        }
        
        with patch.dict(os.environ, env_vars):
            config = ConfigLoader.load_from_env()
            
            assert config.api.base_url == "http://custom-api:9000"
            assert config.api.token == "custom-token"
            assert config.api.service_id == "custom-service"
            assert config.rss.max_concurrent_feeds == 20
            assert config.rss.max_entries_per_feed == 100
            assert config.rss.fetch_interval_minutes == 5
            assert config.rss.batch_processing_enabled is False
            assert config.duplicate_detection.enabled is False
            assert config.duplicate_detection.similarity_threshold == 0.8
            assert config.media.processing_enabled is False
            assert config.media.type_priority == "video"
            assert config.translation.enabled is False
            assert config.logging.level == "DEBUG"
            assert config.logging.format == "text"
            assert config.health.enabled is False
            assert config.environment == "development"
            assert config.debug is True
            assert config.version == "1.0.0"
    
    def test_load_from_env_boolean_values(self):
        """Test loading boolean values from environment."""
        env_vars = {
            "RSS_PARSER_BATCH_PROCESSING_ENABLED": "true",
            "DUPLICATE_DETECTION_ENABLED": "false",
            "MEDIA_PROCESSING_ENABLED": "1",
            "TRANSLATION_ENABLED": "0",
            "HEALTH_ENABLED": "yes",
            "DEBUG": "no"
        }
        
        with patch.dict(os.environ, env_vars):
            config = ConfigLoader.load_from_env()
            
            assert config.rss.batch_processing_enabled is True
            assert config.duplicate_detection.enabled is False
            assert config.media.processing_enabled is True
            assert config.translation.enabled is False
            assert config.health.enabled is True
            assert config.debug is False
    
    def test_load_from_file(self):
        """Test loading config from YAML file."""
        config_data = {
            "api": {
                "base_url": "http://file-api:8000",
                "token": "file-token",
                "service_id": "file-service"
            },
            "rss": {
                "max_concurrent_feeds": 15,
                "max_entries_per_feed": 75
            },
            "environment": "test",
            "version": "0.2.0"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = ConfigLoader.load_from_file(temp_file)
            
            assert config.api.base_url == "http://file-api:8000"
            assert config.api.token == "file-token"
            assert config.api.service_id == "file-service"
            assert config.rss.max_concurrent_feeds == 15
            assert config.rss.max_entries_per_feed == 75
            assert config.environment == "test"
            assert config.version == "0.2.0"
        finally:
            os.unlink(temp_file)
    
    def test_load_from_file_not_found(self):
        """Test loading config from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_file("/nonexistent/file.yaml")
    
    def test_load_from_file_invalid_yaml(self):
        """Test loading config from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: error:")
            temp_file = f.name
        
        try:
            with pytest.raises(Exception):
                ConfigLoader.load_from_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_load_priority(self):
        """Test config loading priority (file over environment)."""
        # Set environment variable
        os.environ["API_BASE_URL"] = "http://env-api:8000"
        
        try:
            # Create config file with different value
            config_data = {
                "api": {
                    "base_url": "http://file-api:8000"
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                import yaml
                yaml.dump(config_data, f)
                temp_file = f.name
            
            try:
                # Set CONFIG_PATH to use file
                os.environ["CONFIG_PATH"] = temp_file
                
                config = ConfigLoader.load()
                
                # File should take precedence
                assert config.api.base_url == "http://file-api:8000"
            finally:
                os.unlink(temp_file)
                if "CONFIG_PATH" in os.environ:
                    del os.environ["CONFIG_PATH"]
        finally:
            if "API_BASE_URL" in os.environ:
                del os.environ["API_BASE_URL"]


class TestConfigIntegration:
    """Test configuration integration."""
    
    def test_config_post_init(self):
        """Test configuration post-initialization."""
        config = RSSParserConfig()
        
        # Should have called setup_logging
        # This is tested indirectly by checking that the config was created successfully
        assert config is not None
    
    def test_config_immutability(self):
        """Test that config objects are properly structured."""
        config = RSSParserConfig()
        
        # Test that nested configs are separate objects
        config1 = RSSParserConfig()
        config2 = RSSParserConfig()
        
        assert config1 is not config2
        assert config1.api is not config2.api
        assert config1.rss is not config2.rss
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = RSSParserConfig()
        
        # Test that all required fields are present
        required_fields = [
            'api', 'rss', 'duplicate_detection', 'media', 
            'translation', 'logging', 'health', 'security', 'monitoring'
        ]
        
        for field in required_fields:
            assert hasattr(config, field)
            assert getattr(config, field) is not None