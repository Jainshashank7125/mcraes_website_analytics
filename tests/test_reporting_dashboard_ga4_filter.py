"""
Backend tests for reporting dashboard GA4 country filter: with/without filter and remove-filter restores behavior.

Verifies:
- Without filter: global_filters is None, response has kpis/chart_data (same as before).
- With filter: global_filters is passed through, response structure unchanged.
- Remove filter: second call without filter gets global_filters=None again (exact functionality back).

Run:
  pytest tests/test_reporting_dashboard_ga4_filter.py -v
"""

import os
import sys
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# main.py is at project root; app is the FastAPI instance
from main import app


# Minimal dashboard response shape (same with or without filter)
def _minimal_dashboard_response(global_filters_received=None):
    return {
        "kpis": {},
        "chart_data": {
            "ga4_traffic_overview": None,
            "ga4_daily_comparison": [],
            "users_over_time": [],
            "traffic_sources": [],
            "top_pages": [],
            "geographic_breakdown": [],
            "device_breakdown": [],
        },
        "global_filters_received": global_filters_received,
    }


@pytest.fixture
def mock_get_reporting_dashboard():
    """Patch get_reporting_dashboard to capture global_filters and return minimal response."""
    async def _fake_dashboard(brand_id, start_date, end_date, client_id=None, db=None, global_filters=None, **kwargs):
        return _minimal_dashboard_response(global_filters)
    with patch("app.api.data.get_reporting_dashboard", side_effect=_fake_dashboard) as m:
        yield m


@pytest.fixture
def mock_db_and_client():
    """Provide a mock DB session and make get_client_by_id return a client with GA4."""
    with patch("app.api.data.get_db") as get_db:
        session = MagicMock()
        get_db.return_value = session
        with patch("app.api.data.SupabaseService") as SupabaseService:
            svc = MagicMock()
            svc.get_client_by_id.return_value = {
                "id": 1,
                "company_name": "Test Client",
                "ga4_property_id": "12345",
                "scrunch_brand_id": 100,
            }
            SupabaseService.return_value = svc
            yield get_db, SupabaseService


def test_reporting_dashboard_without_filter_passes_none_and_returns_structure(mock_get_reporting_dashboard, mock_db_and_client):
    """Without filter: API passes global_filters=None; response has kpis and chart_data."""
    client = TestClient(app)
    resp = client.get(
        "/api/v1/data/reporting-dashboard/client/1",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "chart_data" in data
    assert data.get("global_filters_received") is None
    mock_get_reporting_dashboard.assert_called_once()
    call_kwargs = mock_get_reporting_dashboard.call_args[1]
    assert call_kwargs.get("global_filters") is None


def test_reporting_dashboard_with_filter_passes_filter_and_same_structure(mock_get_reporting_dashboard, mock_db_and_client):
    """With filter: API passes global_filters={'countries': ['United States']}; response structure unchanged."""
    client = TestClient(app)
    import json
    filters = {"countries": ["United States"]}
    resp = client.get(
        "/api/v1/data/reporting-dashboard/client/1",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "global_filters": json.dumps(filters),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "chart_data" in data
    assert data.get("global_filters_received") == filters
    mock_get_reporting_dashboard.assert_called_once()
    call_kwargs = mock_get_reporting_dashboard.call_args[1]
    assert call_kwargs.get("global_filters") == filters


def test_remove_filter_restores_exact_functionality(mock_get_reporting_dashboard, mock_db_and_client):
    """Call without filter -> with filter -> without filter again. Last call gets global_filters=None (exact same as first)."""
    client = TestClient(app)
    import json
    # 1) Without filter
    r1 = client.get(
        "/api/v1/data/reporting-dashboard/client/1",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    assert r1.status_code == 200
    assert r1.json().get("global_filters_received") is None
    first_call_filters = mock_get_reporting_dashboard.call_args[1].get("global_filters")
    assert first_call_filters is None
    # 2) With filter
    mock_get_reporting_dashboard.reset_mock()
    r2 = client.get(
        "/api/v1/data/reporting-dashboard/client/1",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "global_filters": json.dumps({"countries": ["United States"]}),
        },
    )
    assert r2.status_code == 200
    assert r2.json().get("global_filters_received") == {"countries": ["United States"]}
    # 3) Without filter again (filter removed)
    mock_get_reporting_dashboard.reset_mock()
    r3 = client.get(
        "/api/v1/data/reporting-dashboard/client/1",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    assert r3.status_code == 200
    assert r3.json().get("global_filters_received") is None
    third_call_filters = mock_get_reporting_dashboard.call_args[1].get("global_filters")
    assert third_call_filters is None
    # Same as first: no filter
    assert first_call_filters == third_call_filters
