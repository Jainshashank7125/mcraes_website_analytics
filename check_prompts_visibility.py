#!/usr/bin/env python3
"""
Script to check why prompts are not visible for specific clients
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from sqlalchemy import func, and_, or_

def check_clients_prompts():
    """Check prompts visibility for specific clients"""
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
        print("Checking Prompts Visibility for Clients")
        print("=" * 70)
        print()
        
        for client_name in client_names:
            # Search for client (case insensitive, partial match)
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
                print("=" * 70)
                print(f"Client: {client.company_name}")
                print(f"  ID: {client.id}")
                print(f"  Active: {client.is_active}")
                print(f"  Scrunch Brand ID: {client.scrunch_brand_id or 'NOT SET'}")
                print(f"  GA4 Property ID: {client.ga4_property_id or 'NOT SET'}")
                print()
                
                # Check if scrunch_brand_id is configured
                if not client.scrunch_brand_id:
                    print("  ❌ scrunch_brand_id is NOT configured")
                    print("     This is why prompts are not visible!")
                    print("     Solution: Assign a Scrunch Brand ID to this client.")
                    print()
                    continue
                
                brand_id = client.scrunch_brand_id
                print(f"  ✅ scrunch_brand_id is configured: {brand_id}")
                print()
                
                # Check for prompts in database
                prompts_count = db.query(func.count(Prompt.id)).filter(
                    Prompt.brand_id == brand_id
                ).scalar()
                
                print(f"  Prompts in database: {prompts_count}")
                
                # Check for responses in database
                responses_count = db.query(func.count(Response.id)).filter(
                    Response.brand_id == brand_id
                ).scalar()
                
                print(f"  Responses in database: {responses_count}")
                print()
                
                if prompts_count == 0:
                    print("  ❌ NO PROMPTS in database for this brand")
                    print("     This is why prompts are not visible!")
                    print("     Solution: Run a prompts sync for this brand.")
                    print(f"     API: POST /api/v1/sync/prompts?brand_id={brand_id}")
                    print()
                elif prompts_count > 0:
                    print(f"  ✅ Prompts exist in database ({prompts_count} records)")
                    print("     Prompts should be visible. Checking date range...")
                    
                    # Check date range of prompts
                    latest_prompt = db.query(Prompt).filter(
                        Prompt.brand_id == brand_id
                    ).order_by(Prompt.created_at.desc()).first()
                    
                    if latest_prompt and latest_prompt.created_at:
                        print(f"     Latest prompt date: {latest_prompt.created_at}")
                    
                    # Check if prompts are within a reasonable date range
                    from datetime import datetime, timedelta
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    
                    recent_prompts = db.query(func.count(Prompt.id)).filter(
                        and_(
                            Prompt.brand_id == brand_id,
                            Prompt.created_at >= thirty_days_ago
                        )
                    ).scalar()
                    
                    print(f"     Prompts in last 30 days: {recent_prompts}")
                    print()
                
                if responses_count == 0:
                    print("  ⚠️  NO RESPONSES in database for this brand")
                    print("     This might affect prompt analytics.")
                    print()
                else:
                    print(f"  ✅ Responses exist in database ({responses_count} records)")
                    print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print()
        print("Common issues:")
        print("1. scrunch_brand_id not configured - prompts won't be visible")
        print("2. Prompts not synced - need to run sync/prompts endpoint")
        print("3. Date range filtering - prompts might be outside visible date range")
        print()
    
    except Exception as e:
        print(f"❌ Error checking clients: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_clients_prompts()
