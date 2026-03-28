"""Logging configuration for FireFeed RSS Parser."""

import logging
from firefeed_core.config.logging_config import setup_logging as core_setup_logging


def setup_logging():
    """Setup structured logging configuration using firefeed_core."""
    core_setup_logging()


def get_logger(name: str):
    """Get a configured logger instance."""
    return logging.getLogger(name)


# Initialize logging
setup_logging()