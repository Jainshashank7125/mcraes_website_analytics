#!/usr/bin/env python3
"""
Check Scrunch API vs Database for prompts and responses
"""
import sys
import os
import asyncio
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Prompt, Response
from app.services.scrunch_client import ScrunchAPIClient
from sqlalchemy import select, distinct, and_, func

async def check_scrunch_api_vs_db():
    """Compare Scrunch API data with database"""
    db = SessionLocal()
    scrunch_client = ScrunchAPIClient()
    
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
        print("Checking Scrunch API vs Database")
        print("=" * 70)
        print(f"Date Range: {start_date.date()} to {end_date.date()}")
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
                
                # ========== PROMPTS ==========
                print("  📝 PROMPTS:")
                print("  " + "-" * 66)
                
                # Get prompts from Scrunch API
                try:
                    api_prompts = await scrunch_client.get_all_prompts_paginated(brand_id=brand_id)
                    api_prompt_ids = set([p.get("id") for p in api_prompts if p.get("id")])
                    print(f"    Scrunch API: {len(api_prompts)} prompts")
                    print(f"    API prompt_ids: {len(api_prompt_ids)} unique IDs")
                except Exception as e:
                    print(f"    ❌ Error fetching from API: {str(e)}")
                    api_prompts = []
                    api_prompt_ids = set()
                
                # Get prompts from database
                db_prompts_query = select(Prompt).where(Prompt.brand_id == brand_id)
                db_prompts_result = db.scalars(db_prompts_query).all()
                db_prompts = [{"id": p.id, "text": p.text, "created_at": p.created_at} for p in db_prompts_result]
                db_prompt_ids = set([p["id"] for p in db_prompts if p["id"]])
                print(f"    Database: {len(db_prompts)} prompts")
                print(f"    DB prompt_ids: {len(db_prompt_ids)} unique IDs")
                
                # Check for prompts in API but not in DB
                missing_in_db = api_prompt_ids - db_prompt_ids
                if missing_in_db:
                    print(f"    ⚠️  {len(missing_in_db)} prompts in API but NOT in database")
                    print(f"       Missing IDs: {sorted(list(missing_in_db))[:10]}...")
                else:
                    print(f"    ✅ All API prompts exist in database")
                
                # Check for prompts in DB but not in API
                missing_in_api = db_prompt_ids - api_prompt_ids
                if missing_in_api:
                    print(f"    ⚠️  {len(missing_in_api)} prompts in database but NOT in API")
                    print(f"       Orphaned IDs: {sorted(list(missing_in_api))[:10]}...")
                
                # Check prompts created in Dec 2025
                prompts_in_range = [p for p in db_prompts if start_date <= p["created_at"] <= end_date]
                print(f"    Prompts created in Dec 2025: {len(prompts_in_range)}")
                
                print()
                
                # ========== RESPONSES ==========
                print("  💬 RESPONSES:")
                print("  " + "-" * 66)
                
                # Get responses from Scrunch API for Dec 2025
                try:
                    api_responses = await scrunch_client.get_all_responses_paginated(
                        brand_id=brand_id,
                        start_date="2025-12-01",
                        end_date="2025-12-31"
                    )
                    api_response_ids = set([r.get("id") for r in api_responses if r.get("id")])
                    api_response_prompt_ids = set([r.get("prompt_id") for r in api_responses if r.get("prompt_id")])
                    print(f"    Scrunch API (Dec 2025): {len(api_responses)} responses")
                    print(f"    API response_ids: {len(api_response_ids)} unique IDs")
                    print(f"    API prompt_ids from responses: {len(api_response_prompt_ids)} unique")
                except Exception as e:
                    print(f"    ❌ Error fetching from API: {str(e)}")
                    api_responses = []
                    api_response_ids = set()
                    api_response_prompt_ids = set()
                
                # Get responses from database for Dec 2025
                db_responses_query = select(Response).where(
                    and_(
                        Response.brand_id == brand_id,
                        Response.created_at >= start_date,
                        Response.created_at <= end_date
                    )
                )
                db_responses_result = db.scalars(db_responses_query).all()
                db_responses = [{"id": r.id, "prompt_id": r.prompt_id, "created_at": r.created_at} for r in db_responses_result]
                db_response_ids = set([r["id"] for r in db_responses if r["id"]])
                db_response_prompt_ids = set([r["prompt_id"] for r in db_responses if r.get("prompt_id")])
                print(f"    Database (Dec 2025): {len(db_responses)} responses")
                print(f"    DB response_ids: {len(db_response_ids)} unique IDs")
                print(f"    DB prompt_ids from responses: {len(db_response_prompt_ids)} unique")
                
                # Check for responses in API but not in DB
                missing_responses_in_db = api_response_ids - db_response_ids
                if missing_responses_in_db:
                    print(f"    ⚠️  {len(missing_responses_in_db)} responses in API but NOT in database")
                else:
                    print(f"    ✅ All API responses exist in database")
                
                # Check for responses in DB but not in API
                missing_responses_in_api = db_response_ids - api_response_ids
                if missing_responses_in_api:
                    print(f"    ⚠️  {len(missing_responses_in_api)} responses in database but NOT in API")
                
                # Check if prompt_ids from responses exist in prompts table
                if db_response_prompt_ids:
                    missing_prompts_for_responses = db_response_prompt_ids - db_prompt_ids
                    if missing_prompts_for_responses:
                        print(f"    ❌ {len(missing_prompts_for_responses)} prompt_ids from responses don't exist in prompts table!")
                        print(f"       Missing prompt_ids: {sorted(list(missing_prompts_for_responses))[:10]}...")
                    else:
                        print(f"    ✅ All prompt_ids from responses exist in prompts table")
                
                print()
                print("  " + "=" * 66)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("Issues to fix:")
        print("1. If prompts missing in DB → Sync from Scrunch API")
        print("2. If responses missing in DB → Sync from Scrunch API")
        print("3. If prompt_ids from responses don't exist → Sync those prompts")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_scrunch_api_vs_db())
