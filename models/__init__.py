"""Models package for FireFeed RSS Parser."""

# Import models from firefeed_core to avoid duplication
from firefeed_core.models.rss_models import RSSFeed, RSSItem

__all__ = [
    "RSSFeed",
    "RSSItem"
]