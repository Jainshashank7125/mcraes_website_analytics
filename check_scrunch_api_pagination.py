#!/usr/bin/env python3
"""
Check if Scrunch API pagination is working correctly
"""
import sys
import os
import asyncio

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scrunch_client import ScrunchAPIClient

async def check_pagination():
    """Check API pagination"""
    scrunch_client = ScrunchAPIClient()
    
    brand_id = 5553  # Canadian Shade
    
    print("=" * 70)
    print("Checking Scrunch API Pagination")
    print("=" * 70)
    print(f"Brand ID: {brand_id}")
    print()
    
    # Test prompts
    print("📝 PROMPTS:")
    print("-" * 70)
    try:
        # Get all prompts
        all_prompts = await scrunch_client.get_all_prompts_paginated(brand_id=brand_id)
        print(f"Total prompts fetched: {len(all_prompts)}")
        
        # Check API response structure
        single_page = await scrunch_client.get_prompts(brand_id=brand_id, limit=10, offset=0)
        print(f"Single page response type: {type(single_page)}")
        if isinstance(single_page, dict):
            print(f"Single page keys: {list(single_page.keys())}")
            print(f"Total in API: {single_page.get('total', 'N/A')}")
            print(f"Items in first page: {len(single_page.get('items', []))}")
            print(f"Limit: {single_page.get('limit', 'N/A')}")
            print(f"Offset: {single_page.get('offset', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test responses
    print("💬 RESPONSES (Dec 2025):")
    print("-" * 70)
    try:
        # Get responses for Dec 2025
        all_responses = await scrunch_client.get_all_responses_paginated(
            brand_id=brand_id,
            start_date="2025-12-01",
            end_date="2025-12-31"
        )
        print(f"Total responses fetched: {len(all_responses)}")
        
        # Check API response structure
        single_page = await scrunch_client.get_responses(
            brand_id=brand_id,
            start_date="2025-12-01",
            end_date="2025-12-31",
            limit=10,
            offset=0
        )
        print(f"Single page response type: {type(single_page)}")
        if isinstance(single_page, dict):
            print(f"Single page keys: {list(single_page.keys())}")
            print(f"Total in API: {single_page.get('total', 'N/A')}")
            print(f"Items in first page: {len(single_page.get('items', []))}")
            print(f"Limit: {single_page.get('limit', 'N/A')}")
            print(f"Offset: {single_page.get('offset', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("Analysis")
    print("=" * 70)
    print("If API total < database count:")
    print("  → API may have deleted/archived old data")
    print("  → Database has historical data not in API")
    print("  → This is expected if data was synced earlier")
    print()

if __name__ == "__main__":
    asyncio.run(check_pagination())
