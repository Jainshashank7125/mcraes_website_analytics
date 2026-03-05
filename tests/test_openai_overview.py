"""
Tests for AI overview / executive summary:
- Section filtering (no KeyError when only a subset of sections is visible)
- validate_executive_summary
- _round_for_overview
"""
import pytest
from app.api.openai import validate_executive_summary, _round_for_overview


# --- Section filtering: ensure kpis_by_source and chart logic work with partial sections ---
SECTION_KEY_MAP = {"ga4": "GA4", "agency_analytics": "AgencyAnalytics", "scrunch_ai": "Scrunch"}


def test_structured_data_and_kpis_by_source_with_only_ga4():
    """When visible_sections has only ga4, structured_data has only GA4; kpis_by_source must not assume other keys."""
    all_sections = {
        "GA4": {"section_name": "GA4", "kpis": [], "charts": {}},
        "AgencyAnalytics": {"section_name": "AA", "kpis": [], "charts": {}},
        "Scrunch": {"section_name": "Scrunch", "kpis": [], "charts": {}},
    }
    visible_sections = {"ga4"}
    structured_data = {}
    for vk in visible_sections:
        mk = SECTION_KEY_MAP.get(vk)
        if mk and mk in all_sections:
            structured_data[mk] = dict(all_sections[mk])
            structured_data[mk]["kpis"] = list(structured_data[mk]["kpis"])
            structured_data[mk]["charts"] = dict(structured_data[mk]["charts"])
    # Simulate one KPI in GA4
    structured_data["GA4"]["kpis"].append({"label": "Total Users", "value": 1000})
    # Build kpis_by_source from whatever sections exist (no fixed keys)
    kpis_by_source = {k: v["kpis"] for k, v in structured_data.items()}
    all_metrics = []
    for _src, metrics in kpis_by_source.items():
        all_metrics.extend(metrics)
    assert list(kpis_by_source.keys()) == ["GA4"]
    assert len(all_metrics) == 1
    assert all_metrics[0]["label"] == "Total Users"


def test_structured_data_and_kpis_by_source_with_ga4_and_scrunch():
    """Two sections only: GA4 and Scrunch; no AgencyAnalytics."""
    all_sections = {
        "GA4": {"section_name": "GA4", "kpis": [], "charts": {}},
        "AgencyAnalytics": {"section_name": "AA", "kpis": [], "charts": {}},
        "Scrunch": {"section_name": "Scrunch", "kpis": [], "charts": {}},
    }
    visible_sections = {"ga4", "scrunch_ai"}
    structured_data = {}
    for vk in visible_sections:
        mk = SECTION_KEY_MAP.get(vk)
        if mk and mk in all_sections:
            structured_data[mk] = dict(all_sections[mk])
            structured_data[mk]["kpis"] = list(structured_data[mk]["kpis"])
            structured_data[mk]["charts"] = dict(structured_data[mk]["charts"])
    structured_data["GA4"]["kpis"].append({"label": "Users", "value": 500})
    structured_data["Scrunch"]["kpis"].append({"label": "Mentions", "value": 10})
    kpis_by_source = {k: v["kpis"] for k, v in structured_data.items()}
    all_metrics = []
    for _src, metrics in kpis_by_source.items():
        all_metrics.extend(metrics)
    assert set(kpis_by_source.keys()) == {"GA4", "Scrunch"}
    assert len(all_metrics) == 2


# --- validate_executive_summary ---
def test_validate_executive_summary_valid():
    valid = {
        "header": {
            "client_name": "Acme",
            "program_name": "Program",
            "reporting_period": "Jan 2025",
            "overall_status": "✅ Positive momentum",
        },
        "executive_summary": "Summary text.",
        "what_worked": ["a", "b", "c"],
        "what_to_watch": ["x", "y"],
        "ai_visibility_snapshot": ["p", "q"],
        "content_authority_snapshot": ["m", "n"],
        "focus_next_30_days": ["1", "2", "3"],
        "client_action_needed": "None.",
    }
    assert validate_executive_summary(valid) is None


def test_validate_executive_summary_missing_section():
    valid = {
        "header": {"client_name": "A", "program_name": "P", "reporting_period": "Jan", "overall_status": "✅ On track"},
        "executive_summary": "S",
        "what_worked": ["a", "b", "c"],
        "what_to_watch": ["x", "y"],
        "ai_visibility_snapshot": ["p", "q"],
        "content_authority_snapshot": ["m", "n"],
        "focus_next_30_days": ["1", "2", "3"],
        "client_action_needed": "None.",
    }
    # Missing section
    incomplete = {**valid}
    del incomplete["what_to_watch"]
    err = validate_executive_summary(incomplete)
    assert err is not None
    assert "what_to_watch" in err or "required" in err.lower()


def test_validate_executive_summary_invalid_status():
    valid = {
        "header": {"client_name": "A", "program_name": "P", "reporting_period": "Jan", "overall_status": "✅ On track"},
        "executive_summary": "S",
        "what_worked": ["a", "b", "c"],
        "what_to_watch": ["x", "y"],
        "ai_visibility_snapshot": ["p", "q"],
        "content_authority_snapshot": ["m", "n"],
        "focus_next_30_days": ["1", "2", "3"],
        "client_action_needed": "None.",
    }
    bad = {**valid, "header": {**valid["header"], "overall_status": "Bad status"}}
    err = validate_executive_summary(bad)
    assert err is not None


# --- _round_for_overview ---
def test_round_for_overview_number():
    assert _round_for_overview(1.735487, "number") == 1.74
    # Values >= 1000 round to 0 decimals per openai._round_for_overview
    assert _round_for_overview(1000.1, "number") == 1000.0
    assert _round_for_overview(100.12, "number") == 100.12


def test_round_for_overview_percentage():
    assert _round_for_overview(84.567, "percentage") == 84.6


def test_round_for_overview_none():
    assert _round_for_overview(None, "number") is None
