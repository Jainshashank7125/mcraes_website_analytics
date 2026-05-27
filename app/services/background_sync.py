"""
Background sync — backward-compat shim.
All functions now live in app/services/sync/ (one file per service).
"""
from app.services.sync import (  # noqa: F401
    sync_all_background,
    sync_ga4_background,
    sync_agency_analytics_background,
)
