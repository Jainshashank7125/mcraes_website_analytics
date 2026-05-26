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

NOTE: GA4 Data API uses FilterExpression objects, not raw dictionaries.
This builder creates dict structures that can be converted to FilterExpression
objects in the GA4 client.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GA4FilterBuilder:
    """Utility class for building GA4 API dimension filters from global filter configurations"""
    
    # Mapping from our filter keys to GA4 dimension names.
    # GA4 Data API schema: https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
    # sessionDefaultChannelGroup = Session default channel group (Direct, Organic Search, etc.)
    DIMENSION_MAP = {
        'user_type': 'newVsReturning',
        'traffic_channels': 'sessionDefaultChannelGroup',  # GA4 Data API dimension name
        'traffic_sources': 'sessionSource',
        'countries': 'countryId',  # API expects countryId with ISO codes for dimension_filter
        'regions': 'region',
        'cities': 'city',
        'page_urls': 'pagePath',
        'device_categories': 'deviceCategory',
    }
    
    # Display name -> ISO 3166-1 alpha-2 for countryId filter (GA4 Data API standard).
    COUNTRY_NAME_TO_ISO: Dict[str, str] = {
        "United States": "US",
        "Canada": "CA",
        "United Kingdom": "GB",
        "Australia": "AU",
        "Germany": "DE",
        "France": "FR",
        "Italy": "IT",
        "Spain": "ES",
        "Netherlands": "NL",
        "Belgium": "BE",
        "Switzerland": "CH",
        "Austria": "AT",
        "Sweden": "SE",
        "Norway": "NO",
        "Denmark": "DK",
        "Finland": "FI",
        "Poland": "PL",
        "Ireland": "IE",
        "Portugal": "PT",
        "Greece": "GR",
        "Czech Republic": "CZ",
        "Romania": "RO",
        "Hungary": "HU",
        "China": "CN",
        "Japan": "JP",
        "South Korea": "KR",
        "India": "IN",
        "Singapore": "SG",
        "Malaysia": "MY",
        "Thailand": "TH",
        "Indonesia": "ID",
        "Philippines": "PH",
        "Vietnam": "VN",
        "Taiwan": "TW",
        "Hong Kong": "HK",
        "New Zealand": "NZ",
        "Brazil": "BR",
        "Mexico": "MX",
        "Argentina": "AR",
        "Chile": "CL",
        "Colombia": "CO",
        "Peru": "PE",
        "South Africa": "ZA",
        "Egypt": "EG",
        "United Arab Emirates": "AE",
        "Saudi Arabia": "SA",
        "Israel": "IL",
        "Turkey": "TR",
        "Russia": "RU",
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
                                "fieldName": "countryId",
                                "inListFilter": {"values": ["US", "CA"]}
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
        
        # #region agent log
        try:
            import json, time
            debug_payload = {
                "sessionId": "ae9ab7",
                "runId": "pre-fix",
                "hypothesisId": "H2",
                "location": "ga4_filter_builder.py:build_dimension_filter:before_loop",
                "message": "Entering build_dimension_filter",
                "data": {
                    "global_filters": global_filters,
                    "exclude_dimensions": exclude_dimensions,
                },
                "timestamp": int(time.time() * 1000),
            }
            with open("/root/mcraes_website_analytics_staging/.cursor/debug-ae9ab7.log", "a", encoding="utf-8") as _f:
                _f.write(json.dumps(debug_payload) + "\n")
        except Exception:
            pass
        # #endregion
        
        for filter_key, filter_values in global_filters.items():
            # Skip if no values or if dimension is excluded
            if not filter_values or not isinstance(filter_values, list) or filter_key in exclude_dimensions:
                continue
            
            # Get GA4 dimension name
            ga4_dimension = GA4FilterBuilder.DIMENSION_MAP.get(filter_key)
            if not ga4_dimension:
                logger.warning(f"Unknown filter dimension: {filter_key}, skipping")
                continue
            
            # Build filter expression matching GA4's exact structure
            # GA4 uses: evaluationType: 1 (exact match), isCaseSensitive: true
            # Our inListFilter provides exact match (equivalent to evaluationType: 1)
            # GA4 URL shows: expressionList: ["United States"] -> maps to inListFilter.values
            
            normalized_values = filter_values
            if filter_key == 'countries':
                # GA4 Data API: filter by countryId with ISO 3166-1 alpha-2 codes only.
                iso_codes = []
                for v in filter_values:
                    if not v or not v.strip():
                        continue
                    name = v.strip()
                    if name in GA4FilterBuilder.COUNTRY_NAME_TO_ISO:
                        iso_codes.append(GA4FilterBuilder.COUNTRY_NAME_TO_ISO[name])
                    elif len(name) == 2 and name.isupper():
                        iso_codes.append(name)
                    else:
                        iso_codes.append(name)
                normalized_values = list(dict.fromkeys(iso_codes))
                logger.info(
                    f"[GA4 FILTER] Country filter (countryId + ISO): {normalized_values}"
                )
                # #region agent log
                try:
                    import json, time
                    debug_payload = {
                        "sessionId": "ae9ab7",
                        "runId": "pre-fix",
                        "hypothesisId": "H3",
                        "location": "ga4_filter_builder.py:build_dimension_filter:countries",
                        "message": "Normalized country filters",
                        "data": {
                            "raw_values": filter_values,
                            "normalized_values": normalized_values,
                        },
                        "timestamp": int(time.time() * 1000),
                    }
                    with open("/root/mcraes_website_analytics_staging/.cursor/debug-ae9ab7.log", "a", encoding="utf-8") as _f:
                        _f.write(json.dumps(debug_payload) + "\n")
                except Exception:
                    pass
                # #endregion
            else:
                # For other dimensions, preserve case and use exact match
                normalized_values = [v.strip() for v in filter_values if v and v.strip()]
            if not normalized_values:
                continue
            # Build filter expression matching GA4's structure
            # GA4 uses: type: 1 (dimension filter), fieldName: "countryId", inListFilter (ISO codes)
            expressions.append({
                "filter": {
                    "fieldName": ga4_dimension,
                    "inListFilter": {
                        "values": normalized_values
                    }
                }
            })
        
        # Return None if no expressions (no filters to apply)
        if not expressions:
            return None
        
        result = {
            "andGroup": {
                "expressions": expressions
            }
        }
        # #region agent log
        try:
            import json, time
            debug_payload = {
                "sessionId": "ae9ab7",
                "runId": "pre-fix",
                "hypothesisId": "H3",
                "location": "ga4_filter_builder.py:build_dimension_filter:return",
                "message": "Built GA4 dimension filter dict",
                "data": {
                    "result": result,
                },
                "timestamp": int(time.time() * 1000),
            }
            with open("/root/mcraes_website_analytics_staging/.cursor/debug-ae9ab7.log", "a", encoding="utf-8") as _f:
                _f.write(json.dumps(debug_payload) + "\n")
        except Exception:
            pass
        # #endregion
        # Return andGroup structure (all filters must match)
        return result
    
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
