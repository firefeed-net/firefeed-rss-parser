"""Test configuration for firefeed-rss-parser."""

import sys
from pathlib import Path
import pytest

# Add /app to the path so tests can import modules correctly
app_path = Path("/app")
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))