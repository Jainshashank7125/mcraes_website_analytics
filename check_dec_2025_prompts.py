#!/usr/bin/env python3
"""
Check prompts and responses for December 1-31, 2025
"""
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from sqlalchemy import func, and_, or_

def check_dec_2025_data():
    """Check data for December 1-31, 2025"""
    db = SessionLocal()
    
    client_names = [
        "Grow 3",
        "Canadian Shade",
        "City Duct Cleaning",
        "MGA International",
        "PolyPak Packaging",
    ]
    
    # December 1-31, 2025 date range
    start_date = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    try:
        print("=" * 70)
        print("Checking December 1-31, 2025 Data")
        print("=" * 70)
        print(f"Date Range: {start_date} to {end_date}")
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
                if not client.scrunch_brand_id:
                    print(f"⚠️  {client.company_name}: No scrunch_brand_id")
                    print()
                    continue
                
                brand_id = client.scrunch_brand_id
                print(f"Client: {client.company_name}")
                print(f"  Brand ID: {brand_id}")
                print()
                
                # Check prompts created in Dec 2025
                prompts_in_range = db.query(Prompt).filter(
                    and_(
                        Prompt.brand_id == brand_id,
                        Prompt.created_at >= start_date,
                        Prompt.created_at <= end_date
                    )
                ).all()
                
                print(f"  Prompts created in Dec 2025: {len(prompts_in_range)}")
                if prompts_in_range:
                    for prompt in prompts_in_range[:3]:  # Show first 3
                        print(f"    - ID {prompt.id}: {prompt.created_at} - {prompt.text[:60]}...")
                print()
                
                # Check responses created in Dec 2025
                responses_in_range = db.query(Response).filter(
                    and_(
                        Response.brand_id == brand_id,
                        Response.created_at >= start_date,
                        Response.created_at <= end_date
                    )
                ).all()
                
                print(f"  Responses created in Dec 2025: {len(responses_in_range)}")
                if responses_in_range:
                    print(f"    First response: {responses_in_range[0].created_at}")
                    print(f"    Last response: {responses_in_range[-1].created_at}")
                print()
                
                # Check ALL prompts for this brand (regardless of date)
                all_prompts = db.query(Prompt).filter(
                    Prompt.brand_id == brand_id
                ).order_by(Prompt.created_at.desc()).all()
                
                print(f"  Total prompts for brand: {len(all_prompts)}")
                if all_prompts:
                    print(f"    Earliest prompt: {all_prompts[-1].created_at}")
                    print(f"    Latest prompt: {all_prompts[0].created_at}")
                print()
                
                # Check ALL responses for this brand
                all_responses = db.query(Response).filter(
                    Response.brand_id == brand_id
                ).order_by(Response.created_at.desc()).all()
                
                print(f"  Total responses for brand: {len(all_responses)}")
                if all_responses:
                    print(f"    Earliest response: {all_responses[-1].created_at}")
                    print(f"    Latest response: {all_responses[0].created_at}")
                print()
                
                print("-" * 70)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("If prompts created in Dec 2025 = 0:")
        print("  → Dashboard will show 'No data available'")
        print("  → This is expected behavior (filtering by Prompt.created_at)")
        print()
        print("If responses exist but prompts don't:")
        print("  → Prompts were created before/after Dec 2025")
        print("  → But responses were generated in Dec 2025")
        print("  → Current filter shows prompts by creation date only")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_dec_2025_data()
