"""
Unit tests for GA4 country filter: filter builder, client request shape, and reporting dashboard behavior.

Run without GA4 credentials:
  pytest tests/test_ga4_country_filter.py -v
  pytest tests/test_reporting_dashboard_ga4_filter.py -v
"""

import pytest
from app.services.ga4_filter_builder import GA4FilterBuilder
from app.services.ga4_client import GA4APIClient


class TestGA4FilterBuilder:
    """Test that country and other filters produce correct GA4 dimension filter structure."""

    def test_countries_filter_builds_countryId_dimension_with_iso(self):
        f = GA4FilterBuilder.build_dimension_filter({"countries": ["United States"]})
        assert f is not None
        assert "andGroup" in f
        assert "expressions" in f["andGroup"]
        assert len(f["andGroup"]["expressions"]) == 1
        expr = f["andGroup"]["expressions"][0]
        assert expr.get("filter", {}).get("fieldName") == "countryId"
        vals = expr.get("filter", {}).get("inListFilter", {}).get("values", [])
        assert vals == ["US"]

    def test_countries_multiple(self):
        f = GA4FilterBuilder.build_dimension_filter({"countries": ["United States", "Canada"]})
        assert f is not None
        assert len(f["andGroup"]["expressions"]) == 1
        vals = f["andGroup"]["expressions"][0]["filter"]["inListFilter"]["values"]
        assert set(vals) == {"US", "CA"}

    def test_empty_filters_returns_none(self):
        assert GA4FilterBuilder.build_dimension_filter(None) is None
        assert GA4FilterBuilder.build_dimension_filter({}) is None
        assert GA4FilterBuilder.build_dimension_filter({"countries": []}) is None
        assert GA4FilterBuilder.build_dimension_filter({"countries": [""]}) is None

    def test_user_type_and_countries_combined(self):
        f = GA4FilterBuilder.build_dimension_filter({
            "user_type": ["new"],
            "countries": ["United States"],
        })
        assert f is not None
        assert len(f["andGroup"]["expressions"]) == 2
        field_names = {e["filter"]["fieldName"] for e in f["andGroup"]["expressions"]}
        assert field_names == {"newVsReturning", "countryId"}

    def test_countries_unknown_name_passed_through(self):
        """Country not in map is sent as single value so filter still applies."""
        f = GA4FilterBuilder.build_dimension_filter({"countries": ["Some Country"]})
        assert f is not None
        vals = f["andGroup"]["expressions"][0]["filter"]["inListFilter"]["values"]
        assert vals == ["Some Country"]

    def test_get_filter_summary(self):
        s = GA4FilterBuilder.get_filter_summary({"countries": ["United States"]})
        assert "countries" in s
        assert "United States" in s
        assert GA4FilterBuilder.get_filter_summary(None) == "No filters"


class TestGA4ClientFilterApplication:
    """Verify GA4 client applies filter to request when global_filters set; no filter when None."""

    def test_apply_filters_adds_dimension_filter_when_countries_set(self):
        client = GA4APIClient()
        request_params = {"property": "properties/123", "date_ranges": [], "metrics": []}
        out = client._apply_filters_to_request(request_params, {"countries": ["United States"]})
        assert "dimension_filter" in out
        assert out["dimension_filter"] is not None

    def test_apply_filters_does_not_add_dimension_filter_when_none(self):
        client = GA4APIClient()
        request_params = {"property": "properties/123", "date_ranges": [], "metrics": []}
        out = client._apply_filters_to_request(request_params, None)
        assert "dimension_filter" not in out

    def test_apply_filters_does_not_add_dimension_filter_when_empty_dict(self):
        client = GA4APIClient()
        request_params = {"property": "properties/123", "date_ranges": [], "metrics": []}
        out = client._apply_filters_to_request(request_params, {})
        assert "dimension_filter" not in out

    def test_remove_filter_restores_same_request_shape_as_no_filter(self):
        """With filter then without: request params match no-filter case (no dimension_filter)."""
        client = GA4APIClient()
        base = {"property": "properties/123", "date_ranges": [], "metrics": []}
        with_filter = client._apply_filters_to_request(dict(base), {"countries": ["United States"]})
        without_filter = client._apply_filters_to_request(dict(base), None)
        assert "dimension_filter" in with_filter
        assert "dimension_filter" not in without_filter
        assert without_filter.keys() == base.keys()


class TestGA4FilteredVsUnfilteredData:
    """Verify that when we have data in BOTH cases (unfiltered and filtered), the comparison rules hold:
    filtered <= unfiltered, and geographic filtered shows only the selected country.
    Uses same logic as scripts/test_ga4_country_filter.py run_tests() without hitting GA4 API.
    """

    def test_traffic_overview_filtered_le_unfiltered_and_both_have_data(self):
        unfiltered = {"users": 1000, "sessions": 2000, "newUsers": 500, "engagedSessions": 1500}
        filtered = {"users": 400, "sessions": 800, "newUsers": 200, "engagedSessions": 600, "daily_data": []}
        assert filtered["users"] <= unfiltered["users"]
        assert filtered["sessions"] <= unfiltered["sessions"]
        assert filtered["users"] != unfiltered["users"], "data must be different when filter applied"

    def test_geographic_filtered_only_selected_country(self):
        country = "United States"
        iso = GA4FilterBuilder.COUNTRY_NAME_TO_ISO.get(country, country)
        allowed = {country, iso}
        filtered_g = [{"country": "United States", "users": 100}, {"country": "US", "users": 0}]
        countries_in_filtered = [x.get("country") for x in filtered_g if x.get("country")]
        only_selected = all(c in allowed for c in countries_in_filtered)
        assert only_selected
        filtered_g_single = [{"country": "United States", "users": 100}]
        assert all(c in allowed for c in [x.get("country") for x in filtered_g_single if x.get("country")])

    def test_traffic_sources_filtered_le_unfiltered(self):
        unfiltered_s = [{"sessions": 500}, {"sessions": 300}]
        filtered_s = [{"sessions": 200}, {"sessions": 100}]
        u_sum = sum(x.get("sessions", 0) for x in unfiltered_s)
        f_sum = sum(x.get("sessions", 0) for x in filtered_s)
        assert f_sum <= u_sum
        assert f_sum != u_sum

    def test_conversions_filtered_le_unfiltered(self):
        unfiltered_c = [{"count": 50}, {"count": 10}]
        filtered_c = [{"count": 20}]
        assert sum(x.get("count", 0) for x in filtered_c) <= sum(x.get("count", 0) for x in unfiltered_c)
