#!/usr/bin/env python3
"""
Check if prompts exist for responses in December 2025
"""
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from sqlalchemy import func, and_, or_, distinct

def check_prompts_for_responses():
    """Check if prompts exist for responses in Dec 2025"""
    db = SessionLocal()
    
    client_names = [
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
        print("Checking Prompts for Responses in December 2025")
        print("=" * 70)
        print(f"Date Range: {start_date} to {end_date}")
        print()
        
        for client_name in client_names:
            # Search for client
            clients = db.query(Client).filter(
                Client.company_name.ilike(f'%{client_name}%')
            ).all()
            
            if not clients:
                continue
            
            for client in clients:
                if not client.scrunch_brand_id:
                    continue
                
                brand_id = client.scrunch_brand_id
                print(f"Client: {client.company_name}")
                print(f"  Brand ID: {brand_id}")
                print()
                
                # Get responses in Dec 2025
                responses_in_range = db.query(Response).filter(
                    and_(
                        Response.brand_id == brand_id,
                        Response.created_at >= start_date,
                        Response.created_at <= end_date
                    )
                ).all()
                
                print(f"  Responses created in Dec 2025: {len(responses_in_range)}")
                
                if responses_in_range:
                    # Get unique prompt_ids from these responses
                    prompt_ids_from_responses = set()
                    for response in responses_in_range:
                        if response.prompt_id:
                            prompt_ids_from_responses.add(response.prompt_id)
                    
                    print(f"  Unique prompt_ids from responses: {len(prompt_ids_from_responses)}")
                    print(f"    Prompt IDs: {sorted(list(prompt_ids_from_responses))[:10]}...")
                    print()
                    
                    # Check if these prompts exist in database
                    if prompt_ids_from_responses:
                        prompts_for_responses = db.query(Prompt).filter(
                            Prompt.id.in_(prompt_ids_from_responses)
                        ).all()
                        
                        print(f"  Prompts found in database: {len(prompts_for_responses)}")
                        
                        # Check when these prompts were created
                        prompts_created_in_range = [p for p in prompts_for_responses 
                                                   if start_date <= p.created_at <= end_date]
                        prompts_created_before = [p for p in prompts_for_responses 
                                                  if p.created_at < start_date]
                        prompts_created_after = [p for p in prompts_for_responses 
                                                 if p.created_at > end_date]
                        
                        print(f"    Created in Dec 2025: {len(prompts_created_in_range)}")
                        print(f"    Created before Dec 2025: {len(prompts_created_before)}")
                        if prompts_created_before:
                            print(f"      Earliest: {min(p.created_at for p in prompts_created_before)}")
                            print(f"      Latest: {max(p.created_at for p in prompts_created_before)}")
                        print(f"    Created after Dec 2025: {len(prompts_created_after)}")
                        print()
                        
                        # Show sample prompts
                        if prompts_created_before:
                            print(f"  Sample prompts (created before Dec 2025):")
                            for prompt in prompts_created_before[:3]:
                                print(f"    - ID {prompt.id}: Created {prompt.created_at}")
                                print(f"      Text: {prompt.text[:80]}...")
                                print()
                
                print("-" * 70)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("If prompts exist for responses but were created outside date range:")
        print("  → Current filter (by Prompt.created_at) won't show them")
        print("  → But responses exist, so we should show these prompts")
        print("  → Solution: Include prompts that have responses in the date range")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_prompts_for_responses()
