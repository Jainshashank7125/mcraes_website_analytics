#!/usr/bin/env python3
"""
Script to resync GA4 geographic data for all clients.

This script fixes the issue where geographic session totals don't match
traffic overview totals due to incomplete syncs.

Usage:
    # Resync all clients for December 2025
    python scripts/resync_geographic_data.py
    
    # Resync specific date range
    python scripts/resync_geographic_data.py --start-date 2025-11-01 --end-date 2025-11-30
    
    # Resync specific client
    python scripts/resync_geographic_data.py --client-id 9
    
    # Dry run (no changes)
    python scripts/resync_geographic_data.py --dry-run
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, '/app')

from app.services.ga4_client import GA4APIClient
from app.services.supabase_service import SupabaseService


async def resync_geographic(client_id: int, property_id: str, start_date: str, end_date: str, 
                           supabase: SupabaseService, ga4_client: GA4APIClient, dry_run: bool = False):
    """Resync geographic data for a single client."""
    
    # Fetch geographic data from API
    geo_data = await ga4_client.get_geographic_breakdown(
        property_id, start_date, end_date,
        limit=None, include_daily_breakdown=True
    )
    
    if not geo_data:
        return 0, 0, "No data from API"
    
    unique_dates = set(r.get('date') for r in geo_data if r.get('date'))
    total_sessions = sum(r.get('sessions', 0) for r in geo_data)
    
    if dry_run:
        return len(geo_data), total_sessions, f"DRY RUN: Would insert {len(geo_data)} records"
    
    # Format dates for deletion
    formatted_dates = set()
    for d in unique_dates:
        if len(d) == 8:  # YYYYMMDD format
            formatted_dates.add(f'{d[:4]}-{d[4:6]}-{d[6:8]}')
        else:
            formatted_dates.add(d)
    
    # Delete existing data
    for d in formatted_dates:
        delete_query = text('''
            DELETE FROM ga4_geographic 
            WHERE client_id = :client_id AND property_id = :property_id AND date = :date
        ''')
        supabase.db.execute(delete_query, {'client_id': client_id, 'property_id': property_id, 'date': d})
    supabase.db.commit()
    
    # Insert fresh data
    count = supabase.upsert_ga4_geographic(property_id, '', geo_data, client_id=client_id, brand_id=None)
    
    return count, total_sessions, "Success"


async def resync_all_clients(start_date: str, end_date: str, client_id: int = None, dry_run: bool = False):
    """Resync geographic data for all clients (or a specific client)."""
    
    ga4_client = GA4APIClient()
    supabase = SupabaseService()
    
    # Get clients with GA4 property IDs
    if client_id:
        query = text('''
            SELECT id as client_id, ga4_property_id as property_id, company_name
            FROM clients
            WHERE ga4_property_id IS NOT NULL AND ga4_property_id != ''
            AND id = :client_id
        ''')
        result = supabase.db.execute(query, {'client_id': client_id})
    else:
        query = text('''
            SELECT id as client_id, ga4_property_id as property_id, company_name
            FROM clients
            WHERE ga4_property_id IS NOT NULL AND ga4_property_id != ''
            ORDER BY id
        ''')
        result = supabase.db.execute(query)
    
    clients = list(result)
    
    print(f"{'DRY RUN: ' if dry_run else ''}Resyncing geographic data")
    print(f"Found {len(clients)} clients with GA4 properties")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 70)
    
    success_count = 0
    error_count = 0
    total_records = 0
    
    for row in clients:
        client_id = row.client_id
        property_id = row.property_id
        company_name = row.company_name[:30]
        
        try:
            count, sessions, status = await resync_geographic(
                client_id, property_id, start_date, end_date,
                supabase, ga4_client, dry_run
            )
            
            if count > 0:
                print(f"[{client_id:>3}] {company_name:<30}: {count:>5} records, {sessions:>7} sessions")
                success_count += 1
                total_records += count
            else:
                print(f"[{client_id:>3}] {company_name:<30}: {status}")
                
        except Exception as e:
            print(f"[{client_id:>3}] {company_name:<30}: ERROR - {str(e)[:40]}")
            error_count += 1
    
    print("=" * 70)
    print(f"Completed: {success_count} success, {error_count} errors, {total_records} total records")
    
    if not dry_run:
        # Verify results
        print("\nVerification:")
        verify_query = text('''
            WITH traffic AS (
                SELECT client_id, SUM(sessions) as sessions
                FROM ga4_traffic_overview
                WHERE date >= :start_date AND date <= :end_date
                GROUP BY client_id
            ),
            geo AS (
                SELECT client_id, SUM(sessions) as sessions
                FROM ga4_geographic
                WHERE date >= :start_date AND date <= :end_date
                GROUP BY client_id
            )
            SELECT 
                COUNT(DISTINCT t.client_id) as clients,
                SUM(t.sessions) as traffic_total,
                SUM(g.sessions) as geo_total
            FROM traffic t
            LEFT JOIN geo g ON t.client_id = g.client_id
        ''')
        verify_result = supabase.db.execute(verify_query, {'start_date': start_date, 'end_date': end_date})
        vrow = verify_result.first()
        if vrow:
            pct_diff = ((vrow.geo_total / vrow.traffic_total) - 1) * 100 if vrow.traffic_total else 0
            print(f"  Total clients: {vrow.clients}")
            print(f"  Traffic sessions: {vrow.traffic_total}")
            print(f"  Geographic sessions: {vrow.geo_total}")
            print(f"  Difference: {pct_diff:.1f}% (expected: 0-30%)")


def main():
    parser = argparse.ArgumentParser(description='Resync GA4 geographic data')
    parser.add_argument('--start-date', default='2025-12-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2025-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--client-id', type=int, help='Specific client ID to resync')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without making them')
    
    args = parser.parse_args()
    
    asyncio.run(resync_all_clients(
        start_date=args.start_date,
        end_date=args.end_date,
        client_id=args.client_id,
        dry_run=args.dry_run
    ))


if __name__ == '__main__':
    main()
