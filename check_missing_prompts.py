#!/usr/bin/env python3
"""
Check for responses that don't have corresponding prompts in the database
"""
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from sqlalchemy import func, and_, distinct

def check_missing_prompts():
    """Check for missing prompts"""
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
        print("Checking for Missing Prompts")
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
                
                # Get unique prompt_ids from responses in Dec 2025
                from sqlalchemy import select, distinct
                responses_query = select(distinct(Response.prompt_id)).where(
                    and_(
                        Response.brand_id == brand_id,
                        Response.created_at >= start_date,
                        Response.created_at <= end_date,
                        Response.prompt_id.isnot(None)
                    )
                )
                responses_result = db.scalars(responses_query).all()
                prompt_ids_from_responses = [pid for pid in responses_result if pid is not None]
                print(f"  Unique prompt_ids from responses: {len(prompt_ids_from_responses)}")
                
                # Check which prompt_ids exist in prompts table
                from sqlalchemy import select
                existing_prompts_query = select(Prompt.id).where(
                    and_(
                        Prompt.brand_id == brand_id,
                        Prompt.id.in_(prompt_ids_from_responses)
                    )
                )
                existing_prompts_result = db.scalars(existing_prompts_query).all()
                existing_prompt_ids = set([p for p in existing_prompts_result])
                missing_prompt_ids = set(prompt_ids_from_responses) - existing_prompt_ids
                
                print(f"  Prompts that exist in database: {len(existing_prompt_ids)}")
                print(f"  Missing prompts (referenced in responses but not in prompts table): {len(missing_prompt_ids)}")
                
                if missing_prompt_ids:
                    print(f"  Missing prompt_ids: {sorted(list(missing_prompt_ids))[:10]}...")
                    print()
                    print("  ⚠️  ISSUE: Responses reference prompts that don't exist in prompts table")
                    print("     These prompts need to be synced from Scrunch API")
                else:
                    print("  ✅ All prompts exist in database")
                
                print()
                print("-" * 70)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("If prompts are missing:")
        print("  → Need to sync prompts from Scrunch API")
        print("  → Prompts should exist for all responses")
        print("  → This is a data integrity issue")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_missing_prompts()
