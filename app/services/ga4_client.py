"""
Google Analytics 4 API Client
Handles all GA4 API interactions for multi-property reporting
"""
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter,
    RunRealtimeReportRequest,
    OrderBy,
)
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import ListPropertiesRequest
from google.auth import default
from google.oauth2 import service_account
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request
import os
from app.core.config import settings
from app.services.ga4_token_service import GA4TokenService

logger = logging.getLogger(__name__)

class AccessTokenCredentials(GoogleCredentials):
    """Custom credentials class that uses a stored access token"""
    
    def __init__(self, token: str):
        self.token = token
        self.expired = False
    
    def refresh(self, request: Request):
        """Access tokens can't be refreshed this way - need to regenerate"""
        self.expired = True
        raise ValueError("Access token expired. Please regenerate using generate_ga4_token.py")

class GA4APIClient:
    """Client for interacting with Google Analytics 4 API"""
    
    def __init__(self):
        self.credentials_path = settings.GA4_CREDENTIALS_PATH
        self.scopes = settings.GA4_SCOPES
        self._data_client = None
        self._admin_client = None
        self._use_token = True  # Prefer stored tokens over service account
    
    def _apply_filters_to_request(self, request_params: Dict, global_filters: Optional[Dict[str, List[str]]], exclude_dimensions: Optional[List[str]] = None) -> Dict:
        """Helper method to apply global filters to a GA4 request
        
        Converts filter dict to GA4 FilterExpression object.
        GA4 API requires FilterExpression objects, not raw dictionaries.
        """
        from app.services.ga4_filter_builder import GA4FilterBuilder
        
        filter_dict = GA4FilterBuilder.build_dimension_filter(global_filters, exclude_dimensions)
        if filter_dict:
            # Convert dict structure to GA4 FilterExpression object
            # GA4 API expects FilterExpression, not raw dict with andGroup
            dimension_filter = self._dict_to_filter_expression(filter_dict)
            if dimension_filter:
                request_params["dimension_filter"] = dimension_filter
        
        return request_params
    
    def _dict_to_filter_expression(self, filter_dict: Dict) -> Optional[FilterExpression]:
        """Convert filter dictionary to GA4 FilterExpression object
        
        GA4 API structure:
        - Single filter: FilterExpression(filter=Filter(...))
        - Multiple filters: FilterExpression(and_group=FilterExpressionList(expressions=[...]))
        """
        if not filter_dict:
            return None
        
        # If it has andGroup, convert to FilterExpression with and_group
        if "andGroup" in filter_dict:
            expressions = []
            for expr in filter_dict["andGroup"].get("expressions", []):
                filter_obj = expr.get("filter", {})
                field_name = filter_obj.get("fieldName")
                in_list_filter = filter_obj.get("inListFilter")
                
                if field_name and in_list_filter:
                    # Create Filter object
                    ga4_filter = Filter(
                        field_name=field_name,
                        in_list_filter=Filter.InListFilter(
                            values=in_list_filter.get("values", [])
                        )
                    )
                    # Wrap in FilterExpression
                    expressions.append(FilterExpression(filter=ga4_filter))
            
            if len(expressions) == 1:
                # Single expression - return directly
                return expressions[0]
            elif len(expressions) > 1:
                # Multiple expressions - use and_group
                return FilterExpression(
                    and_group=FilterExpressionList(expressions=expressions)
                )
        
        return None
    
    def _get_credentials(self):
        """Get Google Analytics credentials - prefer stored tokens"""
        # First, try to use stored access token
        if self._use_token:
            access_token = GA4TokenService.get_access_token()
            if access_token:
                try:
                    credentials = AccessTokenCredentials(token=access_token)
                    logger.debug("Using stored access token for GA4 API")
                    return credentials
                except Exception as e:
                    logger.warning(f"Failed to use stored token: {e}, falling back to service account")
        
        # Fallback to service account credentials
        if self.credentials_path and os.path.exists(self.credentials_path):
            logger.debug("Using service account credentials for GA4 API")
            return service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.scopes
            )
        else:
            # Try to use default credentials (for GCP environments)
            logger.debug("Using default credentials for GA4 API")
            credentials, _ = default(scopes=self.scopes)
            return credentials
    
    def _get_data_client(self):
        """Get or create Analytics Data API client"""
        if self._data_client is None:
            credentials = self._get_credentials()
            self._data_client = BetaAnalyticsDataClient(credentials=credentials)
        return self._data_client
    
    def _get_admin_client(self):
        """Get or create Analytics Admin API client"""
        if self._admin_client is None:
            credentials = self._get_credentials()
            self._admin_client = AnalyticsAdminServiceClient(credentials=credentials)
        return self._admin_client
    
    # 1. Website Traffic Overview API
    async def get_traffic_overview(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        global_filters: Optional[Dict[str, List[str]]] = None
    ) -> Dict:
        """Get high-level visitor metrics with optional global filters.

        Executes exactly 4 GA4 API calls per invocation:
          1. Current-period totals (no dimension)  – users, sessions, newUsers,
             engagedSessions, conversions, totalRevenue
          2. Current-period daily (date dimension)  – full per-day breakdown
             including conversions and totalRevenue for daily storage
          3. Previous-period totals (no dimension)  – same metrics as call 1
          4. Previous-period daily (date dimension)  – sessions, avgDuration,
             engagementRate, bounceRate for weighted-average computation

        Returns the standard totals dict plus all ``prev_*`` keys so callers
        can obtain previous-period values without making a second full call.
        """
        from app.services.ga4_filter_builder import GA4FilterBuilder
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            client = self._get_data_client()

            # ----------------------------------------------------------------
            # Determine previous-period date range (same duration, immediately
            # preceding the current period).
            # ----------------------------------------------------------------
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")
            period_duration = (end_dt - start_dt).days + 1  # inclusive
            prev_end   = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_start = (start_dt - timedelta(days=period_duration)).strftime("%Y-%m-%d")

            logger.info(
                f"[GA4 CLIENT] get_traffic_overview property={property_id} | "
                f"current={start_date}→{end_date} ({period_duration}d) | "
                f"previous={prev_start}→{prev_end}"
            )

            # ----------------------------------------------------------------
            # Build dimension filter (shared across all 4 requests)
            # ----------------------------------------------------------------
            filter_dict     = GA4FilterBuilder.build_dimension_filter(global_filters)
            dimension_filter = None
            if filter_dict:
                dimension_filter = self._dict_to_filter_expression(filter_dict)
                if dimension_filter:
                    logger.info(
                        f"[GA4 FILTER] Applying filters to get_traffic_overview: "
                        f"{GA4FilterBuilder.get_filter_summary(global_filters)}"
                    )

            # ================================================================
            # REQUEST 1 — Current-period totals (no dimension)
            # Metrics: totalUsers, sessions, newUsers, engagedSessions,
            #          conversions, totalRevenue
            # ================================================================
            totals_request_params = {
                "property":    f"properties/{property_id}",
                "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                "metrics": [
                    Metric(name="totalUsers"),       # index 0
                    Metric(name="sessions"),          # index 1
                    Metric(name="newUsers"),           # index 2
                    Metric(name="engagedSessions"),    # index 3
                    Metric(name="conversions"),        # index 4  ← NEW
                    Metric(name="totalRevenue"),       # index 5  ← NEW
                ],
            }
            if dimension_filter:
                totals_request_params["dimension_filter"] = dimension_filter

            totals_response = client.run_report(RunReportRequest(**totals_request_params), timeout=12)

            totals = {
                "users": 0, "sessions": 0, "newUsers": 0,
                "bounceRate": 0, "averageSessionDuration": 0,
                "engagedSessions": 0, "engagementRate": 0,
                "conversions": 0.0, "revenue": 0.0,
            }

            if totals_response.rows:
                r = totals_response.rows[0]
                totals["users"]           = int(float(r.metric_values[0].value))
                totals["sessions"]        = int(float(r.metric_values[1].value))
                totals["newUsers"]        = int(float(r.metric_values[2].value))
                totals["engagedSessions"] = int(float(r.metric_values[3].value))
                totals["conversions"]     = float(r.metric_values[4].value)
                totals["revenue"]         = float(r.metric_values[5].value)
                logger.info(
                    f"[GA4 CLIENT] Current totals – users={totals['users']}, "
                    f"sessions={totals['sessions']}, newUsers={totals['newUsers']}, "
                    f"conversions={totals['conversions']}, revenue={totals['revenue']}"
                )

            # ================================================================
            # REQUEST 2 — Current-period daily breakdown (date dimension)
            # Metrics: activeUsers, sessions, newUsers, engagedSessions,
            #          bounceRate, averageSessionDuration, engagementRate,
            #          conversions, totalRevenue
            # ================================================================
            daily_request_params = {
                "property":    f"properties/{property_id}",
                "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                "dimensions":  [Dimension(name="date")],
                "metrics": [
                    Metric(name="activeUsers"),          # index 0
                    Metric(name="sessions"),              # index 1
                    Metric(name="newUsers"),               # index 2
                    Metric(name="engagedSessions"),        # index 3
                    Metric(name="bounceRate"),             # index 4
                    Metric(name="averageSessionDuration"), # index 5
                    Metric(name="engagementRate"),         # index 6
                    Metric(name="conversions"),            # index 7  ← NEW
                    Metric(name="totalRevenue"),           # index 8  ← NEW
                ],
            }
            if dimension_filter:
                daily_request_params["dimension_filter"] = dimension_filter

            daily_request  = RunReportRequest(**daily_request_params)
            daily_response = client.run_report(daily_request, timeout=12)

            # Accumulate weighted sums for current-period rate averages
            weighted_duration   = 0.0
            weighted_bounce     = 0.0
            weighted_engagement = 0.0

            daily_data: List[Dict] = []

            for row in daily_response.rows:
                date_str = row.dimension_values[0].value
                rec: Dict = {
                    "date": date_str,
                    "users": 0, "sessions": 0, "newUsers": 0,
                    "bounceRate": 0.0, "averageSessionDuration": 0.0,
                    "engagedSessions": 0, "engagementRate": 0.0,
                    "conversions": 0.0, "revenue": 0.0,
                }
                d_sessions = 0

                for i, mv in enumerate(row.metric_values):
                    name  = daily_request.metrics[i].name
                    value = float(mv.value)
                    if   name == "activeUsers":           rec["users"]                 = int(value)
                    elif name == "sessions":              rec["sessions"]              = int(value);  d_sessions = int(value)
                    elif name == "newUsers":              rec["newUsers"]              = int(value)
                    elif name == "engagedSessions":       rec["engagedSessions"]       = int(value)
                    elif name == "bounceRate":            rec["bounceRate"]            = value
                    elif name == "averageSessionDuration":rec["averageSessionDuration"]= value
                    elif name == "engagementRate":        rec["engagementRate"]        = value
                    elif name == "conversions":           rec["conversions"]           = value     # ← NEW
                    elif name == "totalRevenue":          rec["revenue"]               = value     # ← NEW

                weighted_duration   += rec["averageSessionDuration"] * d_sessions
                weighted_bounce     += rec["bounceRate"]             * d_sessions
                weighted_engagement += rec["engagementRate"]         * d_sessions
                daily_data.append(rec)

            # Compute weighted averages for the full current period
            if totals["sessions"] > 0:
                totals["averageSessionDuration"] = weighted_duration   / totals["sessions"]
                totals["bounceRate"]             = weighted_bounce      / totals["sessions"]
                totals["engagementRate"]         = weighted_engagement  / totals["sessions"]
                logger.info(
                    f"[GA4 CLIENT] Weighted avgs – avgDuration={totals['averageSessionDuration']:.1f}s, "
                    f"bounceRate={totals['bounceRate']:.4f}, engagementRate={totals['engagementRate']:.4f}"
                )

            totals["daily_data"] = daily_data

            # ================================================================
            # REQUEST 3 — Previous-period totals (no dimension)
            # Metrics: totalUsers, sessions, newUsers, engagedSessions,
            #          conversions, totalRevenue
            # ================================================================
            prev_totals: Dict = {
                "users": 0, "sessions": 0, "newUsers": 0,
                "engagedSessions": 0, "bounceRate": 0.0,
                "averageSessionDuration": 0.0, "engagementRate": 0.0,
                "conversions": 0.0, "revenue": 0.0,
            }

            try:
                logger.info(f"[GA4 CLIENT] Fetching previous-period totals {prev_start}→{prev_end}")

                prev_totals_request = RunReportRequest(
                    property=f"properties/{property_id}",
                    date_ranges=[DateRange(start_date=prev_start, end_date=prev_end)],
                    metrics=[
                        Metric(name="totalUsers"),    # index 0
                        Metric(name="sessions"),       # index 1
                        Metric(name="newUsers"),        # index 2  ← NEW
                        Metric(name="engagedSessions"), # index 3
                        Metric(name="conversions"),     # index 4  ← NEW
                        Metric(name="totalRevenue"),    # index 5  ← NEW
                    ],
                )
                prev_totals_response = client.run_report(prev_totals_request, timeout=12)

                if prev_totals_response.rows:
                    r = prev_totals_response.rows[0]
                    prev_totals["users"]           = int(float(r.metric_values[0].value))
                    prev_totals["sessions"]        = int(float(r.metric_values[1].value))
                    prev_totals["newUsers"]        = int(float(r.metric_values[2].value))
                    prev_totals["engagedSessions"] = int(float(r.metric_values[3].value))
                    prev_totals["conversions"]     = float(r.metric_values[4].value)
                    prev_totals["revenue"]         = float(r.metric_values[5].value)
                    logger.info(
                        f"[GA4 CLIENT] Previous totals – users={prev_totals['users']}, "
                        f"sessions={prev_totals['sessions']}, conversions={prev_totals['conversions']}"
                    )

                # ============================================================
                # REQUEST 4 — Previous-period daily (date dimension)
                # Used ONLY for computing weighted-average rates.
                # session counts come from Request 3 (authoritative).
                # ============================================================
                prev_daily_request = RunReportRequest(
                    property=f"properties/{property_id}",
                    date_ranges=[DateRange(start_date=prev_start, end_date=prev_end)],
                    dimensions=[Dimension(name="date")],
                    metrics=[
                        Metric(name="sessions"),              # index 0  (weight only, NOT re-summed)
                        Metric(name="averageSessionDuration"), # index 1
                        Metric(name="engagementRate"),         # index 2
                        Metric(name="bounceRate"),             # index 3  ← NEW (was missing)
                    ],
                )
                prev_daily_response = client.run_report(prev_daily_request, timeout=12)

                prev_weighted_duration   = 0.0
                prev_weighted_engagement = 0.0
                prev_weighted_bounce     = 0.0

                for row in prev_daily_response.rows:
                    d_sessions        = 0
                    d_avg_duration    = 0.0
                    d_engagement_rate = 0.0
                    d_bounce_rate     = 0.0

                    for i, mv in enumerate(row.metric_values):
                        name  = prev_daily_request.metrics[i].name
                        value = float(mv.value)
                        if   name == "sessions":               d_sessions        = int(value)
                        elif name == "averageSessionDuration": d_avg_duration    = value
                        elif name == "engagementRate":         d_engagement_rate = value
                        elif name == "bounceRate":             d_bounce_rate     = value  # ← NEW

                    # NOTE: we do NOT re-add to prev_totals["sessions"] here.
                    # sessions is already correct from Request 3 (no-dimension call).
                    prev_weighted_duration   += d_avg_duration    * d_sessions
                    prev_weighted_engagement += d_engagement_rate * d_sessions
                    prev_weighted_bounce     += d_bounce_rate     * d_sessions   # ← NEW

                # Weighted averages for previous period
                if prev_totals["sessions"] > 0:
                    prev_totals["averageSessionDuration"] = prev_weighted_duration   / prev_totals["sessions"]
                    prev_totals["engagementRate"]         = prev_weighted_engagement / prev_totals["sessions"]
                    prev_totals["bounceRate"]             = prev_weighted_bounce      / prev_totals["sessions"]  # ← NEW

                # ============================================================
                # Compute % changes (current vs previous)
                # ============================================================
                def _pct_change(cur: float, prev: float) -> float:
                    return ((cur - prev) / prev * 100) if prev != 0 else 0.0

                totals["sessionsChange"]          = _pct_change(totals["sessions"],              prev_totals["sessions"])
                totals["engagedSessionsChange"]   = _pct_change(totals["engagedSessions"],       prev_totals["engagedSessions"])
                totals["avgSessionDurationChange"]= _pct_change(totals["averageSessionDuration"],prev_totals["averageSessionDuration"])
                totals["engagementRateChange"]    = _pct_change(totals["engagementRate"],        prev_totals["engagementRate"])

                logger.info(
                    f"[GA4 CLIENT] Changes – sessions={totals['sessionsChange']:.1f}%, "
                    f"engagedSessions={totals['engagedSessionsChange']:.1f}%, "
                    f"avgDuration={totals['avgSessionDurationChange']:.1f}%, "
                    f"engagementRate={totals['engagementRateChange']:.1f}%"
                )

            except Exception as exc:
                logger.warning(f"[GA4 CLIENT] Could not fetch previous-period data: {exc}")
                totals.setdefault("sessionsChange", 0)
                totals.setdefault("engagedSessionsChange", 0)
                totals.setdefault("avgSessionDurationChange", 0)
                totals.setdefault("engagementRateChange", 0)

            # ================================================================
            # Expose previous-period values so callers can consume them
            # without making a redundant second call.
            # ================================================================
            totals["prev_users"]                = prev_totals["users"]
            totals["prev_sessions"]             = prev_totals["sessions"]
            totals["prev_new_users"]            = prev_totals["newUsers"]
            totals["prev_engaged_sessions"]     = prev_totals["engagedSessions"]
            totals["prev_bounce_rate"]          = prev_totals["bounceRate"]
            totals["prev_avg_session_duration"] = prev_totals["averageSessionDuration"]
            totals["prev_engagement_rate"]      = prev_totals["engagementRate"]
            totals["prev_conversions"]          = prev_totals["conversions"]
            totals["prev_revenue"]              = prev_totals["revenue"]

            return totals
        except Exception as e:
            logger.error(f"Error fetching traffic overview: {str(e)}")
            raise
    
    # 2. Top Performing Pages API
    async def get_top_pages(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        global_filters: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:
        """Get top performing pages with optional global filters"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            client = self._get_data_client()
            
            request_params = {
                "property": f"properties/{property_id}",
                "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                "dimensions": [Dimension(name="pagePath")],
                "metrics": [
                    Metric(name="screenPageViews"),
                    Metric(name="activeUsers"),
                    Metric(name="averageSessionDuration"),
                ],
                "limit": limit,
                "order_bys": [
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"),
                        desc=True
                    )
                ],
            }
            
            # Apply global filters
            request_params = self._apply_filters_to_request(request_params, global_filters)
            request = RunReportRequest(**request_params)

            response = client.run_report(request, timeout=12)

            pages = []
            for row in response.rows:
                pages.append({
                    "pagePath": row.dimension_values[0].value,
                    "views": int(row.metric_values[0].value),
                    "users": int(row.metric_values[1].value),
                    "avgSessionDuration": float(row.metric_values[2].value),
                })
            
            return pages
        except Exception as e:
            logger.error(f"Error fetching top pages: {str(e)}")
            raise
    
    # 3. Traffic Sources (Acquisition) API
    async def get_traffic_sources(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        global_filters: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:
        """Get traffic sources breakdown with optional global filters"""
        from app.services.ga4_filter_builder import GA4FilterBuilder
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            client = self._get_data_client()
            
            request_params = {
                "property": f"properties/{property_id}",
                "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                "dimensions": [Dimension(name="sessionDefaultChannelGroup")],  # Use channel dimension instead of source/medium
                "metrics": [
                    Metric(name="sessions"),
                    Metric(name="activeUsers"),
                    Metric(name="bounceRate"),
                    Metric(name="conversions"),  # New: Add conversions metric
                ],
                "order_bys": [
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                        desc=True
                    )
                ],
            }
            
            # Apply global filters
            request_params = self._apply_filters_to_request(request_params, global_filters)
            request = RunReportRequest(**request_params)

            response = client.run_report(request, timeout=12)

            sources = []
            for row in response.rows:
                sessions = int(row.metric_values[0].value)
                conversions = float(row.metric_values[3].value) if len(row.metric_values) > 3 else 0
                conversion_rate = (conversions / sessions * 100) if sessions > 0 else 0
                
                channel = row.dimension_values[0].value
                # Keep source field for backward compatibility, but use channel value
                sources.append({
                    "source": channel,  # Store channel in source field for backward compatibility
                    "channel": channel,  # Add explicit channel field
                    "sessions": sessions,
                    "users": int(row.metric_values[1].value),
                    "bounceRate": float(row.metric_values[2].value),
                    "conversions": conversions,  # New: Conversions count
                    "conversionRate": conversion_rate,  # New: Conversion rate per source
                })
            
            return sources
        except Exception as e:
            logger.error(f"Error fetching traffic sources: {str(e)}")
            raise
    
    # 4. Geographic Breakdown API
    async def get_geographic_breakdown(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20,
        include_daily_breakdown: bool = True,
        global_filters: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:
        """Get geographic breakdown by country with optional global filters
        
        Args:
            property_id: GA4 property ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max number of countries to return (only applies when include_daily_breakdown=False)
            include_daily_breakdown: If True, returns daily data per country. If False, returns aggregated data.
        
        Returns:
            List of dicts with country data. If include_daily_breakdown=True, includes 'date' field.
        """
        from app.services.ga4_filter_builder import GA4FilterBuilder
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            client = self._get_data_client()
            
            # Build dimension filter from global_filters.
            # IMPORTANT: We do NOT exclude 'countries' here – if the user applies a
            # Countries filter, GA4 should restrict results to those countries.
            # This mirrors GA4 UI behavior (filter on country, then view Top Countries).
            dimension_filter = GA4FilterBuilder.build_dimension_filter(global_filters)
            if dimension_filter and global_filters:
                logger.info(
                    f"[GA4 FILTER] Applying filters to get_geographic_breakdown: {GA4FilterBuilder.get_filter_summary(global_filters)}"
                )
            
            if include_daily_breakdown:
                # Return daily breakdown (one record per date per country)
                # engagementRate is included so it can be persisted and later
                # aggregated as a weighted average when reading date-range data.
                request_params = {
                    "property": f"properties/{property_id}",
                    "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                    "dimensions": [
                        Dimension(name="date"),
                        Dimension(name="country")
                    ],
                    "metrics": [
                        Metric(name="activeUsers"),    # index 0
                        Metric(name="sessions"),        # index 1
                        Metric(name="engagementRate"),  # index 2  ← NEW
                    ],
                    # No limit - we need all data for daily storage
                }

                if dimension_filter:
                    request_params["dimension_filter"] = dimension_filter

                request  = RunReportRequest(**request_params)
                response = client.run_report(request, timeout=12)

                daily_data = []
                for row in response.rows:
                    country = row.dimension_values[1].value
                    # Filter out blank, null, or "(not set)" country values
                    if country and country.strip() and country.strip().lower() not in ['(not set)', 'not set', '']:
                        daily_data.append({
                            "date":           row.dimension_values[0].value,
                            "country":        country,
                            "users":          int(float(row.metric_values[0].value)),
                            "sessions":       int(float(row.metric_values[1].value)),
                            "engagementRate": float(row.metric_values[2].value),  # ← NEW
                        })

                logger.info(f"Fetched {len(daily_data)} daily geographic records for {property_id} (filtered out blank countries)")
                return daily_data
            else:
                # Return aggregated breakdown (for display purposes only, not for storage)
                request_params = {
                    "property": f"properties/{property_id}",
                    "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                    "dimensions": [Dimension(name="country")],
                    "metrics": [
                        Metric(name="activeUsers"),
                        Metric(name="sessions"),
                        Metric(name="engagementRate"),
                    ],
                    "limit": limit,
                    "order_bys": [
                        OrderBy(
                            metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                            desc=True
                        )
                    ],
                }
                
                if dimension_filter:
                    request_params["dimension_filter"] = dimension_filter
                
                request = RunReportRequest(**request_params)
                response = client.run_report(request, timeout=12)

                countries = []
                for row in response.rows:
                    country = row.dimension_values[0].value
                    # Filter out blank, null, or "(not set)" country values
                    if country and country.strip() and country.strip().lower() not in ['(not set)', 'not set', '']:
                        countries.append({
                            "country": country,
                            "users": int(row.metric_values[0].value),
                            "sessions": int(row.metric_values[1].value),
                            "engagementRate": float(row.metric_values[2].value) if len(row.metric_values) > 2 else 0,
                        })
                
                logger.info(f"Fetched {len(countries)} geographic countries for {property_id} (filtered out blank countries)")
                return countries
        except Exception as e:
            logger.error(f"Error fetching geographic breakdown: {str(e)}")
            raise
    
    # 5. Device & Platform Insights API
    async def get_device_breakdown(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        global_filters: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:
        """Get device and platform breakdown with optional global filters"""
        from app.services.ga4_filter_builder import GA4FilterBuilder
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            client = self._get_data_client()
            
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="deviceCategory"),
                    Dimension(name="operatingSystem"),
                ],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="sessions"),
                    Metric(name="bounceRate"),
                ],
            )
            
            response = client.run_report(request, timeout=12)

            devices = []
            for row in response.rows:
                devices.append({
                    "deviceCategory": row.dimension_values[0].value,
                    "operatingSystem": row.dimension_values[1].value,
                    "users": int(row.metric_values[0].value),
                    "sessions": int(row.metric_values[1].value),
                    "bounceRate": float(row.metric_values[2].value),
                })
            
            return devices
        except Exception as e:
            logger.error(f"Error fetching device breakdown: {str(e)}")
            raise
    
    # 6. Conversion & Goal Tracking API
    async def get_conversions(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get conversion events"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            client = self._get_data_client()
            
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name="eventName")],
                metrics=[
                    Metric(name="eventCount"),
                    Metric(name="totalUsers"),
                ],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value="conversion"
                        )
                    )
                ),
            )
            
            response = client.run_report(request, timeout=12)

            conversions = []
            for row in response.rows:
                conversions.append({
                    "eventName": row.dimension_values[0].value,
                    "count": int(row.metric_values[0].value),
                    "users": int(row.metric_values[1].value),
                })
            
            return conversions
        except Exception as e:
            logger.error(f"Error fetching conversions: {str(e)}")
            raise
    
    # 7. Realtime Snapshot API
    async def get_realtime_snapshot(self, property_id: str) -> Dict:
        """Get realtime data snapshot"""
        try:
            client = self._get_data_client()
            
            # Realtime API doesn't support pagePath dimension, use city or other supported dimensions
            request = RunRealtimeReportRequest(
                property=f"properties/{property_id}",
                dimensions=[],  # No dimensions for now - just get total active users
                metrics=[
                    Metric(name="activeUsers"),
                ],
            )
            
            response = client.run_realtime_report(request)
            
            active_users = 0
            active_pages = []
            
            # Get total active users
            if response.rows:
                for row in response.rows:
                    active_users += int(row.metric_values[0].value)
            
            # Try to get active pages with a different approach (using pageTitle or screenClass)
            try:
                page_request = RunRealtimeReportRequest(
                    property=f"properties/{property_id}",
                    dimensions=[Dimension(name="pageTitle")],  # Use pageTitle instead of pagePath
                    metrics=[Metric(name="activeUsers")],
                    limit=10
                )
                page_response = client.run_realtime_report(page_request)
                
                for row in page_response.rows:
                    if row.dimension_values[0].value:
                        active_pages.append({
                            "pagePath": row.dimension_values[0].value,  # Actually pageTitle
                            "activeUsers": int(row.metric_values[0].value),
                        })
            except Exception as page_error:
                logger.warning(f"Could not fetch active pages: {str(page_error)}")
                # Continue without pages
            
            return {
                "totalActiveUsers": active_users,
                "activePages": active_pages[:10],  # Top 10 active pages
            }
        except Exception as e:
            logger.error(f"Error fetching realtime snapshot: {str(e)}")
            raise
    
    # 8. Property Details API
    async def get_property_details(self, property_id: str) -> Dict:
        """Get property configuration details"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            property_obj = client.get_property(name=property_name)
            
            return {
                "propertyId": property_id,
                "displayName": property_obj.display_name,
                "timeZone": property_obj.time_zone,
                "currencyCode": property_obj.currency_code,
                "createTime": property_obj.create_time.isoformat() if property_obj.create_time else None,
            }
        except Exception as e:
            logger.error(f"Error fetching property details: {str(e)}")
            raise
    
    # 9. Conversion Configuration API
    async def get_conversion_events(self, property_id: str) -> List[Dict]:
        """Get conversion events configuration"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            conversion_events = client.list_conversion_events(parent=property_name)
            
            events = []
            for event in conversion_events:
                events.append({
                    "eventName": event.event_name,
                    "createTime": event.create_time.isoformat() if event.create_time else None,
                    "deletable": event.deletable,
                    "custom": event.custom,
                })
            
            return events
        except Exception as e:
            logger.error(f"Error fetching conversion events: {str(e)}")
            raise
    
    # 10. Data Streams API
    async def get_data_streams(self, property_id: str) -> List[Dict]:
        """Get data streams for a property"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            streams = client.list_data_streams(parent=property_name)
            
            stream_list = []
            for stream in streams:
                stream_list.append({
                    "streamId": stream.name.split("/")[-1],
                    "displayName": stream.display_name,
                    "type": stream.type_.name if stream.type_ else None,
                    "createTime": stream.create_time.isoformat() if stream.create_time else None,
                })
            
            return stream_list
        except Exception as e:
            logger.error(f"Error fetching data streams: {str(e)}")
            raise
    
    # 11. Custom Dimensions API
    async def get_custom_dimensions(self, property_id: str) -> List[Dict]:
        """Get custom dimensions"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            dimensions = client.list_custom_dimensions(parent=property_name)
            
            dim_list = []
            for dim in dimensions:
                dim_list.append({
                    "parameterName": dim.parameter_name,
                    "displayName": dim.display_name,
                    "description": dim.description,
                    "scope": dim.scope.name if dim.scope else None,
                })
            
            return dim_list
        except Exception as e:
            logger.error(f"Error fetching custom dimensions: {str(e)}")
            raise
    
    # 12. Custom Metrics API
    async def get_custom_metrics(self, property_id: str) -> List[Dict]:
        """Get custom metrics"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            metrics = client.list_custom_metrics(parent=property_name)
            
            metric_list = []
            for metric in metrics:
                metric_list.append({
                    "parameterName": metric.parameter_name,
                    "displayName": metric.display_name,
                    "description": metric.description,
                    "measurementUnit": metric.measurement_unit.name if metric.measurement_unit else None,
                })
            
            return metric_list
        except Exception as e:
            logger.error(f"Error fetching custom metrics: {str(e)}")
            raise
    
    # 13. Audiences API
    async def get_audiences(self, property_id: str) -> List[Dict]:
        """Get audiences configuration"""
        try:
            client = self._get_admin_client()
            property_name = f"properties/{property_id}"
            
            audiences = client.list_audiences(parent=property_name)
            
            audience_list = []
            for audience in audiences:
                audience_list.append({
                    "audienceId": audience.name.split("/")[-1],
                    "displayName": audience.display_name,
                    "description": audience.description,
                    "membershipDurationDays": audience.membership_duration_days,
                })
            
            return audience_list
        except Exception as e:
            logger.error(f"Error fetching audiences: {str(e)}")
            raise
    
    # 14. Account Summaries API
    async def get_account_summaries(self) -> List[Dict]:
        """Get all accessible accounts and properties"""
        try:
            client = self._get_admin_client()
            
            summaries = client.list_account_summaries()
            
            account_list = []
            for summary in summaries:
                for property_summary in summary.property_summaries:
                    account_list.append({
                        "accountId": summary.account.split("/")[-1],
                        "accountDisplayName": summary.display_name,
                        "propertyId": property_summary.property.split("/")[-1],
                        "propertyDisplayName": property_summary.display_name,
                    })
            
            return account_list
        except Exception as e:
            logger.error(f"Error fetching account summaries: {str(e)}")
            raise
    
    # 15. Metadata API
    async def get_metadata(self, property_id: str) -> Dict:
        """Get available metrics and dimensions"""
        try:
            client = self._get_data_client()
            property_name = f"properties/{property_id}"
            
            metadata = client.get_metadata(name=property_name)
            
            dimensions = []
            for dim in metadata.dimensions:
                dimensions.append({
                    "apiName": dim.api_name,
                    "uiName": dim.ui_name,
                    "description": dim.description,
                    "category": dim.category,
                })
            
            metrics = []
            for metric in metadata.metrics:
                metrics.append({
                    "apiName": metric.api_name,
                    "uiName": metric.ui_name,
                    "description": metric.description,
                    "type": metric.type_.name if metric.type_ else None,
                })
            
            return {
                "dimensions": dimensions,
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Error fetching metadata: {str(e)}")
            raise
    
    # Comprehensive method to get all GA4 data for a property
    async def get_all_analytics(
        self,
        property_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get comprehensive GA4 analytics for a property"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch all data in parallel where possible
            traffic_overview = await self.get_traffic_overview(property_id, start_date, end_date)
            top_pages = await self.get_top_pages(property_id, start_date, end_date, limit=10)
            traffic_sources = await self.get_traffic_sources(property_id, start_date, end_date)
            # Use aggregated mode for comprehensive analytics display
            geographic = await self.get_geographic_breakdown(property_id, start_date, end_date, limit=10, include_daily_breakdown=False)
            devices = await self.get_device_breakdown(property_id, start_date, end_date)
            conversions = await self.get_conversions(property_id, start_date, end_date)
            realtime = await self.get_realtime_snapshot(property_id)
            property_details = await self.get_property_details(property_id)
            
            return {
                "trafficOverview": traffic_overview,
                "topPages": top_pages,
                "trafficSources": traffic_sources,
                "geographic": geographic,
                "devices": devices,
                "conversions": conversions,
                "realtime": realtime,
                "propertyDetails": property_details,
                "dateRange": {
                    "startDate": start_date,
                    "endDate": end_date,
                },
            }
        except Exception as e:
            logger.error(f"Error fetching all analytics: {str(e)}")
            raise

