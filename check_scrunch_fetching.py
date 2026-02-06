#!/usr/bin/env python3
"""
Check if clients are fetching data from Scrunch API
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

def check_scrunch_fetching():
    """Check Scrunch data fetching for specific clients"""
    db = SessionLocal()
    
    client_names = [
        "Grow 3",
        "Canadian Shade",
        "City duct cleaning",
        "MGA",
        "Polypak"
    ]
    
    try:
        print("=" * 70)
        print("Checking Scrunch Data Fetching")
        print("=" * 70)
        print()
        
        for client_name in client_names:
            # Search for client
            clients = db.query(Client).filter(
                or_(
                    Client.company_name.ilike(f'%{client_name}%'),
                    Client.company_name.ilike(client_name)
                )
            ).all()
            
            if not clients:
                print(f"❌ Client '{client_name}' NOT FOUND")
                print()
                continue
            
            for client in clients:
                print(f"Client: {client.company_name}")
                print(f"  ID: {client.id}")
                print(f"  Scrunch Brand ID: {client.scrunch_brand_id or 'NOT SET'}")
                print()
                
                if not client.scrunch_brand_id:
                    print("  ❌ scrunch_brand_id is NOT configured")
                    print("     Cannot fetch from Scrunch without brand ID")
                    print()
                    continue
                
                brand_id = client.scrunch_brand_id
                print(f"  ✅ scrunch_brand_id configured: {brand_id}")
                print()
                
                # Check prompts from database
                prompts_count = db.query(func.count(Prompt.id)).filter(
                    Prompt.brand_id == brand_id
                ).scalar()
                
                print(f"  Prompts in database: {prompts_count}")
                
                # Check responses from database
                responses_count = db.query(func.count(Response.id)).filter(
                    Response.brand_id == brand_id
                ).scalar()
                
                print(f"  Responses in database: {responses_count}")
                print()
                
                # Check when data was last synced (check latest prompt/response dates)
                latest_prompt = db.query(Prompt).filter(
                    Prompt.brand_id == brand_id
                ).order_by(Prompt.created_at.desc()).first()
                
                latest_response = db.query(Response).filter(
                    Response.brand_id == brand_id
                ).order_by(Response.created_at.desc()).first()
                
                if latest_prompt:
                    print(f"  Latest prompt synced: {latest_prompt.created_at}")
                else:
                    print(f"  ⚠️  No prompts found in database")
                
                if latest_response:
                    print(f"  Latest response synced: {latest_response.created_at}")
                else:
                    print(f"  ⚠️  No responses found in database")
                
                print()
                
                # Check if data is recent (within last 7 days)
                if latest_response:
                    days_since_sync = (datetime.now(latest_response.created_at.tzinfo) - latest_response.created_at).days
                    if days_since_sync > 7:
                        print(f"  ⚠️  Data is {days_since_sync} days old - may need to sync")
                    else:
                        print(f"  ✅ Data is recent (synced {days_since_sync} days ago)")
                
                print()
                print("  To fetch fresh data from Scrunch:")
                print(f"    POST /api/v1/sync/prompts?brand_id={brand_id}")
                print(f"    POST /api/v1/sync/responses?brand_id={brand_id}")
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("Data in database indicates:")
        print("1. If prompts/responses exist → Data was fetched from Scrunch")
        print("2. Latest sync date shows when data was last fetched")
        print("3. If data is old → Run sync to fetch fresh data")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_scrunch_fetching()
