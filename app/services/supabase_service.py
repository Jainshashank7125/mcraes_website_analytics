"""
SupabaseService — backward-compat composition.
All methods now live in app/services/db/ (one mixin per service).
All existing callers remain unchanged.
"""
from app.services.db.ga4 import GA4DBMixin
from app.services.db.agency_analytics import AgencyAnalyticsDBMixin
from app.services.db.scrunch import ScrunchDBMixin
from app.services.db.clients import ClientDBMixin


class SupabaseService(GA4DBMixin, ScrunchDBMixin, AgencyAnalyticsDBMixin, ClientDBMixin):
    """Composed from per-integration mixins. All existing callers unchanged."""
    pass
