"""Test RSS Parser service basic functionality."""

import pytest
from fastapi.testclient import TestClient


def test_module_imports():
    """Verify basic imports work."""
    import main
    assert main is not None


def test_config_imports():
    """Verify config module exists."""
    import config
    import config.firefeed_rss_parser_config
    assert config.firefeed_rss_parser_config is not None


def test_services_imports():
    """Verify services can be imported."""
    import services.rss_parser
    import services.rss_fetcher
    import services.rss_manager
    import services.rss_storage
    import services.duplicate_detector
    import services.media_extractor
    assert services is not None