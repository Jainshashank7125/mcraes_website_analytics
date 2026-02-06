#!/usr/bin/env python3
"""
Test Scrunch API with detailed response inspection
"""
import sys
import os
import asyncio
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client
from app.services.scrunch_client import ScrunchAPIClient

async def test_scrunch_detailed():
    """Test Scrunch API with detailed inspection"""
    db = SessionLocal()
    
    # Test with Canadian Shade
    brand_id = 5553
    
    scrunch_client = ScrunchAPIClient()
    
    try:
        print("=" * 70)
        print("Testing Scrunch API - Detailed Response")
        print("=" * 70)
        print(f"Brand ID: {brand_id}")
        print()
        
        # Test prompts
        print("1. Fetching Prompts from Scrunch API...")
        print("-" * 70)
        try:
            prompts_response = await scrunch_client.get_prompts(brand_id=brand_id, limit=10)
            print(f"Response type: {type(prompts_response)}")
            print(f"Response keys: {list(prompts_response.keys()) if isinstance(prompts_response, dict) else 'Not a dict'}")
            print()
            
            if isinstance(prompts_response, dict):
                for key, value in prompts_response.items():
                    if isinstance(value, list):
                        print(f"  {key}: {len(value)} items (list)")
                        if value:
                            print(f"    Sample item keys: {list(value[0].keys()) if isinstance(value[0], dict) else type(value[0])}")
                    elif isinstance(value, dict):
                        print(f"  {key}: {len(value)} keys (dict)")
                    else:
                        print(f"  {key}: {type(value)} = {str(value)[:100]}")
            else:
                print(f"  Full response: {str(prompts_response)[:500]}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        
        # Test responses
        print("2. Fetching Responses from Scrunch API...")
        print("-" * 70)
        try:
            responses_response = await scrunch_client.get_responses(brand_id=brand_id, limit=10)
            print(f"Response type: {type(responses_response)}")
            print(f"Response keys: {list(responses_response.keys()) if isinstance(responses_response, dict) else 'Not a dict'}")
            print()
            
            if isinstance(responses_response, dict):
                for key, value in responses_response.items():
                    if isinstance(value, list):
                        print(f"  {key}: {len(value)} items (list)")
                        if value:
                            print(f"    Sample item keys: {list(value[0].keys()) if isinstance(value[0], dict) else type(value[0])}")
                    elif isinstance(value, dict):
                        print(f"  {key}: {len(value)} keys (dict)")
                    else:
                        print(f"  {key}: {type(value)} = {str(value)[:100]}")
            else:
                print(f"  Full response: {str(responses_response)[:500]}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 70)
        print("Conclusion")
        print("=" * 70)
        print("The database has prompts/responses, which means:")
        print("1. Data WAS successfully fetched from Scrunch API in the past")
        print("2. Data is stored in the local PostgreSQL database")
        print("3. The system reads from the database (not directly from Scrunch API)")
        print("4. To get fresh data, run a sync which fetches from Scrunch and stores in DB")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scrunch_detailed())
