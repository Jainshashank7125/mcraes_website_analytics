#!/usr/bin/env python3
"""
Script to check if "3d printer" client has complete GA4 data
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, GA4TrafficOverview, GA4TopPages, GA4TrafficSources, GA4Geographic, GA4Devices, GA4Conversions, GA4Realtime, GA4PropertyDetails, GA4Revenue, GA4DailyConversions, GA4KPISnapshots
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

def check_client_data():
    """Check if 3d printer client has complete GA4 data"""
    db = SessionLocal()
    
    try:
        # Search for clients with "3d printer" in the name (case insensitive)
        clients = db.query(Client).filter(
            or_(
                Client.company_name.ilike('%3d printer%'),
                Client.company_name.ilike('%3D printer%'),
                Client.company_name.ilike('%3DPrinter%'),
                Client.company_name.ilike('%3dprinter%')
            )
        ).all()
        
        if not clients:
            print("❌ No clients found with '3d printer' in the name")
            # Try alternative searches
            clients = db.query(Client).filter(
                Client.company_name.ilike('%printer%')
            ).all()
            if clients:
                print(f"\nFound {len(clients)} clients with 'printer' in name:")
                for c in clients:
                    print(f"  - ID: {c.id}, Name: {c.company_name}")
            return
        
        print(f"✅ Found {len(clients)} client(s) with '3d printer' in name:\n")
        
        for client in clients:
            print("=" * 70)
            print(f"Client ID: {client.id}")
            print(f"Company Name: {client.company_name}")
            print(f"Active: {client.is_active}")
            print(f"GA4 Property ID: {client.ga4_property_id or 'NOT SET'}")
            print(f"Scrunch Brand ID: {client.scrunch_brand_id or 'NOT SET'}")
            print(f"URL Slug: {client.url_slug or 'NOT SET'}")
            print()
            
            # Check if GA4 property ID is configured
            if not client.ga4_property_id:
                print("❌ GA4 Property ID is NOT configured for this client")
                print("   This is why GA4 data cannot be seen.")
                print("   Solution: Assign a GA4 Property ID to this client.")
                continue
            
            property_id = client.ga4_property_id
            print(f"✅ GA4 Property ID is configured: {property_id}")
            print()
            
            # Check for GA4 data in various tables
            print("Checking GA4 data tables:")
            print("-" * 70)
            
            # 1. Traffic Overview
            traffic_count = db.query(func.count(GA4TrafficOverview.id)).filter(
                and_(
                    GA4TrafficOverview.client_id == client.id,
                    GA4TrafficOverview.property_id == property_id
                )
            ).scalar()
            print(f"  Traffic Overview: {traffic_count} records")
            
            # 2. Top Pages
            top_pages_count = db.query(func.count(GA4TopPages.id)).filter(
                and_(
                    GA4TopPages.client_id == client.id,
                    GA4TopPages.property_id == property_id
                )
            ).scalar()
            print(f"  Top Pages: {top_pages_count} records")
            
            # 3. Traffic Sources
            traffic_sources_count = db.query(func.count(GA4TrafficSources.id)).filter(
                and_(
                    GA4TrafficSources.client_id == client.id,
                    GA4TrafficSources.property_id == property_id
                )
            ).scalar()
            print(f"  Traffic Sources: {traffic_sources_count} records")
            
            # 4. Geographic
            geographic_count = db.query(func.count(GA4Geographic.id)).filter(
                and_(
                    GA4Geographic.client_id == client.id,
                    GA4Geographic.property_id == property_id
                )
            ).scalar()
            print(f"  Geographic: {geographic_count} records")
            
            # 5. Devices
            devices_count = db.query(func.count(GA4Devices.id)).filter(
                and_(
                    GA4Devices.client_id == client.id,
                    GA4Devices.property_id == property_id
                )
            ).scalar()
            print(f"  Devices: {devices_count} records")
            
            # 6. Conversions
            conversions_count = db.query(func.count(GA4Conversions.id)).filter(
                and_(
                    GA4Conversions.client_id == client.id,
                    GA4Conversions.property_id == property_id
                )
            ).scalar()
            print(f"  Conversions: {conversions_count} records")
            
            # 7. Realtime
            realtime_count = db.query(func.count(GA4Realtime.id)).filter(
                and_(
                    GA4Realtime.client_id == client.id,
                    GA4Realtime.property_id == property_id
                )
            ).scalar()
            print(f"  Realtime: {realtime_count} records")
            
            # 8. Property Details
            property_details = db.query(GA4PropertyDetails).filter(
                and_(
                    GA4PropertyDetails.client_id == client.id,
                    GA4PropertyDetails.property_id == property_id
                )
            ).first()
            print(f"  Property Details: {'✅ Found' if property_details else '❌ Not found'}")
            
            # 9. Revenue
            revenue_count = db.query(func.count(GA4Revenue.id)).filter(
                and_(
                    GA4Revenue.client_id == client.id,
                    GA4Revenue.property_id == property_id
                )
            ).scalar()
            print(f"  Revenue: {revenue_count} records")
            
            # 10. Daily Conversions
            daily_conversions_count = db.query(func.count(GA4DailyConversions.id)).filter(
                and_(
                    GA4DailyConversions.client_id == client.id,
                    GA4DailyConversions.property_id == property_id
                )
            ).scalar()
            print(f"  Daily Conversions: {daily_conversions_count} records")
            
            # 11. KPI Snapshots
            kpi_snapshots_count = db.query(func.count(GA4KPISnapshots.id)).filter(
                and_(
                    GA4KPISnapshots.client_id == client.id,
                    GA4KPISnapshots.property_id == property_id
                )
            ).scalar()
            print(f"  KPI Snapshots: {kpi_snapshots_count} records")
            
            print()
            
            # Check date ranges
            if traffic_count > 0:
                latest_date = db.query(func.max(GA4TrafficOverview.date)).filter(
                    and_(
                        GA4TrafficOverview.client_id == client.id,
                        GA4TrafficOverview.property_id == property_id
                    )
                ).scalar()
                earliest_date = db.query(func.min(GA4TrafficOverview.date)).filter(
                    and_(
                        GA4TrafficOverview.client_id == client.id,
                        GA4TrafficOverview.property_id == property_id
                    )
                ).scalar()
                print(f"  Date Range: {earliest_date} to {latest_date}")
                print()
            
            # Summary
            total_records = (
                traffic_count + top_pages_count + traffic_sources_count +
                geographic_count + devices_count + conversions_count +
                realtime_count + revenue_count + daily_conversions_count +
                kpi_snapshots_count
            )
            
            if total_records == 0:
                print("❌ NO GA4 DATA FOUND in database")
                print("   This client has a GA4 Property ID configured, but no data has been synced.")
                print("   Solution: Run a GA4 sync for this client.")
            elif traffic_count == 0:
                print("⚠️  PARTIAL DATA: Traffic Overview is missing (most important)")
                print("   Solution: Run a GA4 sync for this client.")
            else:
                print(f"✅ GA4 DATA FOUND: {total_records} total records across all tables")
                if traffic_count > 0:
                    print(f"   Traffic Overview has {traffic_count} records (main data source)")
            
            print()
    
    except Exception as e:
        print(f"❌ Error checking client data: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_client_data()
