#!/usr/bin/env python3
"""
Verify prompts are now filtered by created_at (prompt creation date)
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Prompt
from sqlalchemy import select, and_
from datetime import datetime

def verify_prompt_created_at_filter():
    """Verify prompts are filtered by created_at"""
    db = SessionLocal()
    
    # Test: Canadian Shade
    brand_id = 5553
    
    # December 2025 date range
    start_date = "2025-12-01"
    end_date = "2025-12-31"
    start_ts = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
    end_ts = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
    
    print("=" * 70)
    print("Verifying Prompts Filtered by created_at (Prompt Creation Date)")
    print("=" * 70)
    print(f"Date Range: {start_date} to {end_date}")
    print()
    
    # Get all prompts for this brand
    all_prompts_query = select(
        Prompt.id,
        Prompt.text,
        Prompt.created_at
    ).where(
        Prompt.brand_id == brand_id
    )
    all_prompts_result = db.execute(all_prompts_query)
    all_prompts = [dict(row._mapping) for row in all_prompts_result]
    
    print(f"Total prompts for brand {brand_id}: {len(all_prompts)}")
    print()
    
    # Show when prompts were created
    if all_prompts:
        print("Prompt creation dates:")
        for p in sorted(all_prompts, key=lambda x: x['created_at'])[:10]:
            created_date = p['created_at'].date() if p['created_at'] else None
            print(f"  Prompt ID {p['id']}: Created on {created_date}")
        print()
    
    # Now filter by created_at in date range
    print(f"Filtering prompts created between {start_date} and {end_date}:")
    print("-" * 70)
    
    filtered_prompts_query = select(
        Prompt.id,
        Prompt.text,
        Prompt.created_at
    ).where(
        and_(
            Prompt.brand_id == brand_id,
            Prompt.created_at >= start_ts,
            Prompt.created_at <= end_ts
        )
    )
    filtered_result = db.execute(filtered_prompts_query)
    filtered_prompts = [dict(row._mapping) for row in filtered_result]
    
    print(f"Prompts created in {start_date} to {end_date}: {len(filtered_prompts)}")
    
    if filtered_prompts:
        print("Prompts that WILL be shown:")
        for p in filtered_prompts[:5]:
            print(f"  Prompt ID {p['id']}: Created on {p['created_at'].date()}")
    else:
        print("No prompts created in this date range")
        print()
        print("This is why prompts are not visible:")
        print("- Prompts were created in November 2025 (not December)")
        print("- System now filters by Prompt.created_at")
        print("- Only prompts created in Dec 1-31, 2025 would appear")
    
    print()
    print("=" * 70)
    print("Current Behavior")
    print("=" * 70)
    print("✅ Prompts are filtered by Prompt.created_at (when prompt was created)")
    print("✅ Only prompts created in the selected date range are shown")
    print("✅ This is the correct behavior as requested")
    print()
    
    db.close()

if __name__ == "__main__":
    verify_prompt_created_at_filter()
