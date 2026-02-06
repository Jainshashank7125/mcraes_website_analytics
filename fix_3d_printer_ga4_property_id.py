#!/usr/bin/env python3
"""
Script to fix the GA4 Property ID for 3DPrinterOS client
Extracts the numeric property ID from the malformed value
"""
import sys
import os
import re

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import SessionLocal
from app.db.models import Client
from sqlalchemy import update

def fix_ga4_property_id():
    """Fix the GA4 Property ID for 3DPrinterOS client"""
    db = SessionLocal()
    
    try:
        # Find the client
        client = db.query(Client).filter(
            Client.id == 27
        ).first()
        
        if not client:
            print("❌ Client ID 27 not found")
            return
        
        print(f"Found client: {client.company_name}")
        print(f"Current GA4 Property ID: {client.ga4_property_id}")
        print()
        
        # Extract numeric property ID from the malformed value
        current_value = client.ga4_property_id or ""
        
        # Try to extract the numeric property ID (should be in parentheses)
        # Pattern: "scottsinfo - GA4 (321222128)8yh" -> "321222128"
        match = re.search(r'\((\d+)\)', current_value)
        if match:
            extracted_id = match.group(1)
            print(f"✅ Extracted Property ID: {extracted_id}")
            print()
            
            # Ask for confirmation (in automated mode, just proceed)
            print(f"Updating GA4 Property ID from '{current_value}' to '{extracted_id}'...")
            
            # Update the property ID
            client.ga4_property_id = extracted_id
            db.commit()
            
            print("✅ Successfully updated GA4 Property ID")
            print()
            print("Next steps:")
            print("1. Run a GA4 sync for this client:")
            print("   POST /sync/ga4?client_id=27&sync_mode=complete")
            print("2. Or use the sync interface in the frontend")
        else:
            print("❌ Could not extract numeric Property ID from current value")
            print("   Please manually update the Property ID to the correct numeric value")
            print("   Expected format: numeric string like '321222128'")
    
    except Exception as e:
        print(f"❌ Error fixing Property ID: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_ga4_property_id()
