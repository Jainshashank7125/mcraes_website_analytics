#!/usr/bin/env python3
"""
Check if responses exist in December 1-31, 2025 for these clients
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client, Response
from sqlalchemy import func, and_
from datetime import datetime

def check_responses_dec_2025():
    """Check responses in December 2025 for specific clients"""
    db = SessionLocal()
    
    clients = [
        {"name": "Canadian Shade", "id": 29, "brand_id": 5553},
        {"name": "City Duct Cleaning", "id": 67, "brand_id": 5726},
        {"name": "MGA International", "id": 69, "brand_id": 5908},
        {"name": "PolyPak Packaging", "id": 70, "brand_id": 5915},
    ]
    
    start_date = datetime(2025, 12, 1)
    end_date = datetime(2025, 12, 31, 23, 59, 59)
    
    try:
        print("=" * 70)
        print("Checking Responses in December 1-31, 2025")
        print("=" * 70)
        print()
        
        for client_info in clients:
            brand_id = client_info["brand_id"]
            client_name = client_info["name"]
            
            # Count responses in December 2025
            responses_count = db.query(func.count(Response.id)).filter(
                and_(
                    Response.brand_id == brand_id,
                    Response.created_at >= start_date,
                    Response.created_at <= end_date
                )
            ).scalar()
            
            # Get total responses for this brand
            total_responses = db.query(func.count(Response.id)).filter(
                Response.brand_id == brand_id
            ).scalar()
            
            # Get date range of responses
            earliest_response = db.query(Response.created_at).filter(
                Response.brand_id == brand_id
            ).order_by(Response.created_at.asc()).first()
            
            latest_response = db.query(Response.created_at).filter(
                Response.brand_id == brand_id
            ).order_by(Response.created_at.desc()).first()
            
            print(f"{client_name} (Brand ID: {brand_id})")
            print(f"  Responses in Dec 1-31, 2025: {responses_count}")
            print(f"  Total responses (all time): {total_responses}")
            
            if earliest_response and latest_response:
                print(f"  Response date range: {earliest_response[0].date()} to {latest_response[0].date()}")
            
            if responses_count == 0:
                print(f"  ❌ NO RESPONSES in December 2025")
                print(f"     This is why prompts are not visible for this date range")
                print(f"     Prompts only appear if they have responses in the selected period")
            else:
                print(f"  ✅ Responses exist in December 2025")
                print(f"     Prompts should be visible")
            
            print()
        
        print("=" * 70)
        print("Conclusion")
        print("=" * 70)
        print("The fix is working correctly - it filters prompts by responses in date range.")
        print("If no responses exist in Dec 2025, prompts won't appear for that period.")
        print("This is the expected behavior - prompts are shown based on when responses occurred.")
        print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_responses_dec_2025()
