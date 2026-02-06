#!/usr/bin/env python3
"""
Check when prompts were created in database vs when responses were created
"""
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Prompt, Response
from sqlalchemy import select, and_, distinct

def check_prompt_dates():
    """Check prompt creation dates"""
    db = SessionLocal()
    
    brand_id = 5553
    prompt_ids = [482623, 482624, 482625, 482626, 482627, 482628, 482629, 482630, 482631, 482632]
    
    # December 1-31, 2025 date range
    start_date = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    try:
        print("=" * 70)
        print("Checking Prompt Creation Dates")
        print("=" * 70)
        print(f"Brand ID: {brand_id}")
        print(f"Prompt IDs from Dec 2025 responses: {prompt_ids}")
        print()
        
        # Get prompts from database
        prompts_query = select(Prompt).where(
            and_(
                Prompt.brand_id == brand_id,
                Prompt.id.in_(prompt_ids)
            )
        )
        prompts_result = db.scalars(prompts_query).all()
        prompts = [{"id": p.id, "text": p.text[:60], "created_at": p.created_at} for p in prompts_result]
        
        print(f"Prompts found in database: {len(prompts)}")
        print()
        
        for prompt in prompts:
            created = prompt["created_at"]
            in_range = start_date <= created <= end_date
            status = "✅ IN Dec 2025" if in_range else "❌ OUTSIDE Dec 2025"
            print(f"  Prompt ID {prompt['id']}: Created {created}")
            print(f"    {status}")
            print(f"    Text: {prompt['text']}...")
            print()
        
        # Get responses for these prompts in Dec 2025
        responses_query = select(Response).where(
            and_(
                Response.brand_id == brand_id,
                Response.prompt_id.in_(prompt_ids),
                Response.created_at >= start_date,
                Response.created_at <= end_date
            )
        )
        responses_result = db.scalars(responses_query).all()
        responses = [{"id": r.id, "prompt_id": r.prompt_id, "created_at": r.created_at} for r in responses_result]
        
        print(f"Responses in Dec 2025 for these prompts: {len(responses)}")
        if responses:
            print(f"  First response: {responses[0]['created_at']}")
            print(f"  Last response: {responses[-1]['created_at']}")
        
        print()
        print("=" * 70)
        print("Conclusion")
        print("=" * 70)
        prompts_in_range = [p for p in prompts if start_date <= p["created_at"] <= end_date]
        print(f"Prompts created in Dec 2025: {len(prompts_in_range)}")
        print(f"Prompts with responses in Dec 2025: {len(prompts)}")
        print()
        if len(prompts_in_range) == 0 and len(prompts) > 0:
            print("ISSUE:")
            print("  - Prompts were created BEFORE Dec 2025")
            print("  - But responses were generated IN Dec 2025")
            print("  - Filtering by Prompt.created_at in Dec 2025 returns 0 prompts")
            print("  - But we need to show these prompts because they have responses")
            print()
            print("CORRECT FIX:")
            print("  - Show prompts that have responses in the date range")
            print("  - This is the correct behavior - show prompts with activity in the period")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_prompt_dates()
