"""Models package for FireFeed RSS Parser.

Use models from firefeed_core.models for consistency and DRY principle.
"""

# Import models from firefeed_core
from firefeed_core.models.rss_models import RSSFeed as CoreRSSFeed, RSSItem as CoreRSSItem

# Aliases for backward compatibility
RSSFeed = CoreRSSFeed
RSSItem = CoreRSSItem

__all__ = [
    "RSSFeed",
    "RSSItem"
]

