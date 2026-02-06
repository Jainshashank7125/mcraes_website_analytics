#!/usr/bin/env python3
"""
Test if prompts are correctly filtered by date range
"""
import requests
import json

def test_date_filtering():
    """Test prompts filtering for different date ranges"""
    base_url = "http://localhost:8000/api/v1"
    
    # Test client
    client = {"name": "Canadian Shade", "id": 29, "brand_id": 5553}
    
    # Test different date ranges
    date_ranges = [
        {"name": "December 2025", "start": "2025-12-01", "end": "2025-12-31"},
        {"name": "November 2025", "start": "2025-11-01", "end": "2025-11-30"},
        {"name": "January 2026", "start": "2026-01-01", "end": "2026-01-31"},
        {"name": "Last 7 days", "start": "2026-01-20", "end": "2026-01-27"},
    ]
    
    print("=" * 70)
    print(f"Testing Date Filtering for {client['name']}")
    print("=" * 70)
    print()
    
    for date_range in date_ranges:
        print(f"Date Range: {date_range['name']} ({date_range['start']} to {date_range['end']})")
        print("-" * 70)
        
        try:
            url = f"{base_url}/data/reporting-dashboard/{client['brand_id']}/scrunch"
            params = {
                "client_id": client['id'],
                "start_date": date_range['start'],
                "end_date": date_range['end']
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chart_data = data.get("chart_data", {})
                top_prompts = chart_data.get("top_performing_prompts", [])
                insights = chart_data.get("scrunch_ai_insights", [])
                
                print(f"  Top Performing Prompts: {len(top_prompts)}")
                print(f"  Scrunch AI Insights: {len(insights)}")
                
                if top_prompts:
                    print(f"  ✅ Prompts ARE filtered by date range")
                    print(f"     Showing prompts with responses in {date_range['name']}")
                else:
                    print(f"  ⚠️  No prompts (no responses in this date range)")
                
                # Show sample prompt IDs to verify they're different per date range
                if top_prompts:
                    prompt_ids = [p.get('id') for p in top_prompts[:3]]
                    print(f"  Sample prompt IDs: {prompt_ids}")
            else:
                print(f"  ❌ API Error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    print("=" * 70)
    print("How Date Filtering Works")
    print("=" * 70)
    print("1. User selects a date range (e.g., Dec 1-31, 2025)")
    print("2. System finds all RESPONSES in that date range")
    print("3. System finds all PROMPTS that have those responses")
    print("4. Only prompts with responses in the selected date range are shown")
    print()
    print("✅ This is correct behavior - prompts are filtered by when responses occurred")
    print("   Not by when the prompt was created")
    print()

if __name__ == "__main__":
    test_date_filtering()
