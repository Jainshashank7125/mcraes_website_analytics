from typing import Optional, List, Dict, Any
from datetime import datetime, date as date_type
from pydantic import BaseModel, Field


class DashboardLinkRequest(BaseModel):
    executive_summary: Optional[Dict[str, Any]] = Field(None, description="Executive summary data (structured JSON)")
    slug: Optional[str] = None
    start_date: date_type
    end_date: date_type
    enabled: bool = True
    expires_at: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
    selected_kpis: Optional[List[str]] = None
    visible_sections: Optional[List[str]] = None
    visible_highlights: Optional[List[str]] = None
    selected_charts: Optional[List[str]] = None
    selected_performance_metrics_kpis: Optional[List[str]] = None
    show_change_period: Optional[Dict[str, bool]] = Field(None, description="Per-section flags for showing change period indicators")
    # Global filters configuration for this dashboard link (applied to GA4 data)
    # Example: {"user_type": ["new"], "countries": ["United States"], "traffic_channels": ["Organic Search"]}
    global_filters: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Global filters configuration for this dashboard link (user_type, traffic_channels, traffic_sources, countries, regions, cities, page_urls, conversion_types, conversion_by)",
    )

class DashboardLinkUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    enabled: Optional[bool] = None
    expires_at: Optional[datetime] = None
    slug: Optional[str] = None
    selected_kpis: Optional[List[str]] = None
    visible_sections: Optional[List[str]] = None
    visible_highlights: Optional[List[str]] = None
    selected_charts: Optional[List[str]] = None
    selected_performance_metrics_kpis: Optional[List[str]] = None
    show_change_period: Optional[Dict[str, bool]] = Field(None, description="Per-section flags for showing change period indicators")
    # Allow updating global filters independently of other link fields
    global_filters: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Global filters configuration for this dashboard link (user_type, traffic_channels, traffic_sources, countries, regions, cities, page_urls, conversion_types, conversion_by)",
    )
    executive_summary: Optional[Dict[str, Any]] = Field(None, description="Executive summary data (structured JSON)")
