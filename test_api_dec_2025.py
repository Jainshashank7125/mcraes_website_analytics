#!/usr/bin/env python3
"""
Test the API endpoint for December 2025 data
"""
import requests
import json
from datetime import datetime

def test_api():
    """Test the reporting dashboard API for Dec 2025"""
    
    # Test with Canadian Shade (brand_id = 5553)
    brand_id = 5553
    start_date = "2025-12-01"
    end_date = "2025-12-31"
    
    url = f"http://localhost:8000/api/v1/data/reporting-dashboard/{brand_id}/scrunch"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    print("=" * 70)
    print("Testing API Endpoint")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            print("Response Structure:")
            print(f"  Keys: {list(data.keys())}")
            print()
            
            # Check prompts
            prompts = data.get("prompts", [])
            print(f"Prompts returned: {len(prompts)}")
            if prompts:
                print(f"  Sample prompt: {prompts[0]}")
            print()
            
            # Check top_performing_prompts
            chart_data = data.get("chart_data", {})
            top_prompts = chart_data.get("top_performing_prompts", [])
            print(f"Top performing prompts: {len(top_prompts)}")
            if top_prompts:
                print(f"  Sample: {top_prompts[0]}")
            print()
            
            # Check scrunch_ai_insights
            insights = chart_data.get("scrunch_ai_insights", [])
            print(f"Scrunch AI insights: {len(insights)}")
            if insights:
                print(f"  Sample: {insights[0]}")
            print()
            
            # Check no_data flag
            no_data = data.get("no_data", False)
            print(f"no_data flag: {no_data}")
            print()
            
            # Check has_any_scrunch_data
            has_data = data.get("has_any_scrunch_data", False)
            print(f"has_any_scrunch_data: {has_data}")
            print()
            
            print("=" * 70)
            print("Summary")
            print("=" * 70)
            if len(prompts) == 0:
                print("❌ No prompts returned - this will show 'No data available'")
            else:
                print("✅ Prompts returned")
            
            if no_data:
                print("⚠️  API returned no_data=true")
            else:
                print("✅ API returned no_data=false")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
