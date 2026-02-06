#!/usr/bin/env python3
"""
Script to check Aeroport taxi client's geographic data for blank country names
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, GA4Geographic
from sqlalchemy import func, and_, or_, desc
from datetime import datetime

def check_aeroport_taxi_geographic():
    """Check Aeroport taxi client's geographic data"""
    db = SessionLocal()
    
    try:
        # Search for client with "Aeroport taxi" in the name
        clients = db.query(Client).filter(
            or_(
                Client.company_name.ilike('%Aeroport taxi%'),
                Client.company_name.ilike('%aeroport taxi%'),
                Client.company_name.ilike('%Aeroport%'),
                Client.company_name.ilike('%taxi%')
            )
        ).all()
        
        if not clients:
            print("❌ No clients found with 'Aeroport taxi' in the name")
            return
        
        print("=" * 70)
        print("Checking Aeroport Taxi Client Geographic Data")
        print("=" * 70)
        print()
        
        for client in clients:
            print(f"Client: {client.company_name}")
            print(f"  ID: {client.id}")
            print(f"  GA4 Property ID: {client.ga4_property_id or 'NOT SET'}")
            print()
            
            if not client.ga4_property_id:
                print("  ❌ No GA4 Property ID configured")
                continue
            
            property_id = client.ga4_property_id
            
            # Get geographic data
            geographic_records = db.query(GA4Geographic).filter(
                and_(
                    GA4Geographic.client_id == client.id,
                    GA4Geographic.property_id == property_id
                )
            ).order_by(desc(GA4Geographic.date)).limit(50).all()
            
            print(f"  Total Geographic Records: {len(geographic_records)}")
            print()
            
            if len(geographic_records) == 0:
                print("  ❌ NO GEOGRAPHIC DATA found")
                continue
            
            # Check for blank/null country names
            blank_countries = []
            countries_with_data = []
            
            for record in geographic_records:
                country = record.country
                if not country or country.strip() == '' or country == '(not set)':
                    blank_countries.append({
                        'id': record.id,
                        'date': record.date,
                        'country': country,
                        'users': record.users,
                        'sessions': record.sessions
                    })
                else:
                    countries_with_data.append({
                        'country': country,
                        'users': record.users,
                        'sessions': record.sessions
                    })
            
            print(f"  Records with blank/null country names: {len(blank_countries)}")
            print(f"  Records with valid country names: {len(countries_with_data)}")
            print()
            
            if blank_countries:
                print("  ⚠️  BLANK COUNTRY NAMES FOUND:")
                print("  " + "-" * 66)
                for item in blank_countries[:10]:  # Show first 10
                    print(f"    ID: {item['id']}, Date: {item['date']}, Country: '{item['country']}', Sessions: {item['sessions']}")
                if len(blank_countries) > 10:
                    print(f"    ... and {len(blank_countries) - 10} more")
                print()
            
            # Show unique countries
            unique_countries = set()
            for record in geographic_records:
                if record.country and record.country.strip() and record.country != '(not set)':
                    unique_countries.add(record.country)
            
            print(f"  Unique countries with data: {len(unique_countries)}")
            if unique_countries:
                print(f"  Countries: {', '.join(sorted(list(unique_countries))[:20])}")
                if len(unique_countries) > 20:
                    print(f"    ... and {len(unique_countries) - 20} more")
            print()
            
            # Check latest date
            if geographic_records:
                latest_date = max(r.date for r in geographic_records)
                print(f"  Latest geographic data date: {latest_date}")
                print()
            
            # Check if there's a pattern (e.g., all blank on certain dates)
            if blank_countries:
                dates_with_blanks = {}
                for item in blank_countries:
                    date_str = str(item['date'])
                    if date_str not in dates_with_blanks:
                        dates_with_blanks[date_str] = 0
                    dates_with_blanks[date_str] += 1
                
                print("  Dates with blank country names:")
                for date_str, count in sorted(dates_with_blanks.items())[:10]:
                    print(f"    {date_str}: {count} records")
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("If blank country names are found, possible causes:")
        print("1. GA4 API returning '(not set)' or empty country values")
        print("2. Data sync issue - country field not being populated")
        print("3. Need to filter out blank countries in the API response")
        print()
    
    except Exception as e:
        print(f"❌ Error checking geographic data: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_aeroport_taxi_geographic()
