#!/usr/bin/env python3
"""
Test if prompts are now shown for December 2025
"""
import requests
import json

def test_api():
    """Test the API endpoints"""
    
    # Test with Canadian Shade (brand_id = 5553)
    brand_id = 5553
    start_date = "2025-12-01"
    end_date = "2025-12-31"
    
    print("=" * 70)
    print("Testing Fixed Prompts Logic")
    print("=" * 70)
    print()
    
    # Test 1: Scrunch dashboard endpoint
    print("1. Testing /data/reporting-dashboard/{brand_id}/scrunch")
    print("-" * 70)
    url1 = f"http://localhost:8000/api/v1/data/reporting-dashboard/{brand_id}/scrunch"
    params1 = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response1 = requests.get(url1, params=params1)
        if response1.status_code == 200:
            data1 = response1.json()
            prompts1 = data1.get("prompts", [])
            print(f"  ✅ Prompts returned: {len(prompts1)}")
            if prompts1:
                print(f"  Sample prompt: {prompts1[0].get('text', 'N/A')[:60]}...")
        else:
            print(f"  ❌ Error: {response1.status_code} - {response1.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()
    
    # Test 2: Prompts analytics endpoint
    print("2. Testing /data/prompts-analytics (seed_prompts)")
    print("-" * 70)
    url2 = "http://localhost:8000/api/v1/data/prompts-analytics"
    params2 = {
        "group_by": "seed_prompts",
        "client_id": 29,  # Canadian Shade client_id
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response2 = requests.get(url2, params=params2)
        if response2.status_code == 200:
            data2 = response2.json()
            items2 = data2.get("items", [])
            print(f"  ✅ Items returned: {len(items2)}")
            if items2:
                print(f"  Sample item: {items2[0].get('display_name', 'N/A')[:60]}...")
                print(f"  Responses count: {items2[0].get('responses_count', 0)}")
        else:
            print(f"  ❌ Error: {response2.status_code} - {response2.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("If prompts are now returned:")
    print("  ✅ Fix is working - prompts with responses in date range are shown")
    print("  ✅ Even if prompts were created outside the date range")
    print()

if __name__ == "__main__":
    test_api()
