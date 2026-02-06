#!/usr/bin/env python3
"""
Test if we can fetch data directly from Scrunch API for these clients
"""
import sys
import os
import asyncio

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client
from app.services.scrunch_client import ScrunchAPIClient

async def test_scrunch_fetch():
    """Test fetching from Scrunch API"""
    db = SessionLocal()
    
    client_names = [
        "Canadian Shade",
        "City Duct Cleaning",
        "MGA International",
        "PolyPak Packaging",
    ]
    
    scrunch_client = ScrunchAPIClient()
    
    try:
        print("=" * 70)
        print("Testing Scrunch API Fetch")
        print("=" * 70)
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
                print(f"Testing: {client.company_name} (Brand ID: {brand_id})")
                print("-" * 70)
                
                # Test fetching prompts from Scrunch API
                try:
                    print("  Fetching prompts from Scrunch API...")
                    prompts_response = await scrunch_client.get_prompts(brand_id=brand_id, limit=10)
                    prompts = prompts_response.get("prompts", []) if isinstance(prompts_response, dict) else prompts_response
                    
                    if isinstance(prompts, list):
                        print(f"  ✅ Successfully fetched {len(prompts)} prompts from Scrunch API")
                        if prompts:
                            print(f"     Sample: {prompts[0].get('text', 'N/A')[:60]}...")
                    else:
                        print(f"  ⚠️  Unexpected response format: {type(prompts_response)}")
                        print(f"     Response keys: {list(prompts_response.keys()) if isinstance(prompts_response, dict) else 'N/A'}")
                except Exception as e:
                    print(f"  ❌ Error fetching prompts: {str(e)}")
                
                # Test fetching responses from Scrunch API
                try:
                    print("  Fetching responses from Scrunch API...")
                    responses_response = await scrunch_client.get_responses(brand_id=brand_id, limit=10)
                    responses = responses_response.get("responses", []) if isinstance(responses_response, dict) else responses_response
                    
                    if isinstance(responses, list):
                        print(f"  ✅ Successfully fetched {len(responses)} responses from Scrunch API")
                        if responses:
                            print(f"     Sample response ID: {responses[0].get('id', 'N/A')}")
                    else:
                        print(f"  ⚠️  Unexpected response format: {type(responses_response)}")
                        print(f"     Response keys: {list(responses_response.keys()) if isinstance(responses_response, dict) else 'N/A'}")
                except Exception as e:
                    print(f"  ❌ Error fetching responses: {str(e)}")
                
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("✅ If prompts/responses were fetched → Scrunch API is working")
        print("✅ Data can be synced from Scrunch to database")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scrunch_fetch())
