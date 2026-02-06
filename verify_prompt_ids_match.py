#!/usr/bin/env python3
"""
Verify if prompt_ids from responses actually exist in prompts from API
"""
import sys
import os
import asyncio

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client
from app.services.scrunch_client import ScrunchAPIClient

async def verify_prompt_ids():
    """Verify prompt_ids match"""
    db = SessionLocal()
    scrunch_client = ScrunchAPIClient()
    
    # Test with Canadian Shade
    brand_id = 5553
    
    try:
        print("=" * 70)
        print("Verifying Prompt IDs Match")
        print("=" * 70)
        print(f"Brand ID: {brand_id}")
        print()
        
        # Get all prompts from API
        print("1. Fetching ALL prompts from Scrunch API...")
        all_prompts = await scrunch_client.get_all_prompts_paginated(brand_id=brand_id)
        api_prompt_ids = set([p.get("id") for p in all_prompts if p.get("id")])
        print(f"   Total prompts: {len(all_prompts)}")
        print(f"   Prompt IDs: {sorted(list(api_prompt_ids))}")
        print()
        
        # Get responses for Dec 2025
        print("2. Fetching responses for Dec 2025 from Scrunch API...")
        responses = await scrunch_client.get_all_responses_paginated(
            brand_id=brand_id,
            start_date="2025-12-01",
            end_date="2025-12-31"
        )
        print(f"   Total responses: {len(responses)}")
        
        # Get unique prompt_ids from responses
        prompt_ids_from_responses = set()
        for response in responses:
            prompt_id = response.get("prompt_id")
            if prompt_id:
                prompt_ids_from_responses.add(prompt_id)
        
        print(f"   Unique prompt_ids from responses: {len(prompt_ids_from_responses)}")
        print(f"   Prompt IDs from responses: {sorted(list(prompt_ids_from_responses))}")
        print()
        
        # Check if they match
        print("3. Checking if prompt_ids from responses exist in prompts...")
        missing = prompt_ids_from_responses - api_prompt_ids
        if missing:
            print(f"   ❌ {len(missing)} prompt_ids from responses NOT in prompts API!")
            print(f"   Missing IDs: {sorted(list(missing))}")
            print()
            print("   This means:")
            print("   - Responses reference prompts that don't exist in current prompts")
            print("   - These prompts may have been deleted or are from a different time period")
            print("   - The database may have old prompts that are no longer in API")
        else:
            print(f"   ✅ All prompt_ids from responses exist in prompts API")
        
        print()
        print("=" * 70)
        print("Conclusion")
        print("=" * 70)
        if missing:
            print("ISSUE FOUND:")
            print("  - Responses reference prompt_ids that don't exist in current API prompts")
            print("  - These are likely old/deleted prompts")
            print("  - Database has these prompts (from previous syncs)")
            print("  - But API no longer returns them")
            print()
            print("SOLUTION:")
            print("  - Database prompts are correct (they exist from previous syncs)")
            print("  - The issue is that API doesn't return old prompts")
            print("  - We should use database prompts (which are correct)")
            print("  - Filter prompts by created_at date as originally designed")
        else:
            print("No issue - all prompt_ids match")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_prompt_ids())
