"""Models package for FireFeed RSS Parser."""

from firefeed_core.models.rss_models import RSSFeed

class DummyRSSItem(dict):
    """Dummy RSSItem - dict subclass for API compatibility."""
    pass

RSSItem = DummyRSSItem

__all__ = [
    "RSSFeed",
    "RSSItem"
]

