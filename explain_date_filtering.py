#!/usr/bin/env python3
"""
Explain how date filtering works - show the actual logic
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Response, Prompt
from sqlalchemy import select, and_
from datetime import datetime

def explain_date_filtering():
    """Show exactly how date filtering works"""
    db = SessionLocal()
    
    # Example: Canadian Shade, December 2025
    brand_id = 5553
    start_date = "2025-12-01"
    end_date = "2025-12-31"
    
    # Convert to datetime for filtering
    start_ts = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
    end_ts = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
    
    print("=" * 70)
    print("How Date Filtering Works - Step by Step")
    print("=" * 70)
    print()
    print(f"Date Range Selected: {start_date} to {end_date}")
    print()
    
    # Step 1: Get responses in the date range
    print("STEP 1: Find RESPONSES that occurred in the date range")
    print("-" * 70)
    responses_query = select(
        Response.id,
        Response.prompt_id,
        Response.created_at,
        Response.brand_id
    ).where(
        and_(
            Response.brand_id == brand_id,
            Response.created_at >= start_ts,  # ← Response occurred AFTER start date
            Response.created_at <= end_ts     # ← Response occurred BEFORE end date
        )
    )
    responses_result = db.execute(responses_query)
    responses = [dict(row._mapping) for row in responses_result]
    
    print(f"Found {len(responses)} responses in date range {start_date} to {end_date}")
    print()
    
    if responses:
        print("Sample responses:")
        for i, r in enumerate(responses[:5], 1):
            print(f"  {i}. Response ID: {r['id']}, Prompt ID: {r['prompt_id']}, Occurred: {r['created_at']}")
        print()
        
        # Step 2: Get unique prompt IDs from these responses
        print("STEP 2: Extract PROMPT IDs from these responses")
        print("-" * 70)
        prompt_ids_with_responses = set(r.get("prompt_id") for r in responses if r.get("prompt_id"))
        print(f"Found {len(prompt_ids_with_responses)} unique prompts that have responses in this date range")
        print(f"Prompt IDs: {sorted(list(prompt_ids_with_responses))[:10]}...")
        print()
        
        # Step 3: Get all prompts for the brand
        print("STEP 3: Get ALL prompts for this brand (no date filter)")
        print("-" * 70)
        prompts_query = select(
            Prompt.id,
            Prompt.text,
            Prompt.created_at,
            Prompt.brand_id
        ).where(
            Prompt.brand_id == brand_id
        )
        prompts_result = db.execute(prompts_query)
        all_prompts = [dict(row._mapping) for row in prompts_result]
        
        print(f"Found {len(all_prompts)} total prompts for this brand")
        print()
        
        # Step 4: Filter prompts to only those with responses in date range
        print("STEP 4: Filter prompts to only those with responses in date range")
        print("-" * 70)
        prompts = [p for p in all_prompts if p.get("id") in prompt_ids_with_responses]
        
        print(f"Result: {len(prompts)} prompts will be shown")
        print(f"(These are prompts that have responses occurring between {start_date} and {end_date})")
        print()
        
        if prompts:
            print("Sample prompts that will be shown:")
            for i, p in enumerate(prompts[:5], 1):
                prompt_text = p.get('text', 'N/A')[:60]
                print(f"  {i}. Prompt ID: {p['id']}, Created: {p['created_at']}, Text: {prompt_text}...")
                # Show that this prompt has responses in the date range
                responses_for_prompt = [r for r in responses if r.get('prompt_id') == p['id']]
                print(f"      → Has {len(responses_for_prompt)} responses in {start_date} to {end_date}")
        print()
        
        # Show comparison
        print("=" * 70)
        print("Key Point")
        print("=" * 70)
        print("The system checks Response.created_at (when response occurred)")
        print("NOT Prompt.created_at (when prompt was created)")
        print()
        print("Example:")
        if prompts:
            sample_prompt = prompts[0]
            sample_responses = [r for r in responses if r.get('prompt_id') == sample_prompt['id']]
            if sample_responses:
                print(f"  Prompt created: {sample_prompt['created_at']}")
                print(f"  But has responses in: {start_date} to {end_date}")
                print(f"  → Prompt WILL be shown (because responses occurred in date range)")
        print()
    
    db.close()

if __name__ == "__main__":
    explain_date_filtering()
