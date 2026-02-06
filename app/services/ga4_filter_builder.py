"""
GA4 Filter Builder - Converts global filter configurations to GA4 API dimension filters

This module provides utilities to transform user-friendly filter configurations
(e.g., {"user_type": ["new", "returning"], "countries": ["USA", "Canada"]})
into GA4 API-compatible dimension filter expressions.

Filter Types Supported:
- user_type: New vs Returning users
- traffic_channels: Session default channel grouping
- traffic_sources: Session source
- countries: Geographic country filter
- regions: Geographic region/state filter
- cities: Geographic city filter
- page_urls: Page path filter
- device_categories: Device category filter
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GA4FilterBuilder:
    """Utility class for building GA4 API dimension filters from global filter configurations"""
    
    # Mapping from our filter keys to GA4 dimension names
    DIMENSION_MAP = {
        'user_type': 'newVsReturning',
        'traffic_channels': 'sessionDefaultChannelGrouping',
        'traffic_sources': 'sessionSource',
        'countries': 'country',
        'regions': 'region',
        'cities': 'city',
        'page_urls': 'pagePath',
        'device_categories': 'deviceCategory',
    }
    
    @staticmethod
    def build_dimension_filter(
        global_filters: Optional[Dict[str, List[str]]],
        exclude_dimensions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Convert global filters dictionary to GA4 API dimensionFilter structure
        
        Args:
            global_filters: Dictionary of filter dimensions and their values
                           Example: {"user_type": ["new"], "countries": ["USA", "Canada"]}
            exclude_dimensions: List of filter keys to exclude from the filter
                               Useful when you want to display a dimension rather than filter by it
        
        Returns:
            GA4 dimensionFilter dict or None if no filters to apply
            
        Example output:
            {
                "andGroup": {
                    "expressions": [
                        {
                            "filter": {
                                "fieldName": "newVsReturning",
                                "inListFilter": {"values": ["new"]}
                            }
                        },
                        {
                            "filter": {
                                "fieldName": "country",
                                "inListFilter": {"values": ["USA", "Canada"]}
                            }
                        }
                    ]
                }
            }
        """
        if not global_filters:
            return None
        
        exclude_dimensions = exclude_dimensions or []
        expressions = []
        
        for filter_key, filter_values in global_filters.items():
            # Skip if no values or if dimension is excluded
            if not filter_values or not isinstance(filter_values, list) or filter_key in exclude_dimensions:
                continue
            
            # Get GA4 dimension name
            ga4_dimension = GA4FilterBuilder.DIMENSION_MAP.get(filter_key)
            if not ga4_dimension:
                logger.warning(f"Unknown filter dimension: {filter_key}, skipping")
                continue
            
            # Build filter expression
            expressions.append({
                "filter": {
                    "fieldName": ga4_dimension,
                    "inListFilter": {
                        "values": filter_values
                    }
                }
            })
        
        # Return None if no expressions (no filters to apply)
        if not expressions:
            return None
        
        # Return andGroup structure (all filters must match)
        return {
            "andGroup": {
                "expressions": expressions
            }
        }
    
    @staticmethod
    def get_filter_summary(global_filters: Optional[Dict[str, List[str]]]) -> str:
        """
        Generate a human-readable summary of applied filters for logging
        
        Args:
            global_filters: Dictionary of filter dimensions and their values
        
        Returns:
            String summary like "user_type: new | countries: USA, Canada"
        """
        if not global_filters:
            return "No filters"
        
        parts = []
        for key, values in global_filters.items():
            if values and isinstance(values, list):
                parts.append(f"{key}: {', '.join(values)}")
        
        return " | ".join(parts) if parts else "No filters"
