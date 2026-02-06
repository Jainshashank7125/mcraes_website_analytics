#!/usr/bin/env python3
"""
Fix Client 27 (3DPrinterOS) Duplicate GA4 Property Data

Root Cause: Client 27 has data from TWO GA4 property IDs:
  - Old Property: 321222128
  - Current Property: 284911826

This script deletes all data for the old property ID (321222128) to fix incorrect KPI values.

Affected Date Range: November 2025 - January 2026
"""

import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from sqlalchemy import text

CLIENT_ID = 27
OLD_PROPERTY_ID = '321222128'
CURRENT_PROPERTY_ID = '284911826'

def analyze_duplicate_data(db):
    """Analyze the extent of duplicate data before deletion"""
    print("=" * 80)
    print("ANALYZING DUPLICATE DATA FOR CLIENT 27")
    print("=" * 80)
    
    # Check ga4_traffic_overview
    result = db.execute(text("""
        SELECT 
            property_id,
            COUNT(*) as records,
            MIN(date) as first_date,
            MAX(date) as last_date,
            SUM(users) as total_users,
            SUM(sessions) as total_sessions
        FROM ga4_traffic_overview 
        WHERE client_id = :client_id
        GROUP BY property_id
        ORDER BY property_id
    """), {"client_id": CLIENT_ID})
    
    rows = result.fetchall()
    print(f"\nGA4 Traffic Overview Table:")
    print(f"{'Property ID':15} {'Records':>10} {'Date Range':30} {'Users':>12} {'Sessions':>12}")
    print("-" * 85)
    for row in rows:
        date_range = f"{row[2]} to {row[3]}" if row[2] and row[3] else "N/A"
        print(f"{row[0]:15} {row[1]:>10} {date_range:30} {row[4]:>12} {row[5]:>12}")
    
    # Check other GA4 tables
    tables = [
        'ga4_top_pages',
        'ga4_traffic_sources', 
        'ga4_geographic',
        'ga4_devices',
        'ga4_conversions',
        'ga4_realtime',
        'ga4_revenue',
        'ga4_daily_conversions'
    ]
    
    print(f"\nOther GA4 Tables:")
    print(f"{'Table Name':30} {'Property {OLD_PROPERTY_ID}':>25} {'Property {CURRENT_PROPERTY_ID}':>25}")
    print("-" * 85)
    
    for table in tables:
        try:
            result = db.execute(text(f"""
                SELECT property_id, COUNT(*) 
                FROM {table}
                WHERE client_id = :client_id
                GROUP BY property_id
                ORDER BY property_id
            """), {"client_id": CLIENT_ID})
            rows = result.fetchall()
            
            old_count = 0
            new_count = 0
            for row in rows:
                if row[0] == OLD_PROPERTY_ID:
                    old_count = row[1]
                elif row[0] == CURRENT_PROPERTY_ID:
                    new_count = row[1]
            
            print(f"{table:30} {old_count:>25} {new_count:>25}")
        except Exception as e:
            print(f"{table:30} {'Error: ' + str(e)[:40]:>25}")
    
    print("\n" + "=" * 80)

def delete_old_property_data(db, dry_run=True):
    """Delete data for the old property ID"""
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No data will be deleted\n")
    else:
        print("\n⚠️  DELETION MODE - Data will be permanently deleted\n")
    
    tables = [
        'ga4_traffic_overview',
        'ga4_top_pages',
        'ga4_traffic_sources',
        'ga4_geographic',
        'ga4_devices',
        'ga4_conversions',
        'ga4_realtime',
        'ga4_revenue',
        'ga4_daily_conversions',
        'ga4_kpi_snapshots'
    ]
    
    total_deleted = 0
    
    for table in tables:
        try:
            # Check how many records would be deleted
            result = db.execute(text(f"""
                SELECT COUNT(*) 
                FROM {table}
                WHERE client_id = :client_id AND property_id = :property_id
            """), {"client_id": CLIENT_ID, "property_id": OLD_PROPERTY_ID})
            count = result.scalar()
            
            if count > 0:
                print(f"  {table:30} - {count:>6} records to delete")
                
                if not dry_run:
                    # Delete the records
                    result = db.execute(text(f"""
                        DELETE FROM {table}
                        WHERE client_id = :client_id AND property_id = :property_id
                    """), {"client_id": CLIENT_ID, "property_id": OLD_PROPERTY_ID})
                    
                    deleted = result.rowcount
                    total_deleted += deleted
                    print(f"    ✅ Deleted {deleted} records")
                else:
                    total_deleted += count
            
        except Exception as e:
            print(f"  {table:30} - Error: {str(e)[:50]}")
    
    print(f"\nTotal records {'to delete' if dry_run else 'deleted'}: {total_deleted}")
    
    if not dry_run:
        db.commit()
        print("\n✅ Changes committed to database")
    
    return total_deleted

