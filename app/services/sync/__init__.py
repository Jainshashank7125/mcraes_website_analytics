"""
Background sync package — one module per service.

Backward-compatible: callers importing from app.services.background_sync
still work via the shim at that path.
"""
from .scrunch import sync_all_background
from .ga4 import sync_ga4_background
from .agency_analytics import sync_agency_analytics_background

__all__ = [
    "sync_all_background",
    "sync_ga4_background",
    "sync_agency_analytics_background",
]
