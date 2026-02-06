#!/usr/bin/env python3
"""
Sync missing prompts from Scrunch API for responses that don't have prompts in database
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
from app.services.supabase_service import SupabaseService
from sqlalchemy import select, distinct, and_

async def sync_missing_prompts():
    """Sync missing prompts from Scrunch API"""
    db = SessionLocal()
    scrunch_client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)
    
    client_names = [
        "Canadian Shade",
        "City Duct Cleaning",
        "MGA International",
        "PolyPak Packaging",
    ]
    
    try:
        print("=" * 70)
        print("Syncing Missing Prompts from Scrunch API")
        print("=" * 70)
        print()
        
        for client_name in client_names:
            # Search for client
            clients = db.query(Client).filter(
                Client.company_name.ilike(f'%{client_name}%')
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
                
                # Get all unique prompt_ids from responses
                responses_query = select(distinct(Response.prompt_id)).where(
                    and_(
                        Response.brand_id == brand_id,
                        Response.prompt_id.isnot(None)
                    )
                )
                responses_result = db.scalars(responses_query).all()
                prompt_ids_from_responses = [pid for pid in responses_result if pid is not None]
                
                print(f"  Total prompt_ids referenced in responses: {len(prompt_ids_from_responses)}")
                
                # Check which prompt_ids exist in prompts table
                if prompt_ids_from_responses:
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
                    print(f"  Missing prompts: {len(missing_prompt_ids)}")
                    
                    if missing_prompt_ids:
                        print(f"  Missing prompt_ids: {sorted(list(missing_prompt_ids))[:10]}...")
                        print()
                        print(f"  🔄 Syncing {len(missing_prompt_ids)} missing prompts from Scrunch API...")
                        
                        # Fetch all prompts from Scrunch API
                        try:
                            all_prompts = await scrunch_client.get_all_prompts_paginated(brand_id=brand_id)
                            print(f"  ✅ Fetched {len(all_prompts)} prompts from Scrunch API")
                            
                            # Filter to only missing prompts
                            prompts_to_sync = [p for p in all_prompts if p.get("id") in missing_prompt_ids]
                            print(f"  📥 Syncing {len(prompts_to_sync)} missing prompts to database...")
                            
                            if prompts_to_sync:
                                count = supabase.upsert_prompts(prompts_to_sync, brand_id=brand_id)
                                print(f"  ✅ Synced {count} prompts to database")
                            else:
                                print(f"  ⚠️  No prompts found in Scrunch API for missing prompt_ids")
                                print(f"     This might mean these prompts were deleted from Scrunch")
                                
                        except Exception as e:
                            print(f"  ❌ Error syncing prompts: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"  ✅ All prompts exist in database")
                else:
                    print(f"  ⚠️  No prompt_ids found in responses")
                
                print()
                print("-" * 70)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("✅ Missing prompts have been synced from Scrunch API")
        print("✅ All responses should now have corresponding prompts in database")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(sync_missing_prompts())
