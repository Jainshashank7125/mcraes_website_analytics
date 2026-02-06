#!/usr/bin/env python3
"""
Directly check Scrunch API for prompts and responses
"""
import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client
from app.services.scrunch_client import ScrunchAPIClient

async def check_scrunch_api_direct():
    """Check Scrunch API directly"""
    db = SessionLocal()
    scrunch_client = ScrunchAPIClient()
    
    client_names = [
        "Canadian Shade",
        "City Duct Cleaning",
        "MGA International",
        "PolyPak Packaging",
    ]
    
    try:
        print("=" * 70)
        print("Direct Scrunch API Check")
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
                print(f"Client: {client.company_name}")
                print(f"  Brand ID: {brand_id}")
                print()
                
                # ========== PROMPTS ==========
                print("  📝 PROMPTS from Scrunch API:")
                print("  " + "-" * 66)
                try:
                    # Get all prompts
                    all_prompts = await scrunch_client.get_all_prompts_paginated(brand_id=brand_id)
                    print(f"    Total prompts in API: {len(all_prompts)}")
                    
                    if all_prompts:
                        # Show sample prompts with dates
                        print(f"    Sample prompts:")
                        for i, prompt in enumerate(all_prompts[:5], 1):
                            prompt_id = prompt.get("id")
                            text = prompt.get("text", "N/A")[:60]
                            created_at = prompt.get("created_at", "N/A")
                            print(f"      {i}. ID {prompt_id}: {text}...")
                            print(f"         Created: {created_at}")
                        
                        # Check prompts created in Dec 2025
                        dec_2025_prompts = []
                        for prompt in all_prompts:
                            created_at = prompt.get("created_at")
                            if created_at:
                                try:
                                    if isinstance(created_at, str):
                                        # Parse date string
                                        if "T" in created_at:
                                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                        else:
                                            dt = datetime.strptime(created_at, "%Y-%m-%d")
                                    else:
                                        dt = created_at
                                    
                                    if dt.year == 2025 and dt.month == 12:
                                        dec_2025_prompts.append(prompt)
                                except:
                                    pass
                        
                        print(f"    Prompts created in Dec 2025: {len(dec_2025_prompts)}")
                        if dec_2025_prompts:
                            print(f"    Dec 2025 prompt IDs: {[p.get('id') for p in dec_2025_prompts]}")
                    
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                print()
                
                # ========== RESPONSES ==========
                print("  💬 RESPONSES from Scrunch API (Dec 2025):")
                print("  " + "-" * 66)
                try:
                    # Get responses for Dec 2025
                    responses = await scrunch_client.get_all_responses_paginated(
                        brand_id=brand_id,
                        start_date="2025-12-01",
                        end_date="2025-12-31"
                    )
                    print(f"    Total responses in API (Dec 2025): {len(responses)}")
                    
                    if responses:
                        # Get unique prompt_ids from responses
                        prompt_ids_from_responses = set()
                        for response in responses:
                            prompt_id = response.get("prompt_id")
                            if prompt_id:
                                prompt_ids_from_responses.add(prompt_id)
                        
                        print(f"    Unique prompt_ids from responses: {len(prompt_ids_from_responses)}")
                        print(f"    Prompt IDs: {sorted(list(prompt_ids_from_responses))[:20]}")
                        
                        # Show sample responses
                        print(f"    Sample responses:")
                        for i, response in enumerate(responses[:3], 1):
                            response_id = response.get("id")
                            prompt_id = response.get("prompt_id", "N/A")
                            created_at = response.get("created_at", "N/A")
                            print(f"      {i}. Response ID {response_id}, Prompt ID {prompt_id}")
                            print(f"         Created: {created_at}")
                        
                        # Check if these prompt_ids exist in the prompts we fetched
                        if all_prompts:
                            api_prompt_ids = set([p.get("id") for p in all_prompts if p.get("id")])
                            missing_prompts = prompt_ids_from_responses - api_prompt_ids
                            if missing_prompts:
                                print(f"    ⚠️  {len(missing_prompts)} prompt_ids from responses NOT in prompts API!")
                                print(f"       Missing prompt_ids: {sorted(list(missing_prompts))[:10]}")
                            else:
                                print(f"    ✅ All prompt_ids from responses exist in prompts API")
                    else:
                        print(f"    No responses found in API for Dec 2025")
                        
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                print()
                print("  " + "=" * 66)
                print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print("This shows what's actually available in Scrunch API")
        print("Compare with database to identify sync issues")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_scrunch_api_direct())