def verify_cleanup(db):
    """Verify that cleanup was successful"""
    print("\n" + "=" * 80)
    print("VERIFICATION: Checking for remaining old property data")
    print("=" * 80 + "\n")
    
    result = db.execute(text("""
        SELECT COUNT(*) 
        FROM ga4_traffic_overview 
        WHERE client_id = :client_id AND property_id = :property_id
    """), {"client_id": CLIENT_ID, "property_id": OLD_PROPERTY_ID})
    
    remaining = result.scalar()
    
    if remaining == 0:
        print(f"✅ SUCCESS: No data found for old property {OLD_PROPERTY_ID}")
        print(f"   All data now uses current property {CURRENT_PROPERTY_ID}")
    else:
        print(f"⚠️  WARNING: Still found {remaining} records for old property {OLD_PROPERTY_ID}")
        return False
    
    # Show December 2025 data after cleanup
    print(f"\nDecember 2025 Data After Cleanup:")
    result = db.execute(text("""
        SELECT 
            property_id,
            COUNT(*) as records,
            SUM(users) as total_users,
            SUM(sessions) as total_sessions,
            SUM(new_users) as total_new_users,
            SUM(conversions) as total_conversions
        FROM ga4_traffic_overview 
        WHERE client_id = :client_id 
            AND date >= '2025-12-01' 
            AND date <= '2025-12-31'
        GROUP BY property_id
    """), {"client_id": CLIENT_ID})
    
    rows = result.fetchall()
    print(f"{'Property ID':15} {'Records':>10} {'Users':>12} {'Sessions':>12} {'New Users':>12} {'Conversions':>12}")
    print("-" * 85)
    for row in rows:
        print(f"{row[0]:15} {row[1]:>10} {row[2]:>12} {row[3]:>12} {row[4]:>12} {row[5]:>12}")
    
    return True

def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("CLIENT 27 DUPLICATE GA4 PROPERTY DATA CLEANUP")
    print("=" * 80)
    print(f"\nClient ID: {CLIENT_ID}")
    print(f"Client Name: 3DPrinterOS")
    print(f"Old Property ID (to delete): {OLD_PROPERTY_ID}")
    print(f"Current Property ID (to keep): {CURRENT_PROPERTY_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db = SessionLocal()
    
    try:
        # Step 1: Analyze duplicate data
        analyze_duplicate_data(db)
        
        # Step 2: Dry run - show what would be deleted
        print("\n" + "=" * 80)
        print("STEP 1: DRY RUN (Preview)")
        print("=" * 80)
        delete_old_property_data(db, dry_run=True)
        
        # Step 3: Confirm deletion
        print("\n" + "=" * 80)
        response = input("\nProceed with deletion? (type 'DELETE' to confirm): ")
        
        if response.strip() == 'DELETE':
            print("\n" + "=" * 80)
            print("STEP 2: DELETING OLD PROPERTY DATA")
            print("=" * 80)
            delete_old_property_data(db, dry_run=False)
            
            # Step 4: Verify
            success = verify_cleanup(db)
            
            if success:
                print("\n" + "=" * 80)
                print("✅ CLEANUP COMPLETED SUCCESSFULLY")
                print("=" * 80)
                print("\nNext steps:")
                print("1. Test the KPI endpoint for December 2025:")
                print("   curl 'http://localhost:8000/api/v1/data/reporting-dashboard/client/27?start_date=2025-12-01&end_date=2025-12-31'")
                print("2. Verify KPI values are now correct")
                print("3. Check the frontend dashboard for client 27")
            else:
                print("\n⚠️  Cleanup verification failed. Please review manually.")
        else:
            print("\n❌ Deletion cancelled by user")
            print("   No changes were made to the database")
    
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
