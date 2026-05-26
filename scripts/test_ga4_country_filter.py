#!/usr/bin/env python3
"""
Test GA4 country filter: verify each KPI/chart source returns filtered data correctly.

Compares unfiltered vs filtered (countries=["United States"]) for:
- get_traffic_overview (KPIs: users, sessions, new_users, engaged_sessions, bounce_rate, etc.)
- get_traffic_sources (charts: ga4_traffic_sources_distribution, ga4_sessions_by_channel)
- get_geographic_breakdown (charts: ga4_geographic_distribution, ga4_top_countries)
- get_top_pages (chart: ga4_top_pages)
- get_device_breakdown (chart: device_breakdown)
- get_conversions (KPI: conversions)

Usage:
  # Use property_id from env or first client in DB with ga4_property_id
  python scripts/test_ga4_country_filter.py

  # Specify property and date range
  python scripts/test_ga4_country_filter.py --property-id 93484123 --start-date 2026-01-01 --end-date 2026-01-31

  # Use different country
  python scripts/test_ga4_country_filter.py --country "United Kingdom"
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timedelta

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ga4_client import GA4APIClient
from app.db.database import SessionLocal
from app.services.supabase_service import SupabaseService


def get_test_property_id(from_db: bool = True):
    """Get GA4 property_id from env GA4_TEST_PROPERTY_ID or from DB (first client with ga4_property_id)."""
    pid = os.environ.get("GA4_TEST_PROPERTY_ID", "").strip()
    if pid:
        return pid
    if not from_db:
        return None
    db = SessionLocal()
    try:
        supabase = SupabaseService(db=db)
        # Get first client with ga4_property_id
        from sqlalchemy import text
        r = db.execute(text(
            "SELECT id, company_name, ga4_property_id FROM clients WHERE ga4_property_id IS NOT NULL AND ga4_property_id != '' LIMIT 1"
        ))
        row = r.fetchone()
        if row:
            return row[2]
    finally:
        db.close()
    return None


async def run_tests(property_id: str, start_date: str, end_date: str, country: str = "United States"):
    client = GA4APIClient()
    filters = {"countries": [country]}
    errors = []
    checks = []

    def ok(name: str, passed: bool, msg: str):
        checks.append((name, passed, msg))
        if not passed:
            errors.append(f"{name}: {msg}")

    # ---- 1. get_traffic_overview ----
    try:
        unfiltered = await client.get_traffic_overview(property_id, start_date, end_date, global_filters=None)
        filtered = await client.get_traffic_overview(property_id, start_date, end_date, global_filters=filters)
    except Exception as e:
        ok("get_traffic_overview", False, str(e))
        unfiltered = filtered = None

    if unfiltered is not None and filtered is not None:
        u_users = unfiltered.get("users", 0)
        f_users = filtered.get("users", 0)
        u_sessions = unfiltered.get("sessions", 0)
        f_sessions = filtered.get("sessions", 0)
        ok("traffic_overview (filtered <= unfiltered)", f_users <= u_users and f_sessions <= u_sessions,
           f"users: {f_users} <= {u_users}, sessions: {f_sessions} <= {u_sessions}")
        ok("traffic_overview (daily_data when filter)", not filters or "daily_data" in filtered,
           "daily_data present in filtered response")
        # Optional: if we expect some traffic from country, filtered > 0 when unfiltered > 0
        if u_sessions > 0 and f_sessions == 0:
            checks.append(("traffic_overview (filtered>0 hint)", True, "filtered=0 (no traffic from country in range?)"))

    # ---- 2. get_traffic_sources ----
    try:
        unfiltered_s = await client.get_traffic_sources(property_id, start_date, end_date, global_filters=None)
        filtered_s = await client.get_traffic_sources(property_id, start_date, end_date, global_filters=filters)
    except Exception as e:
        ok("get_traffic_sources", False, str(e))
        unfiltered_s = filtered_s = []

    if unfiltered_s is not None and filtered_s is not None:
        u_sum = sum(x.get("sessions", 0) for x in unfiltered_s)
        f_sum = sum(x.get("sessions", 0) for x in filtered_s)
        ok("traffic_sources (filtered <= unfiltered)", f_sum <= u_sum,
           f"sum sessions: {f_sum} <= {u_sum}")

    # ---- 3. get_geographic_breakdown ----
    try:
        unfiltered_g = await client.get_geographic_breakdown(
            property_id, start_date, end_date, limit=50, include_daily_breakdown=False, global_filters=None
        )
        filtered_g = await client.get_geographic_breakdown(
            property_id, start_date, end_date, limit=50, include_daily_breakdown=False, global_filters=filters
        )
    except Exception as e:
        ok("get_geographic_breakdown", False, str(e))
        unfiltered_g = filtered_g = []

    if unfiltered_g is not None and filtered_g is not None:
        countries_in_filtered = [x.get("country") for x in filtered_g if x.get("country")]
        # GA4 can return full name or ISO code; allow both (we send both in filter)
        from app.services.ga4_filter_builder import GA4FilterBuilder
        iso = GA4FilterBuilder.COUNTRY_NAME_TO_ISO.get(country, country)
        allowed = {country, iso}
        only_selected = all(c in allowed for c in countries_in_filtered) if countries_in_filtered else True
        ok("geographic_breakdown (only selected country)", only_selected or len(filtered_g) == 0,
           f"countries in filtered: {countries_in_filtered}")

    # ---- 4. get_top_pages ----
    try:
        unfiltered_p = await client.get_top_pages(property_id, start_date, end_date, limit=20, global_filters=None)
        filtered_p = await client.get_top_pages(property_id, start_date, end_date, limit=20, global_filters=filters)
    except Exception as e:
        ok("get_top_pages", False, str(e))
        unfiltered_p = filtered_p = []

    if unfiltered_p is not None and filtered_p is not None:
        u_views = sum(x.get("views", 0) for x in unfiltered_p)
        f_views = sum(x.get("views", 0) for x in filtered_p)
        ok("top_pages (filtered <= unfiltered)", f_views <= u_views, f"sum views: {f_views} <= {u_views}")

    # ---- 5. get_device_breakdown ----
    try:
        unfiltered_d = await client.get_device_breakdown(property_id, start_date, end_date, global_filters=None)
        filtered_d = await client.get_device_breakdown(property_id, start_date, end_date, global_filters=filters)
    except Exception as e:
        ok("get_device_breakdown", False, str(e))
        unfiltered_d = filtered_d = []

    if unfiltered_d is not None and filtered_d is not None:
        u_sess = sum(x.get("sessions", 0) for x in unfiltered_d)
        f_sess = sum(x.get("sessions", 0) for x in filtered_d)
        ok("device_breakdown (filtered <= unfiltered)", f_sess <= u_sess, f"sum sessions: {f_sess} <= {u_sess}")

    # ---- 6. get_conversions ----
    try:
        unfiltered_c = await client.get_conversions(property_id, start_date, end_date, global_filters=None)
        filtered_c = await client.get_conversions(property_id, start_date, end_date, global_filters=filters)
    except Exception as e:
        ok("get_conversions", False, str(e))
        unfiltered_c = filtered_c = []

    if unfiltered_c is not None and filtered_c is not None:
        u_conv = sum(x.get("count", 0) for x in unfiltered_c)
        f_conv = sum(x.get("count", 0) for x in filtered_c)
        ok("get_conversions (filtered <= unfiltered)", f_conv <= u_conv, f"total count: {f_conv} <= {u_conv}")

    return errors, checks


def main():
    parser = argparse.ArgumentParser(description="Test GA4 country filter on all KPI/chart sources")
    parser.add_argument("--property-id", type=str, help="GA4 property ID (default: env or DB)")
    parser.add_argument("--start-date", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="End date YYYY-MM-DD")
    parser.add_argument("--country", type=str, default="United States", help="Country to filter (default: United States)")
    parser.add_argument("--no-db", action="store_true", help="Do not read property_id from DB")
    parser.add_argument("--dry-run", action="store_true", help="Only run filter-builder checks (no GA4 API calls)")
    args = parser.parse_args()

    if args.dry_run:
        from app.services.ga4_filter_builder import GA4FilterBuilder
        f = GA4FilterBuilder.build_dimension_filter({"countries": [args.country]})
        assert f is not None and "andGroup" in f and f["andGroup"]["expressions"][0]["filter"]["fieldName"] == "countryId"
        vals = f["andGroup"]["expressions"][0]["filter"]["inListFilter"]["values"]
        assert "US" in vals or args.country in vals or (GA4FilterBuilder.COUNTRY_NAME_TO_ISO.get(args.country, args.country) in vals)
        print("DRY-RUN PASSED: Filter builder produces correct country dimension filter.")
        sys.exit(0)

    property_id = args.property_id or get_test_property_id(from_db=not args.no_db)
    if not property_id:
        print("ERROR: No property_id. Set GA4_TEST_PROPERTY_ID or run with --property-id or use DB.")
        sys.exit(2)

    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"Testing GA4 country filter: property_id={property_id}, {start_date} to {end_date}, country={args.country}")
    print("=" * 60)

    errors, checks = asyncio.run(run_tests(property_id, start_date, end_date, args.country))

    for name, passed, msg in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {msg}")

    print("=" * 60)
    if errors:
        print("FAILED:", len(errors), "check(s)")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("ALL CHECKS PASSED. Filtered data behaves as expected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
